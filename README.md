# Plex Backup & Overseerr Restore

A disaster recovery tool for Plex media libraries that backs up metadata and allows recovery through Overseerr.

## Normal Operation: Regular Backups

Schedule regular backups (daily, weekly, monthly - your choice):

```bash
# Daily backup at 2 AM
python backup_scheduler.py --daily 02:00

# Or one-time backup
python backup_scheduler.py --backup-now
```

Store backups in a safe location (external drive, cloud storage, different NAS, etc).

**This backup will be used later if disaster strikes.**

## Disaster Recovery: After Files Are Lost

**Use your pre-disaster backup with these steps:**

### Step 1: Update Plex Library

Plex must scan and recognize that files are missing:

1. Files have been lost from your storage (hardware failure, accidental deletion, etc)
2. Go to Plex → Library → Settings
3. Run "Optimize Library" or full library scan
4. Wait for scan to complete (Plex must recognize missing files)
5. Proceed to Step 2

### Step 2: Sync Overseerr

Overseerr must update its cache to know files are missing:

1. Go to Overseerr → Settings → Integrations → Plex
2. Click "Test Connection" or "Resync"
3. Wait for full sync to complete (must be fully synced)
4. Proceed to Step 3

### Step 3: Restore Using Your Pre-Disaster Backup

Use the backup file you created BEFORE the disaster:

1. Open web UI → "Restore" tab
2. Select your **pre-disaster backup file** (supports both `.json` and `.json.gz`)
3. Go to "Review Missing" tab to see what will be restored
4. Verify the list is correct
5. Click "Batch" to start restore
6. Overseerr will request missing content
7. Approve requests and monitor Overseerr for downloads
8. Click "Batch" again to continue with more files

### Why This Order Matters

- **Plex must scan first** - So it knows which files are missing
- **Overseerr must resync second** - So it will accept restore requests  
- **Use pre-disaster backup** - Contains all files that existed before loss occurred

### Important: Sonarr/Radarr Integration

**Overseerr submits requests to Sonarr/Radarr, but if those apps already have the media entry from the original request, they won't re-download it.**

**Automatic Solution (Recommended):**
Configure Radarr and Sonarr URLs/API tokens in the Settings tab. When you enable Force Mode during restore, the tool will automatically:
1. Clear entries from Overseerr
2. Clear movie entries from Radarr  
3. Clear series entries from Sonarr
4. Submit fresh requests

**Manual Solution:**
If you prefer not to configure Radarr/Sonarr integration:
- Use [Maintainerr](https://github.com/jorenn92/maintainerr) to clean up stale entries
- Or manually delete entries in Sonarr/Radarr before restoring

**Why this matters:**
Without clearing Radarr/Sonarr entries:
- Overseerr sends request to Sonarr/Radarr
- Sonarr/Radarr says "I already have this" (even though files are gone)
- Nothing gets downloaded

## Features

- 📦 **Backup Plex Library** - Exports metadata for movies and TV shows
- 📋 **Review Missing Files** - See what was missing at backup time
- 🔄 **Restore via Overseerr** - Submit requests for missing content
- 🎬 **Movie & TV Support** - Handles both types with episode counting
- 📺 **Detailed Episode Tracking** - Optional per-episode file verification for TV shows
- 🔍 **File Verification** - Checks if files still exist on disk
- 🗜️ **Automatic Compression** - Backups are gzip compressed by default
- ✅ **Integrity Verification** - SHA256 checksums detect corrupted backups
- 📊 **Progress Tracking** - Batch processing with state persistence
- 🌐 **Web Interface** - Easy-to-use Flask UI
- 📅 **Automated Backups** - Schedule daily/weekly backups with auto-cleanup
- 🔁 **Retry Logic** - Automatic retries with exponential backoff for transient failures
- ⏱️ **Rate Limiting** - Built-in delays to avoid overwhelming Overseerr

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

**Note:** API tokens are stored in plain text in `config.json`. Keep this file secure.

### Option B: Automated Backups

Use the backup scheduler for automatic daily or weekly backups:

```bash
# Daily backup at 2 AM, keep 30 days
python backup_scheduler.py --daily 02:00

# Weekly backup on Sunday at 2 AM, keep 90 days
python backup_scheduler.py --weekly sunday 02:00 --retention 90

# One-time backup now
python backup_scheduler.py --backup-now

# One-time backup with detailed episode tracking
python backup_scheduler.py --backup-now --detailed-episodes

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

**Create a backup with detailed episode tracking:**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --export backups/plex_backup.json \
  --detailed-episodes
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

**Force restore (when Overseerr ignores requests):**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --import backups/plex_backup.json \
  --overseerr-url http://localhost:5055 \
  --overseerr-token YOUR_OVERSEERR_TOKEN \
  --force
```

## Backup Modes

### Standard Mode (Default)

Fast backup that stores episode counts for TV shows:

```bash
python backup_scheduler.py --backup-now
```

- **Speed:** Fast (1 API call per library)
- **TV Shows:** Stores total episode count only
- **Restore:** Requests all seasons if episodes are missing

### Detailed Episode Mode

Slower backup that tracks individual episode files:

```bash
python backup_scheduler.py --backup-now --detailed-episodes
```

- **Speed:** Slower (3 API calls per TV show: show → seasons → episodes)
- **TV Shows:** Stores individual episode file paths
- **Restore:** Requests only specific missing seasons
- **Review:** Shows exactly which episodes are missing (e.g., S02E05, S03E10)

**When to use detailed mode:**
- You want to know exactly which episodes are missing
- You want to restore only affected seasons (not entire series)
- You have a smaller TV library (large libraries will be slow)

## Backup Compression

Backups are automatically compressed with gzip (`.json.gz`), typically reducing file size by 80-90%.

```bash
# Backup with compression (default)
python backup_scheduler.py --backup-now

# Backup without compression
python backup_scheduler.py --backup-now --no-compress
```

Both `.json` and `.json.gz` files are supported for restore and review operations.

## Workflow

### Backing Up

1. Open web UI → "Backup" tab
2. (Optional) Select specific libraries
3. (Optional) Enable "Detailed episode tracking" for per-episode tracking
4. (Optional) Uncheck "Verify files" for speed
5. Click "Create Backup"
6. Backup saved to `backups/` directory (compressed by default)

### After Data Loss

1. Files have been lost from storage (disaster occurred)
2. Follow the "Disaster Recovery" steps above (Plex scan, Overseerr sync)
3. Create new backup to detect what's missing
4. Review missing files
5. Open web UI → "Restore" tab
6. Select your backup file (`.json` or `.json.gz`)
7. Choose batch size (smaller = safer)
8. Click "Batch" to start
9. Watch Overseerr for new requests
10. Approve requests and let them download
11. Click "Batch" again to continue with more files

## Important Limitations

### Force Re-Request Mode

If Overseerr ignores your restore requests because it thinks content already exists, use **Force Mode**:

**Web UI:** 
1. Configure Radarr/Sonarr URLs and API tokens in Settings (optional but recommended)
2. Check "Force re-request (clear existing media data)" in the Restore tab

**Command Line:**
```bash
# Basic force mode (Overseerr only)
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --import backups/plex_backup.json \
  --overseerr-url http://localhost:5055 \
  --overseerr-token YOUR_OVERSEERR_TOKEN \
  --force

# Full force mode (Overseerr + Radarr + Sonarr)
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --import backups/plex_backup.json \
  --overseerr-url http://localhost:5055 \
  --overseerr-token YOUR_OVERSEERR_TOKEN \
  --radarr-url http://localhost:7878 \
  --radarr-token YOUR_RADARR_TOKEN \
  --sonarr-url http://localhost:8989 \
  --sonarr-token YOUR_SONARR_TOKEN \
  --force
```

**What it does:**
1. Looks up each item in Overseerr's database - clears if found
2. Looks up movies in Radarr - clears if found (when configured)
3. Looks up TV shows in Sonarr - clears if found (when configured)
4. Submits fresh request to Overseerr

**When to use:**
- Overseerr's cache is stale and thinks files exist when they don't
- Radarr/Sonarr still have entries from previous requests
- You've already requested something before but files were deleted
- Overseerr shows "Already Requested" for content you need

**Note:** This clears entries from all configured services. Files are NOT deleted (deleteFiles=false). For disaster recovery, this is usually exactly what you want - fresh entries that will trigger new downloads.

### Review Missing Now Dynamically Checks Files

**Review Missing reads backup file AND checks filesystem:**

**For Movies:**
- Dynamically checks if file exists on disk **right now**
- Shows file size if it exists
- Shows "File not found on disk" if missing
- Reports missing if file was deleted after backup

**For TV Shows (Standard Mode):**
- Cannot verify individual episode files
- Reports TV show type in output
- You must manually determine if episodes are missing

**For TV Shows (Detailed Mode):**
- Checks each episode file individually
- Shows exactly which episodes are missing (e.g., S02E05, S02E06)
- Restore requests only affected seasons

### Overseerr Ignores Restore Requests

**Problem:** Overseerr has stale cache and thinks files still exist
- Files were lost from storage (disaster)
- But Overseerr hasn't resynced with Plex yet
- Overseerr still believes files are there
- Overseerr ignores restore requests for "existing" files

**Solution:** Follow Step 2 above - Force Overseerr to resync before restore

### Plex Library Not Updated

**Problem:** Plex hasn't scanned and still thinks files exist
- Files were lost from storage (disaster)
- But Plex hasn't run library scan
- Plex library shows files as still present
- Restore won't see them as missing

**Solution:** Follow Step 1 above - Run Plex library scan first

## Backup File Format

Backups are JSON files (optionally gzip compressed) containing:
- Library names
- Item metadata (title, year, type)
- External IDs (TMDB, TVDB)
- File paths
- Episode counts (for TV shows)
- Detailed episode data (if `--detailed-episodes` used)
- SHA256 checksum for integrity verification
- Backup statistics

Example (standard mode):
```json
{
  "version": "1.2",
  "exported_at": "2025-01-15T14:30:00",
  "detailed_episodes": false,
  "checksum": "a1b2c3d4...",
  "stats": {
    "total_items": 500,
    "movies": 350,
    "shows": 150,
    "verified": 498,
    "missing": 2
  },
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

Example (detailed episode mode):
```json
{
  "title": "Breaking Bad",
  "type": "show",
  "detailed": true,
  "seasons": 5,
  "episodes": 62,
  "season_details": [
    {
      "season_num": 1,
      "episode_count": 7,
      "episodes": [
        {
          "episode_num": 1,
          "title": "Pilot",
          "file_path": "/tv/Breaking Bad/S01E01.mkv",
          "file_exists": true,
          "file_size_mb": 1250.5
        }
      ]
    }
  ]
}
```

## Important Notes

### TV Shows
- Episode counts are checked to detect missing episodes
- Only TV shows with missing episodes are submitted
- With detailed mode, only affected seasons are requested
- Without detailed mode, all seasons are requested
- You can manually adjust which seasons to request in Overseerr

### Batch Mode
- Creates limited requests to avoid overwhelming Overseerr
- Built-in 1-second delay between requests (rate limiting)
- Progress is saved to `plex_library_*_progress.json`
- Click Batch again to resume

### File Verification
- Slower but ensures accuracy
- Checks that files still exist on disk
- Uncheck if backups are taking too long

### Backup Integrity
- SHA256 checksums are calculated and stored in backup files
- On restore, checksums are verified and warnings shown if mismatch detected
- Helps detect corrupted backup files

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

### "Backup checksum mismatch" warning
- Backup file may be corrupted
- Try downloading/copying the backup file again
- Create a new backup if necessary

### Backup/restore timing out
- The tool includes automatic retry with exponential backoff
- For very large libraries, try backing up specific libraries separately
- Use `--no-verify` for faster backups

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
1. First, try resyncing: Overseerr → Settings → Integrations → Plex → "Test Connection" or "Resync"
2. If that doesn't work, use **Force Mode** in the Restore tab (or `--force` on command line)
3. Force mode clears Overseerr's record of the media so it can be re-requested

### "Requests created but nothing downloads"
**Cause:** Sonarr/Radarr already has the media entry from the original request
**Solution:**
1. Configure Radarr/Sonarr URLs and API tokens in Settings
2. Enable Force Mode when restoring - it will automatically clear entries from Radarr/Sonarr
3. If you don't want to use Force Mode, manually delete entries in Sonarr/Radarr

**Note:** Force mode with Radarr/Sonarr configured is the recommended approach for disaster recovery.

### "Shows/movies appear in backup but not requested"
**Cause:** File still exists on disk even though you thought it was deleted
**Solution:**
1. Check file system to confirm file is actually deleted
2. Verify file path in backup JSON
3. Double-check Plex has scanned and shows file as missing

## Development

### Project Structure
```
plex-overseerr-backup/
├── plex_overseerr_backup.py  # Main script
├── ui.py                      # Web interface
├── backup_scheduler.py        # Automated backups
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── INSTALL.md                 # Quick start guide
├── SCHEDULER.md               # Scheduler documentation
├── GET_TOKENS.md              # Token setup guide
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
