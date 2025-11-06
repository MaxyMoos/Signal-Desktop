#!/usr/bin/env python3
"""
Signal Desktop Media Attachment Cleanup Script

This script deletes old media attachments from Signal Desktop's local storage
to free up disk space while preserving message text.

Usage:
    python cleanup_signal_attachments.py --user-data ~/.config/Signal --before "2024-01-01"
    python cleanup_signal_attachments.py --user-data ~/Library/Application\ Support/Signal --before "1 year ago" --dry-run

Requirements:
    pip install sqlcipher3 python-dateutil
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

try:
    from pysqlcipher3 import dbapi2 as sqlcipher
except ImportError:
    print("Error: pysqlcipher3 is not installed.")
    print("Install it with: pip install pysqlcipher3")
    sys.exit(1)

try:
    from dateutil.parser import parse as parse_date
    from dateutil.relativedelta import relativedelta
except ImportError:
    print("Error: python-dateutil is not installed.")
    print("Install it with: pip install python-dateutil")
    sys.exit(1)


class SignalAttachmentCleaner:
    def __init__(self, user_data_path: Path, dry_run: bool = False, verbose: bool = False):
        self.user_data_path = Path(user_data_path)
        self.dry_run = dry_run
        self.verbose = verbose

        # Key directories
        self.db_path = self.user_data_path / "sql" / "db.sqlite"
        self.config_path = self.user_data_path / "config.json"
        self.attachments_dir = self.user_data_path / "attachments.noindex"
        self.downloads_dir = self.user_data_path / "downloads.noindex"
        self.drafts_dir = self.user_data_path / "drafts.noindex"
        self.temp_dir = self.user_data_path / "temp"

        self.stats = {
            'messages_processed': 0,
            'files_deleted': 0,
            'bytes_freed': 0,
            'errors': 0
        }

    def log(self, message: str, level: str = "INFO"):
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = f"[{level}]"
            print(f"{prefix} {message}")

    def get_database_key(self) -> str:
        """Extract the database encryption key from config.json"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        if 'key' not in config:
            raise ValueError("Database key not found in config.json")

        return config['key']

    def parse_date_string(self, date_str: str) -> datetime:
        """Parse various date formats including relative dates"""
        date_str = date_str.lower().strip()

        # Relative dates
        if 'year' in date_str or 'month' in date_str or 'day' in date_str or 'week' in date_str:
            now = datetime.now()
            parts = date_str.split()

            if len(parts) >= 2:
                try:
                    amount = int(parts[0])
                    unit = parts[1]

                    if 'year' in unit:
                        return now - relativedelta(years=amount)
                    elif 'month' in unit:
                        return now - relativedelta(months=amount)
                    elif 'week' in unit:
                        return now - relativedelta(weeks=amount)
                    elif 'day' in unit:
                        return now - relativedelta(days=amount)
                except (ValueError, IndexError):
                    pass

        # Try parsing as absolute date
        try:
            return parse_date(date_str)
        except Exception as e:
            raise ValueError(f"Cannot parse date: {date_str}. Error: {e}")

    def connect_database(self) -> sqlcipher.Connection:
        """Open an encrypted connection to the Signal database"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        key = self.get_database_key()

        self.log(f"Opening database: {self.db_path}")
        conn = sqlcipher.connect(str(self.db_path))

        # Set encryption key
        conn.execute(f"PRAGMA key = \"x'{key}'\"")

        # Verify the database is accessible
        try:
            conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            self.log("Database opened successfully")
        except sqlcipher.DatabaseError as e:
            raise ValueError(f"Failed to decrypt database. Wrong key? Error: {e}")

        return conn

    def get_messages_with_attachments(self, conn: sqlcipher.Connection, before_timestamp: int) -> List[Dict]:
        """Query messages with attachments before the cutoff date"""
        self.log(f"Querying messages before timestamp: {before_timestamp}")

        # Query the messages table for messages with attachments
        query = """
            SELECT
                id,
                json,
                received_at,
                sent_at,
                hasAttachments,
                hasVisualMediaAttachments,
                hasFileAttachments
            FROM messages
            WHERE (received_at < ? OR sent_at < ?)
              AND (hasAttachments = 1 OR hasVisualMediaAttachments = 1 OR hasFileAttachments = 1)
            ORDER BY received_at ASC
        """

        cursor = conn.execute(query, (before_timestamp, before_timestamp))
        messages = []

        for row in cursor:
            message = {
                'id': row[0],
                'json': json.loads(row[1]) if row[1] else {},
                'received_at': row[2],
                'sent_at': row[3],
                'hasAttachments': row[4],
                'hasVisualMediaAttachments': row[5],
                'hasFileAttachments': row[6]
            }
            messages.append(message)

        self.log(f"Found {len(messages)} messages with attachments")
        return messages

    def extract_attachment_paths(self, message: Dict) -> List[str]:
        """Extract all attachment file paths from a message"""
        paths = []
        msg_json = message.get('json', {})

        # Main attachments
        attachments = msg_json.get('attachments', [])
        for att in attachments:
            if isinstance(att, dict) and 'path' in att:
                paths.append(att['path'])

            # Thumbnail
            if isinstance(att, dict) and 'thumbnail' in att:
                thumb = att['thumbnail']
                if isinstance(thumb, dict) and 'path' in thumb:
                    paths.append(thumb['path'])

            # Screenshot
            if isinstance(att, dict) and 'screenshot' in att:
                screenshot = att['screenshot']
                if isinstance(screenshot, dict) and 'path' in screenshot:
                    paths.append(screenshot['path'])

        # Quote attachments
        quote = msg_json.get('quote', {})
        if isinstance(quote, dict):
            quote_attachments = quote.get('attachments', [])
            for att in quote_attachments:
                if isinstance(att, dict) and 'thumbnail' in att:
                    thumb = att['thumbnail']
                    if isinstance(thumb, dict) and 'path' in thumb:
                        paths.append(thumb['path'])

        # Preview attachments
        previews = msg_json.get('preview', [])
        for preview in previews:
            if isinstance(preview, dict) and 'image' in preview:
                img = preview['image']
                if isinstance(img, dict) and 'path' in img:
                    paths.append(img['path'])

        # Contact avatars
        contacts = msg_json.get('contact', [])
        for contact in contacts:
            if isinstance(contact, dict) and 'avatar' in contact:
                avatar = contact['avatar']
                if isinstance(avatar, dict) and 'path' in avatar:
                    paths.append(avatar['path'])

        # Sticker
        sticker = msg_json.get('sticker', {})
        if isinstance(sticker, dict) and 'path' in sticker:
            paths.append(sticker['path'])

        # Download path (in downloads directory)
        for att in attachments:
            if isinstance(att, dict) and 'downloadPath' in att:
                paths.append(att['downloadPath'])

        return paths

    def delete_attachment_file(self, relative_path: str) -> Tuple[bool, int]:
        """Delete an attachment file and return (success, bytes_freed)"""
        # Determine which base directory this file is in
        if relative_path.startswith('downloads'):
            base_dir = self.user_data_path
        else:
            base_dir = self.attachments_dir

        file_path = base_dir / relative_path

        if not file_path.exists():
            self.log(f"File not found (already deleted?): {relative_path}", "WARNING")
            return False, 0

        try:
            # Get file size before deletion
            file_size = file_path.stat().st_size

            if self.dry_run:
                self.log(f"[DRY RUN] Would delete: {relative_path} ({self._format_bytes(file_size)})")
                return True, file_size
            else:
                file_path.unlink()
                self.log(f"Deleted: {relative_path} ({self._format_bytes(file_size)})", "DEBUG")
                return True, file_size

        except Exception as e:
            self.log(f"Error deleting {relative_path}: {e}", "ERROR")
            self.stats['errors'] += 1
            return False, 0

    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes as human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    def cleanup_attachments(self, before_date: str):
        """Main cleanup function"""
        # Parse date
        cutoff_date = self.parse_date_string(before_date)
        cutoff_timestamp = int(cutoff_date.timestamp() * 1000)  # Convert to milliseconds

        print(f"\n{'='*70}")
        print(f"Signal Desktop Attachment Cleanup")
        print(f"{'='*70}")
        print(f"User data path: {self.user_data_path}")
        print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Cutoff timestamp: {cutoff_timestamp}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE DELETION'}")
        print(f"{'='*70}\n")

        if self.dry_run:
            print("⚠️  DRY RUN MODE: No files will actually be deleted\n")
        else:
            response = input("⚠️  WARNING: This will permanently delete attachment files. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return
            print()

        # Connect to database
        try:
            conn = self.connect_database()
        except Exception as e:
            print(f"Error: {e}")
            return

        try:
            # Get messages with attachments
            messages = self.get_messages_with_attachments(conn, cutoff_timestamp)

            if not messages:
                print("No messages with attachments found before the cutoff date.")
                return

            print(f"Processing {len(messages)} messages...\n")

            # Process each message
            for i, message in enumerate(messages, 1):
                self.stats['messages_processed'] += 1

                # Extract attachment paths
                paths = self.extract_attachment_paths(message)

                if paths:
                    self.log(f"Message {i}/{len(messages)}: {len(paths)} attachment(s)", "DEBUG")

                    # Delete each attachment file
                    for path in paths:
                        success, bytes_freed = self.delete_attachment_file(path)
                        if success:
                            self.stats['files_deleted'] += 1
                            self.stats['bytes_freed'] += bytes_freed

                # Progress indicator
                if i % 100 == 0:
                    print(f"Progress: {i}/{len(messages)} messages processed, "
                          f"{self.stats['files_deleted']} files deleted, "
                          f"{self._format_bytes(self.stats['bytes_freed'])} freed")

        finally:
            conn.close()

        # Print summary
        print(f"\n{'='*70}")
        print("Cleanup Summary")
        print(f"{'='*70}")
        print(f"Messages processed: {self.stats['messages_processed']}")
        print(f"Files deleted: {self.stats['files_deleted']}")
        print(f"Space freed: {self._format_bytes(self.stats['bytes_freed'])}")
        print(f"Errors: {self.stats['errors']}")
        print(f"{'='*70}\n")

        if self.dry_run:
            print("This was a DRY RUN. No files were actually deleted.")
            print("Run without --dry-run to perform the actual deletion.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old media attachments from Signal Desktop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - see what would be deleted
  %(prog)s --user-data ~/.config/Signal --before "2024-01-01" --dry-run

  # Delete attachments older than 1 year
  %(prog)s --user-data ~/.config/Signal --before "1 year ago"

  # Delete attachments older than 6 months with verbose output
  %(prog)s --user-data ~/Library/Application\ Support/Signal --before "6 months ago" -v

  # Delete attachments before a specific date
  %(prog)s --user-data ~/.config/Signal --before "2023-06-15"

Date formats supported:
  - Absolute: "2024-01-01", "2024-01-01 12:00:00"
  - Relative: "1 year ago", "6 months ago", "30 days ago", "2 weeks ago"
        """
    )

    parser.add_argument(
        '--user-data',
        required=True,
        help='Path to Signal Desktop user data directory (e.g., ~/.config/Signal)'
    )

    parser.add_argument(
        '--before',
        required=True,
        help='Delete attachments before this date (e.g., "2024-01-01" or "1 year ago")'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate user data path
    user_data_path = Path(args.user_data).expanduser()
    if not user_data_path.exists():
        print(f"Error: User data directory does not exist: {user_data_path}")
        sys.exit(1)

    # Run cleanup
    cleaner = SignalAttachmentCleaner(user_data_path, dry_run=args.dry_run, verbose=args.verbose)

    try:
        cleaner.cleanup_attachments(args.before)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
