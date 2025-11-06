# Testing Signal Desktop Development Build with Production Data

## The Issue

The development build is not loading your production Signal data because of one of these reasons:

1. **Container Environment**: You're running in a Docker container, but your Signal data is on the host machine
2. **Missing Data Copy**: The `Signal-development` directory doesn't exist or wasn't copied correctly
3. **Wrong User**: Running as a different user than your production Signal installation

## How Signal Development Data Loading Works

The development build looks for data in a **different directory** than production:

- **Production**: `~/.config/Signal` (Linux), `~/Library/Application Support/Signal` (macOS)
- **Development**: `~/.config/Signal-development` (Linux), `~/Library/Application Support/Signal-development` (macOS)

This is configured in `config/development.json`:
```json
{
  "storageProfile": "development"
}
```

The code in `app/user_config.main.ts` (lines 16-20) creates the path:
```typescript
userData = join(
  app.getPath('appData'),
  `Signal-${config.get('storageProfile')}`  // becomes "Signal-development"
);
```

## Solution Steps

### Step 1: Identify Your Setup

Run this diagnostic script:
```bash
./check-user-data.sh
```

Or manually check:
```bash
# Linux
ls -l ~/.config/Signal-development
ls -l ~/.config/Signal

# macOS
ls -l ~/Library/Application\ Support/Signal-development
ls -l ~/Library/Application\ Support/Signal
```

### Step 2: Copy Production Data

**IMPORTANT**: Make sure both Signal Desktop and the development build are **completely closed** before copying!

#### Linux:
```bash
# Close all Signal instances first!
cp -r ~/.config/Signal ~/.config/Signal-development
```

#### macOS:
```bash
# Close all Signal instances first!
cp -r ~/Library/Application\ Support/Signal ~/Library/Application\ Support/Signal-development
```

#### Windows:
```powershell
# Close all Signal instances first!
Copy-Item -Recurse "$env:APPDATA\Signal" "$env:APPDATA\Signal-development"
```

### Step 3: Verify the Copy

Check that these key files exist:

```bash
# Linux
ls ~/.config/Signal-development/sql/db.sqlite
ls ~/.config/Signal-development/attachments.noindex/

# macOS
ls ~/Library/Application\ Support/Signal-development/sql/db.sqlite
ls ~/Library/Application\ Support/Signal-development/attachments.noindex/
```

### Step 4: Run Development Build

```bash
cd /path/to/Signal-Desktop
pnpm install          # If not already done
pnpm run generate     # Build assets
pnpm start            # Start development build
```

You should see console output showing:
```
userData: /home/you/.config/Signal-development
```

## For Container/Docker Users

If you're running in a container (like this Claude Code environment), you have two options:

### Option A: Mount Host Data (Preferred)
Mount your host's Signal data into the container:

```bash
docker run -v ~/.config/Signal:/root/.config/Signal-development ...
```

### Option B: Copy into Container
Copy your production data into the container:

```bash
# From host machine
docker cp ~/.config/Signal container_name:/root/.config/Signal-development
```

### Option C: Run on Host Instead
The easiest solution is to run the development build on your host machine, not in the container.

## Troubleshooting

### "No chats appear"

1. **Check database exists**:
   ```bash
   ls -lh ~/.config/Signal-development/sql/db.sqlite
   ```
   Should be several MB or larger.

2. **Check permissions**:
   ```bash
   ls -l ~/.config/Signal-development/
   ```
   Make sure you own the directory.

3. **Check logs**:
   - Open DevTools: View → Toggle Developer Tools
   - Check Console for errors
   - Look for SQL/database errors

### "Database version mismatch"

If you see errors about database versions:

1. Your production Signal is likely newer than the development build
2. Try updating the development build to latest:
   ```bash
   git fetch origin
   git checkout main
   git pull
   pnpm install
   pnpm run generate
   ```

### "Cannot open database"

1. Make sure Signal production is **completely closed**
2. The database might be locked - check for leftover processes:
   ```bash
   ps aux | grep -i signal
   ```

3. Try copying again with production Signal closed

## Testing the Cleanup Feature

Once your data loads correctly:

1. Open DevTools to monitor: View → Toggle Developer Tools
2. Go to Preferences → Privacy
3. Find "Cleanup old media" (above "Delete application data")
4. Click "Cleanup" button
5. Select a date (e.g., 1 year ago)
6. Click "Delete Media"
7. Check Console for:
   - "deleteOldAttachments: Starting deletion..."
   - Progress logs
   - Success toast notification

## Important Notes

⚠️ **DO NOT** test the cleanup feature on your production `~/.config/Signal` directory!
Always use the development copy in `Signal-development`.

⚠️ After testing destructive features, you may want to re-copy from production:
```bash
rm -rf ~/.config/Signal-development
cp -r ~/.config/Signal ~/.config/Signal-development
```

⚠️ The development build connects to **staging servers** by default. You won't be able to send/receive actual messages unless you:
- Set up as a standalone device, OR
- Link to a phone that's also on staging servers

## Need Help?

If data still won't load:
1. Run `./check-user-data.sh` and share the output
2. Check the app console logs (DevTools → Console)
3. Look for errors in: `~/.config/Signal-development/logs/`
