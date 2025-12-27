# Plex Backup & Overseerr Restore

A disaster recovery tool for Plex media libraries that backs up metadata and allows recovery through Overseerr.

## Why This Exists

If you lose a hard drive or multiple drives in your NAS, you don't want to back up all 30TB of media files. This tool backs up only the **metadata** (titles, years, ratings, paths) to a JSON file, then uses that to automatically submit recovery requests to Overseerr, which downloads the content again.

**Use case:** You lose a drive → run restore → Overseerr re-downloads everything automatically.

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

## Backup Format

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
