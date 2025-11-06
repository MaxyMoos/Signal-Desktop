// Copyright 2025 Signal Messenger, LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState } from 'react';
import type { LocalizerType, ThemeType } from '../types/Util.std.js';
import { ConfirmationDialog } from './ConfirmationDialog.dom.js';
import { AxoButton } from '../axo/AxoButton.dom.js';

const CSS_MODULE = 'CleanupOldDataDialog';

export type PropsType = Readonly<{
  i18n: LocalizerType;
  theme?: ThemeType;
  onClose: () => void;
  onConfirm: (beforeDate: Date) => Promise<void>;
}>;

export function CleanupOldDataDialog(props: PropsType): JSX.Element {
  const { i18n, theme, onClose, onConfirm } = props;

  // State for the date input
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    // Default to 1 year ago
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    return oneYearAgo.toISOString().split('T')[0];
  });

  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      const date = new Date(selectedDate);
      // Set to end of day to include all messages from that day
      date.setHours(23, 59, 59, 999);
      await onConfirm(date);
      onClose();
    } catch (error) {
      // Error handling is done in the parent component
      setIsDeleting(false);
    }
  };

  // Get max date (today)
  const maxDate = new Date().toISOString().split('T')[0];

  return (
    <ConfirmationDialog
      dialogName="Preference.cleanupOldData"
      moduleClassName={CSS_MODULE}
      i18n={i18n}
      theme={theme}
      onClose={onClose}
      title={i18n('icu:Preferences__cleanup-old-data__modal--title')}
      hasXButton
      isSpinning={isDeleting}
      actions={[
        {
          text: i18n('icu:Preferences__cleanup-old-data__modal--delete'),
          style: 'negative',
          disabled: isDeleting,
          action: handleConfirm,
        },
      ]}
      cancelButtonVariant="secondary"
      cancelText={i18n('icu:cancel')}
    >
      <div className={`${CSS_MODULE}__content`}>
        <p>{i18n('icu:Preferences__cleanup-old-data__modal--body')}</p>

        <div className={`${CSS_MODULE}__date-input-container`}>
          <label htmlFor="cleanup-date-input" className={`${CSS_MODULE}__label`}>
            {i18n('icu:Preferences__cleanup-old-data__modal--date-label')}
          </label>
          <input
            id="cleanup-date-input"
            type="date"
            className={`${CSS_MODULE}__date-input`}
            value={selectedDate}
            max={maxDate}
            onChange={e => setSelectedDate(e.target.value)}
            disabled={isDeleting}
          />
        </div>

        <div className={`${CSS_MODULE}__warning`}>
          {i18n('icu:Preferences__cleanup-old-data__modal--warning')}
        </div>
      </div>
    </ConfirmationDialog>
  );
}
