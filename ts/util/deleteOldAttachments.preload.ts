// Copyright 2025 Signal Messenger, LLC
// SPDX-License-Identifier: AGPL-3.0-only

import PQueue from 'p-queue';
import { DataReader } from '../sql/Client.preload.js';
import { deleteMessageData } from './cleanup.preload.js';
import { createLogger } from '../logging/log.std.js';
import type { MessageAttributesType } from '../model-types.d.ts';
import * as Errors from '../types/errors.std.js';
import { MINUTE } from './durations/index.std.js';
import { drop } from './drop.std.js';

const log = createLogger('deleteOldAttachments');

export type DeleteOldAttachmentsOptions = {
  beforeTimestamp: number; // Unix timestamp in milliseconds
  onProgress?: (progress: {
    totalMessages: number;
    processedMessages: number;
    deletedAttachmentFiles: number;
  }) => void;
};

export type DeleteOldAttachmentsResult = {
  totalMessages: number;
  deletedAttachmentFiles: number;
};

/**
 * Deletes all media attachments from messages received/sent before a specified date.
 * This helps users free up disk space while keeping message text intact.
 *
 * @param options Configuration including the cutoff timestamp
 * @returns Statistics about the deletion operation
 */
export async function deleteOldAttachments(
  options: DeleteOldAttachmentsOptions
): Promise<DeleteOldAttachmentsResult> {
  const { beforeTimestamp, onProgress } = options;

  log.info(
    `deleteOldAttachments: Starting deletion of attachments before ${new Date(
      beforeTimestamp
    ).toISOString()}`
  );

  // Get all messages with attachments before the specified date
  // We use received_at as the primary timestamp field
  const allMessages = await DataReader._getAllMessages();
  log.info(`All messages = ${allMessages.length} messages`);
  const messagesWithAttachments = allMessages.filter(message => {
    const messageTimestamp = message.received_at || message.sent_at || 0;
    const hasAttachments = message.attachments;

    return messageTimestamp < beforeTimestamp && hasAttachments;
  });

  log.info(
    `deleteOldAttachments: Found ${messagesWithAttachments.length} messages with attachments to process`
  );

  let processedMessages = 0;
  let deletedAttachmentFiles = 0;

  // Process messages in batches to avoid overwhelming the system
  const queue = new PQueue({ concurrency: 3, timeout: MINUTE * 30 });

  drop(
    queue.addAll(
      messagesWithAttachments.map(
        (message: MessageAttributesType) => async () => {
          try {
            // Count attachments before deletion
            const attachmentCount =
              (message.attachments?.length || 0) +
              (message.preview?.length || 0) +
              (message.contact?.length || 0) +
              (message.quote?.attachments?.length || 0);

            // Delete attachment files from disk
            // This preserves the message but removes media files
            await deleteMessageData(message);

            if (attachmentCount > 0) {
              deletedAttachmentFiles += attachmentCount;
            }

            processedMessages++;

            // Report progress
            if (onProgress) {
              onProgress({
                totalMessages: messagesWithAttachments.length,
                processedMessages,
                deletedAttachmentFiles,
              });
            }

            // Log progress periodically
            if (processedMessages % 100 === 0) {
              log.info(
                `deleteOldAttachments: Processed ${processedMessages}/${messagesWithAttachments.length} messages`
              );
            }
          } catch (error) {
            log.error(
              `deleteOldAttachments: Error processing message ${message.id}:`,
              Errors.toLogFormat(error)
            );
          }
        }
      )
    )
  );

  await queue.onIdle();

  const result = {
    totalMessages: messagesWithAttachments.length,
    deletedAttachmentFiles,
  };

  log.info(
    `deleteOldAttachments: Completed. Processed ${result.totalMessages} messages, ` +
      `deleted ${result.deletedAttachmentFiles} attachment files`
  );

  return result;
}
