# Quick Start Guide

## 5-Minute Setup

### 1. Install Python 3.7+

Check if you have Python:
```bash
python --version
```

### 2. Clone This Repository

```bash
git clone https://github.com/SamMcFly/plex-overseerr-backup.git
cd plex-overseerr-backup
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Get Your API Tokens

**Plex Token:**
- Follow: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
- Paste the token into the Plex API Token field

**Overseerr Token:**
- Open Overseerr
- Settings → Users (in sidebar)
- Click "Create API Key"

### 5. Start the UI

```bash
python ui.py
```

Open browser to: **http://localhost:5000**

### 6. Configure (First Time Only)

1. Click "Setup" tab
2. Enter your Plex URL and token
3. Enter your Overseerr URL and token
4. Click "Save Settings" to save your configuration
5. Click "Test Connection" to verify everything works

**Note:** API tokens are stored in plain text in `config.json`. Keep this file secure.

### 7. Create Your First Backup

1. Click "Backup" tab
2. (Optional) Check "Detailed episode tracking" for per-episode tracking
3. Click "Create Backup"
4. Wait for "Backup complete" message
5. Backup saved to `backups/` folder (compressed `.json.gz` by default)

### 8. Test Restore (Optional)

To test without losing data:
1. Click "Review Missing" tab
2. Select your backup file (`.json` or `.json.gz`)
3. Click "Review Missing Files"
4. You should see "Found 0 missing files" (since nothing is missing)

## Common Commands

**Just backup:**
```bash
python ui.py
# Then use the web interface
```

**Command line backup:**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_TOKEN \
  --export backups/backup.json
```

**Command line backup with detailed episodes:**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_TOKEN \
  --export backups/backup.json \
  --detailed-episodes
```

**Command line restore (batch):**
```bash
python plex_overseerr_backup.py \
  --plex-url http://localhost:32400 \
  --plex-token YOUR_PLEX_TOKEN \
  --import backups/backup.json \
  --overseerr-url http://localhost:5055 \
  --overseerr-token YOUR_OVERSEERR_TOKEN \
  --batch-limit 10
```

**Scheduled backup:**
```bash
# Daily at 2 AM
python backup_scheduler.py --daily 02:00

# One-time now
python backup_scheduler.py --backup-now
```

## Troubleshooting

### "Module not found: requests"
```bash
pip install requests
```

### "Module not found: flask"
```bash
pip install flask
```

### "Cannot connect to Plex"
- Check Plex URL is correct
- Check token is valid
- Make sure ports match (default 32400)

### "Cannot connect to Overseerr"
- Check Overseerr is running
- Check URL includes http:// or https://
- Check token is valid

### Web UI won't start
```bash
# Try explicit port
python ui.py
# Then visit http://localhost:5000
```

### Backup file is .json.gz - is that right?
Yes! Backups are automatically compressed with gzip to save space (80-90% smaller). Both `.json` and `.json.gz` files work for restore and review.

### Overseerr ignores restore requests
If Overseerr says content already exists or ignores your requests:
1. Try resyncing Overseerr with Plex first
2. If that doesn't work, enable "Force re-request" in the Restore tab
3. This clears Overseerr's record so content can be re-requested

## New Features

### Force Re-Request Mode
Force Overseerr to accept requests even if it thinks content exists:
```bash
python plex_overseerr_backup.py --import backup.json --force ...
```

Or check "Force re-request" in the web UI Restore tab.

### Detailed Episode Tracking
Track individual TV episode files for precise restore:
```bash
python backup_scheduler.py --backup-now --detailed-episodes
```

Or check the "Detailed episode tracking" box in the web UI.

### Automatic Compression
Backups are gzip compressed by default. To disable:
```bash
python backup_scheduler.py --backup-now --no-compress
```

### Integrity Verification
Backups include SHA256 checksums. If a backup is corrupted, you'll see a warning during restore.

## Next Steps

- Read full README.md for detailed documentation
- Schedule regular backups (weekly/monthly)
- **Store backups in safe location** (this is your insurance!)
- Test restore process with a small backup first
- Consider using detailed episode mode for weekly backups

## After Disaster: Recovery Process

**If files are lost, use your pre-disaster backup:**

1. **Update Plex Library**
   - Go to Library → Settings
   - Run "Optimize Library" or library scan
   - Wait for Plex to recognize missing files

2. **Sync Overseerr**
   - Go to Settings → Integrations → Plex
   - Click "Test Connection" or "Resync"
   - Wait for full sync to complete

3. **Restore Using Pre-Disaster Backup**
   - Open web UI → "Restore" tab
   - Select your **backup file from before the disaster** (`.json` or `.json.gz`)
   - Review what will be restored
   - Click "Batch" to start restore
   - Monitor Overseerr for downloads

**Why both steps matter:**
- Plex must scan to know which files are missing
- Overseerr must resync to request the missing files
- Use the backup you created before files were lost

**Important:** If Sonarr/Radarr still have the media entries (just without files), they won't re-download. You may need to remove stale entries from Sonarr/Radarr first, or use [Maintainerr](https://github.com/jorenn92/maintainerr) to clean them up automatically.

## Support

Need help?
- Check README.md for detailed docs
- Open an issue on GitHub
- Include error messages and Python version
