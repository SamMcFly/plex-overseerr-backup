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

### 7. Create Your First Backup

1. Click "Backup" tab
2. Click "Create Backup"
3. Wait for "Backup complete" message
4. Backup saved to `backups/` folder

### 8. Test Restore (Optional)

To test without losing data:
1. Click "Review Missing" tab
2. Select your backup file
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
  --export backups/backup.json \
  --verify
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

## Troubleshooting

### "Module not found: requests"
```bash
pip install requests
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

## Next Steps

- Read full README.md for detailed documentation
- Schedule regular backups (weekly/monthly)
- Test restore process with a small backup first
- Keep backups in safe location (external drive, cloud storage)

## After Disaster: Recovery Process

**If files are lost from your storage:**

1. **Update Plex Library**
   - Go to Library → Settings
   - Run "Optimize Library" or library scan
   - Wait for Plex to recognize missing files

2. **Sync Overseerr**
   - Go to Settings → Integrations → Plex
   - Click "Test Connection" or "Resync"
   - Wait for full sync to complete

3. **Then Run Restore**
   - Create new backup: `python backup_scheduler.py --backup-now`
   - Review missing files in web UI
   - Start restore process
   - Monitor Overseerr for downloads

**Why both steps matter:**
- Plex must scan to know files are missing
- Overseerr must resync to request missing files
- Both must complete before restore will work correctly

## Support

Need help?
- Check README.md for detailed docs
- Open an issue on GitHub
- Include error messages and Python version
