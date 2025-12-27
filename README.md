# Plex Backup & Overseerr Restore

A disaster recovery tool for Plex media libraries that backs up metadata and allows recovery through Overseerr.

## Important Limitations

### Overseerr Library Sync

**If Overseerr thinks you already have the files**, it will ignore restore requests. This happens when:
- Files were deleted from your storage
- But Overseerr has not synced with Plex yet
- Overseerr still sees the files in its cache

**Solution:** Force Overseerr to resync before restore:
1. Go to Overseerr Settings → Integrations → Plex
2. Click "Test Connection" or "Resync"
3. Wait for sync to complete
4. Then run the restore process

### Plex Library Not Updated

**If files are missing but Plex hasn't scanned yet**, the backup will not know they're missing:
- You delete files from disk
- But haven't run "Optimize Library" or library scan
- Backup still thinks files are there
- Restore won't process them as missing

**Solution:** Update Plex library before backup:
1. Delete or lose files from your storage
2. Go to Plex → Library → Settings
3. Run "Optimize Library" or full library scan
4. Wait for scan to complete
5. Then run backup

### Recommended Recovery Workflow

1. **Discover data loss** (files are missing from storage)
2. **Update Plex** - Run library scan so Plex knows files are gone
3. **Sync Overseerr** - Force Overseerr to resync with Plex
4. **Create backup** - Run `python backup_scheduler.py --backup-now` to detect missing
5. **Review missing** - Check "Review Missing" tab to see what will be restored
6. **Start restore** - Click "Restore to Overseerr"
7. **Wait for downloads** - Overseerr will re-download everything

## Features

- 📦 **Backup Plex Library** - Exports metadata for movies and TV shows
- 📋 **Review Missing Files** - See what was missing at backup time
- 🔄 **Restore via Overseerr** - Submit requests for missing content
- 🎬 **Movie & TV Support** - Handles both types with episode counting
- 🔍 **File Verification** - Checks if files still exist on disk
- 📊 **Progress Tracking** - Batch processing with state persistence
- 🌐 **Web Interface** - Easy-to-use Flask UI
- 📅 **Automated Backups** - Schedule daily/weekly backups with auto-cleanup

## Requirements

- Python 3.7+
- Plex Media Server
- Overseerr instance
- Network access to both servers

## Installation

### 1. Clone or Download

```bash
git clone https://github.com/SamMcFly/plex-overseerr-backup.git
cd plex-overseerr-backup
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `requests` - HTTP requests to Plex/Overseerr
- `flask` - Web UI server
- `schedule` - Backup scheduler

### 3. Get API Tokens

**Plex Token** - Follow official Plex documentation:
https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

Once you have your token, paste it into the Plex API Token field.

**Overseerr Token** - Settings → API Keys → Create API Key

See [GET_TOKENS.md](GET_TOKENS.md) for more details.

## Usage

### Option A: Web Interface (Recommended)

```bash
python ui.py
```

Then open `http://localhost:5000` in your browser.

**First time setup:**
1. Go to "Setup" tab
2. Enter Plex URL (e.g., `http://localhost:32400`)
3. Enter Plex API Token
4. Enter Overseerr URL (e.g., `http://localhost:5055`)
5. Enter Overseerr API Token
6. Click "Save Settings" to save your configuration
7. Click "Test Connection" to verify everything works

### Option B: Automated Backups

Use the backup scheduler for automatic daily or weekly backups:

```bash
# Daily backup at 2 AM, keep 30 days
python backup_scheduler.py --daily 02:00

# Weekly backup on Sunday at 2 AM, keep 90 days
python backup_scheduler.py --weekly sunday 02:00 --retention 90

# One-time backup now
python backup_scheduler.py --backup-now

# List all backups
python backup_scheduler.py --list
```

See [SCHEDULER.md](SCHEDULER.md) for complete scheduler documentation and system integration options.

### Option C: Command Line

**Create a backup:**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --export backups/plex_backup.json
```

**Review missing files:**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --import backups/plex_backup.json \
  --review-missing
```

**Restore to Overseerr:**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --import backups/plex_backup.json \
  --overseerr-url http://localhost:5055 \
  --overseerr-token YOUR_OVERSEERR_TOKEN
```

## Workflow

### Backing Up

1. Open web UI → "Backup" tab
2. (Optional) Select specific libraries
3. (Optional) Uncheck "Verify files" for speed
4. Click "Create Backup"
5. Backup JSON saved to `backups/` directory

### After Data Loss

1. Open web UI → "Restore" tab
2. Select your backup JSON file
3. Choose batch size (smaller = safer)
4. Click "Batch" to start
5. Watch Overseerr for new requests
6. Approve requests and let them download
7. Click "Batch" again to continue with more files

### Before You Restore - Critical Steps

**IMPORTANT:** Follow these steps before starting recovery to ensure it works:

1. **Update Plex Library (MUST DO FIRST)**
   - Delete files from your storage first
   - Open Plex → Library → Settings
   - Click "Optimize Library" or run a library scan
   - Wait for Plex to scan and update
   - Plex must recognize files are missing before backup can detect them

2. **Sync Overseerr (MUST DO SECOND)**
   - Open Overseerr → Settings → Integrations → Plex
   - Click "Test Connection" or "Resync"
   - Wait for Overseerr to resync with Plex
   - Overseerr cache must be updated or it will ignore restore requests

3. **Then Create Backup and Restore**
   - Now run backup to detect missing files
   - Review what's missing in "Review Missing" tab
   - Proceed with restore

**Why this matters:**
- If Plex hasn't scanned, it doesn't know files are missing → backup won't detect them
- If Overseerr hasn't synced, it thinks files still exist → it ignores restore requests
- This workflow ensures detection and recovery actually work

## Troubleshooting Restore Issues

### "No missing files detected"
**Cause:** Plex library hasn't been updated yet
**Solution:** 
1. Go to Plex → Library → Settings
2. Run "Optimize Library" or scan
3. Wait for scan to complete
4. Create a new backup
5. Check "Review Missing" again

### "Overseerr ignores restore requests"
**Cause:** Overseerr cache doesn't know files are gone
**Solution:**
1. Open Overseerr → Settings → Integrations → Plex
2. Click "Test Connection" or "Resync" 
3. Wait for full sync to complete
4. Try restore again

### "Shows/movies appear in backup but not requested"
**Cause:** File still exists on disk even though you thought it was deleted
**Solution:**
1. Check file system to confirm file is actually deleted
2. Verify file path in backup JSON
3. Double-check Plex has scanned and shows file as missing

Backups are JSON files containing:
- Library names
- Item metadata (title, year, type)
- External IDs (TMDB, TVDB)
- File paths
- Episode counts (for TV shows)

Example:
```json
{
  "libraries": {
    "Movies": [
      {
        "title": "Inception",
        "type": "movie",
        "year": 2010,
        "tmdb_id": "27205",
        "file_path": "/movies/Inception.mkv",
        "file_exists": true
      }
    ]
  }
}
```

## Important Notes

### TV Shows
- Episode counts are checked to detect missing episodes
- Only TV shows with missing episodes are submitted
- You can manually adjust which seasons to request in Overseerr

### Batch Mode
- Creates limited requests to avoid overwhelming Overseerr
- Progress is saved to `plex_library_*_progress.json`
- Click Batch again to resume

### File Verification
- Slower but ensures accuracy
- Checks that files still exist on disk
- Uncheck if backups are taking too long

## Troubleshooting

### "Cannot read properties of undefined (reading 'filter')"
This error from Overseerr means the seasons parameter is wrong. Make sure you're using version 2.7+.

### Requests not appearing in Overseerr
- Check that the API key is valid
- Verify Overseerr URL is correct (with http/https)
- Check browser console for errors

### TV shows marked as missing but they're not
- Make sure your backup has correct episode counts
- Run a fresh backup - old backups may have wrong counts

## Development

### Project Structure
```
plex-overseerr-backup/
├── plex_overseerr_backup.py  # Main script
├── ui.py                      # Web interface
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── LICENSE                    # MIT License
```

### Adding Features
1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test with your Plex/Overseerr setup
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

Inspired by disaster recovery best practices and the need to protect media libraries from hardware failure.

## Support

Found a bug or have a feature request?
- Open an issue on GitHub
- Include your Python version and error messages

## Disclaimer

This tool reads from Plex and submits requests to Overseerr. Always test with a non-critical backup first. The author is not responsible for data loss or system issues.
