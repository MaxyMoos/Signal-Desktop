# Signal Desktop Attachment Cleanup Script

A standalone Python script to clean up old media attachments from Signal Desktop's local storage, freeing up disk space while preserving message text.

## Why This Script?

Signal Desktop stores all media attachments (photos, videos, audio, documents) locally on your computer. Over time, this can consume significant disk space (often several GB or more). This script allows you to delete old attachments while keeping your message history intact.

## Features

- ✅ Safely deletes old attachment files from disk
- ✅ Preserves all message text and metadata
- ✅ Supports flexible date formats (absolute and relative)
- ✅ Dry-run mode to preview what would be deleted
- ✅ Progress tracking and detailed statistics
- ✅ Handles all attachment types (photos, videos, audio, documents, thumbnails, etc.)
- ✅ Works with Signal's encrypted SQLCipher database

## Prerequisites

### 1. Python 3.7+

Check your Python version:
```bash
python3 --version
```

### 2. Install Required Dependencies

The script requires different dependencies based on your Signal Desktop configuration:

#### Basic Dependencies (Required)

```bash
pip install pysqlcipher3 python-dateutil
```

#### Encryption Dependencies (Required for Modern Signal Versions)

Modern Signal Desktop versions use encrypted database keys. You'll need additional packages:

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install libsqlcipher-dev libsecret-1-dev
pip install pysqlcipher3 python-dateutil keyring cryptography secretstorage
```

**macOS (with Homebrew):**
```bash
brew install sqlcipher
pip install pysqlcipher3 python-dateutil keyring cryptography
```

**Windows:**
```bash
pip install pysqlcipher3-binary python-dateutil keyring pywin32
```

**Note**: If you're using an older Signal Desktop version with legacy (plaintext) keys, you only need the basic dependencies. The script will automatically detect and use the appropriate key format.

## Usage

### Basic Syntax

```bash
python cleanup_signal_attachments.py --user-data <PATH> --before <DATE> [OPTIONS]
```

### Find Your User Data Path

**Linux:**
```bash
~/.config/Signal
```

**macOS:**
```bash
~/Library/Application Support/Signal
```

**Windows:**
```bash
%APPDATA%\Signal
```

### Examples

#### 1. Dry Run (Preview Only)

See what would be deleted without actually deleting anything:

```bash
# Linux
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal \
  --before "1 year ago" \
  --dry-run

# macOS
python cleanup_signal_attachments.py \
  --user-data ~/Library/Application\ Support/Signal \
  --before "1 year ago" \
  --dry-run
```

#### 2. Delete Attachments Older Than 1 Year

```bash
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal \
  --before "1 year ago"
```

#### 3. Delete Attachments Before a Specific Date

```bash
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal \
  --before "2024-01-01"
```

#### 4. Delete Attachments Older Than 6 Months (Verbose)

```bash
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal \
  --before "6 months ago" \
  --verbose
```

#### 5. Delete Attachments Older Than 30 Days

```bash
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal \
  --before "30 days ago"
```

### Date Format Options

The script supports both absolute and relative dates:

**Absolute Dates:**
- `"2024-01-01"`
- `"2024-01-01 12:00:00"`
- `"2023-06-15"`

**Relative Dates:**
- `"1 year ago"`
- `"6 months ago"`
- `"30 days ago"`
- `"2 weeks ago"`

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--user-data PATH` | Path to Signal Desktop user data directory (required) |
| `--before DATE` | Delete attachments before this date (required) |
| `--dry-run` | Preview what would be deleted without actually deleting |
| `-v, --verbose` | Enable verbose output for debugging |
| `-h, --help` | Show help message |

## Important Safety Notes

### ⚠️ CRITICAL: Close Signal Desktop First!

**ALWAYS close Signal Desktop completely before running this script!**

The database is locked while Signal is running, and the script will fail if Signal is open.

**How to ensure Signal is closed:**

Linux/macOS:
```bash
# Check if Signal is running
ps aux | grep -i signal

# Kill any Signal processes
killall signal-desktop
```

Windows:
```powershell
# Check Task Manager and end all Signal processes
```

### ⚠️ Backup Your Data First

**STRONGLY RECOMMENDED:** Make a backup of your Signal data before running this script:

Linux:
```bash
cp -r ~/.config/Signal ~/.config/Signal-backup
```

macOS:
```bash
cp -r ~/Library/Application\ Support/Signal ~/Library/Application\ Support/Signal-backup
```

Windows:
```powershell
Copy-Item -Recurse "$env:APPDATA\Signal" "$env:APPDATA\Signal-backup"
```

### ⚠️ This Action is Irreversible

Once attachment files are deleted, they cannot be recovered unless you have a backup. The script does NOT:
- Upload files to cloud storage
- Create trash/recycle bin copies
- Keep any recovery copies

### Test with Dry Run First

**ALWAYS run with `--dry-run` first** to see what would be deleted:

```bash
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal \
  --before "1 year ago" \
  --dry-run
```

## What Gets Deleted

The script deletes these types of files:
- Photos and images
- Videos
- Audio messages and files
- Documents and PDFs
- Thumbnails and preview images
- Contact avatars
- Stickers
- Link preview images
- Any other media attachments

The script does NOT delete:
- Message text
- Message metadata (timestamps, read status, etc.)
- Conversation structure
- Contacts
- Groups
- Your encryption keys
- App settings

## Sample Output

```
======================================================================
Signal Desktop Attachment Cleanup
======================================================================
User data path: /home/user/.config/Signal
Cutoff date: 2024-01-01 00:00:00
Cutoff timestamp: 1704067200000
Mode: LIVE DELETION
======================================================================

⚠️  WARNING: This will permanently delete attachment files. Continue? (yes/no): yes

[INFO] Opening database: /home/user/.config/Signal/sql/db.sqlite
[INFO] Database opened successfully
[INFO] Querying messages before timestamp: 1704067200000
[INFO] Found 1543 messages with attachments

Processing 1543 messages...

Progress: 100/1543 messages processed, 234 files deleted, 123.45 MB freed
Progress: 200/1543 messages processed, 456 files deleted, 245.67 MB freed
...

======================================================================
Cleanup Summary
======================================================================
Messages processed: 1543
Files deleted: 3421
Space freed: 2.34 GB
Errors: 0
======================================================================
```

## Troubleshooting

### Error: "pysqlcipher3 is not installed"

Install the required dependency:
```bash
pip install pysqlcipher3
```

If that fails, try:
```bash
pip install pysqlcipher3-binary
```

### Error: "Database key not found in config.json"

This means Signal hasn't been set up yet, or the config file is corrupted. Make sure:
1. Signal Desktop has been installed and opened at least once
2. You've logged in and have an active account
3. You're pointing to the correct user data directory

### Error: "Failed to decrypt database"

Possible causes:
1. Signal is still running (close it completely)
2. The database is corrupted
3. You're using the wrong user data directory
4. The config.json file is from a different Signal installation

### Error: "Failed to decrypt modern encryptedKey"

Modern Signal versions store the database key in an encrypted format. This error occurs when the script can't decrypt it.

**Solutions:**

1. **Install missing encryption dependencies:**

   Linux:
   ```bash
   pip install keyring cryptography secretstorage
   sudo apt-get install libsecret-1-dev
   ```

   macOS:
   ```bash
   pip install keyring cryptography
   ```

   Windows:
   ```bash
   pip install keyring pywin32
   ```

2. **Run the script on the same machine as Signal Desktop:**
   The encryption key is tied to your system's keyring/keychain. You can't decrypt it on a different machine.

3. **Fallback to legacy key (temporary workaround):**
   If you need to run the script urgently and can't decrypt the modern key:
   - Back up your `config.json`
   - Remove the `encryptedKey` field from `config.json`
   - Start Signal Desktop once (it will regenerate a plaintext key)
   - Run the cleanup script
   - Restore your backup after (Signal will re-encrypt on next start)

### Error: "Database is locked"

Signal Desktop is still running. Close it completely and try again.

### No messages found

This is normal if:
- You haven't been using Signal Desktop for long
- All your messages are recent (after the cutoff date)
- Attachments have already been deleted

Try adjusting the `--before` date to see if more messages match.

## Performance Notes

- **Speed**: Processes approximately 50-100 messages per second
- **Memory**: Uses minimal memory (< 100 MB typically)
- **Disk I/O**: May be slow on older hard drives with many small files
- **Interruption**: You can press Ctrl+C to stop at any time (files already deleted won't be restored)

## Advanced Usage

### Working with Development/Test Instances

If you have multiple Signal instances (e.g., development, staging):

```bash
# Development instance
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal-development \
  --before "30 days ago"

# Staging instance
python cleanup_signal_attachments.py \
  --user-data ~/.config/Signal-staging \
  --before "30 days ago"
```

### Scripting / Automation

You can run this script in a cron job or scheduled task:

```bash
#!/bin/bash
# cleanup-signal-monthly.sh

# Run cleanup for attachments older than 1 year
python /path/to/cleanup_signal_attachments.py \
  --user-data ~/.config/Signal \
  --before "1 year ago" \
  2>&1 | tee -a /var/log/signal-cleanup.log
```

Make sure Signal is closed when the script runs!

## Comparison with Built-in Feature

If the Signal Desktop PR for this feature gets merged, you'll be able to do this cleanup directly from the app's Preferences. Until then, this script provides the same functionality:

| Feature | This Script | Built-in UI (if merged) |
|---------|-------------|------------------------|
| Delete old attachments | ✅ | ✅ |
| Preserve message text | ✅ | ✅ |
| Date selection | ✅ | ✅ |
| Dry run | ✅ | ❌ |
| Progress tracking | ✅ | ✅ |
| Requires closing app | ✅ | ❌ |
| Automated/scripted | ✅ | ❌ |

## Contributing

This script was created as part of a Signal Desktop feature request. If you find bugs or have improvements, please contribute!

## License

SPDX-License-Identifier: AGPL-3.0-only

This script follows Signal Desktop's licensing.

## Disclaimer

This script modifies your Signal Desktop data. While it's been designed to be safe:
- Always backup your data first
- Test with --dry-run first
- The authors are not responsible for any data loss
- Use at your own risk

## Support

For issues with this script, please file an issue in the Signal Desktop repository or contact the contributor who created this script.

For issues with Signal Desktop itself, please use the official Signal support channels.
