# Backup Scheduler

Automate your Plex backups with scheduled execution and automatic cleanup of old backups.

## Features

- 📅 **Daily or Weekly Scheduling** - Set backup times
- 🗑️ **Automatic Cleanup** - Remove old backups automatically
- ⏰ **Retention Policy** - Keep backups for N days (default: 30)
- 📋 **Backup Listing** - See all your backups
- 🎯 **One-Time Backups** - Run manually anytime
- 📝 **Logging** - Track all backup activities
- ⚙️ **Config Integration** - Uses your existing config.json

## Installation

The scheduler is included with the package. Just make sure you have the required dependencies:

```bash
pip install -r requirements.txt
```

The `schedule` library is required for scheduled backups.

## Quick Start

### One-Time Backup (Right Now)

```bash
python backup_scheduler.py --backup-now
```

### One-Time Backup + Cleanup Old Files

```bash
python backup_scheduler.py --backup-now --cleanup 30
```

Keeps backups from last 30 days, removes anything older.

### List All Backups

```bash
python backup_scheduler.py --list
```

Shows:
- Backup filenames
- Modification dates
- File sizes
- Total count

### Manual Cleanup

```bash
python backup_scheduler.py --cleanup 60
```

Removes backups older than 60 days (without running a new backup).

## Scheduling Backups

### Daily Backup at Specific Time

```bash
# Backup every day at 2:00 AM
python backup_scheduler.py --daily 02:00

# Backup every day at 11:00 PM
python backup_scheduler.py --daily 23:00

# Backup every day at 3:30 AM with no file verification (faster)
python backup_scheduler.py --daily 03:30 --no-verify
```

The script runs continuously and executes the backup at the specified time each day.

### Weekly Backup

```bash
# Backup every Sunday at 2:00 AM
python backup_scheduler.py --weekly sunday 02:00

# Backup every Friday at 11:00 PM
python backup_scheduler.py --weekly friday 23:00

# Valid days: monday, tuesday, wednesday, thursday, friday, saturday, sunday
```

### Customize Retention Policy

By default, backups older than 30 days are removed. Customize this:

```bash
# Keep backups for 60 days
python backup_scheduler.py --daily 02:00 --retention 60

# Keep backups for 7 days (weekly)
python backup_scheduler.py --daily 02:00 --retention 7

# Keep backups for 90 days (quarterly)
python backup_scheduler.py --daily 02:00 --retention 90
```

## Options

```
--config CONFIG          Config file (default: config.json)
--backup-dir DIR        Backup directory (default: backups)
--backup-now            Run backup immediately
--no-verify             Skip file verification (faster)
--list                  List all backups
--cleanup DAYS          Remove backups older than DAYS
--daily HH:MM           Schedule daily backup at HH:MM
--weekly DAY HH:MM      Schedule weekly backup
--verify                Verify files during backup (default)
--retention DAYS        Keep backups for DAYS (default: 30)
```

## Examples

### Daily Backup Strategy

Backup every day at 2 AM, keep 30 days of backups:

```bash
python backup_scheduler.py --daily 02:00
```

This runs continuously. When it finishes, backups older than 30 days are automatically removed.

### Weekly Backup Strategy

Backup every Sunday at 2 AM, keep 90 days of backups:

```bash
python backup_scheduler.py --weekly sunday 02:00 --retention 90
```

### Fast Daily Backup

Skip file verification for speed, backup at midnight, keep 14 days:

```bash
python backup_scheduler.py --daily 00:00 --no-verify --retention 14
```

### Multiple Backups (Weekly + Monthly)

Run two instances in separate terminals:

Terminal 1 - Weekly backup (Sundays):
```bash
python backup_scheduler.py --weekly sunday 02:00 --retention 90
```

Terminal 2 - Daily backup (keeps last 7 days):
```bash
python backup_scheduler.py --daily 03:00 --retention 7
```

This way you have:
- Daily backups from the last week
- Plus a full backup from the last 3 months

## Using with System Scheduler

Instead of running the Python scheduler continuously, use your system's scheduler:

### Linux/Mac - Cron

```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/plex-overseerr-backup && python backup_scheduler.py --backup-now --cleanup 30

# Weekly backup every Sunday at 2 AM
0 2 * * 0 cd /path/to/plex-overseerr-backup && python backup_scheduler.py --backup-now --cleanup 90
```

Add to crontab:
```bash
crontab -e
```

### Windows - Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Plex Backup"
4. Trigger: Daily at 2:00 AM
5. Action: Start program
   - Program: `python.exe`
   - Arguments: `backup_scheduler.py --backup-now --cleanup 30`
   - Start in: `/path/to/plex-overseerr-backup`

### Docker/System Service (Linux)

Create `/etc/systemd/system/plex-backup.service`:

```ini
[Unit]
Description=Plex Backup Scheduler
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/plex-overseerr-backup
ExecStart=/usr/bin/python3 backup_scheduler.py --daily 02:00
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable plex-backup.service
sudo systemctl start plex-backup.service
```

Check status:
```bash
sudo systemctl status plex-backup.service
```

## Logging

All backup activities are logged to `plex_backup_scheduler.log`:

```
2025-12-27 02:00:15 - INFO - ============================================================
2025-12-27 02:00:15 - INFO - Starting backup: plex_library_20251227_020015.json
2025-12-27 02:00:15 - INFO - ============================================================
2025-12-27 02:05:45 - INFO - Backup successful: plex_library_20251227_020015.json
2025-12-27 02:05:45 - INFO - File size: 1234.5 KB
2025-12-27 02:05:45 - INFO - Cleanup complete: Removed 2 backups (567.3 KB)
```

View logs:
```bash
tail -f plex_backup_scheduler.log
```

## Troubleshooting

### "Config file not found"

Make sure you've run `python ui.py` first to create `config.json`.

### "Cannot connect to Plex"

Check that:
- Plex URL is correct in config.json
- Plex token is valid
- Network connectivity to Plex

### Scheduler doesn't run

If using `--daily` or `--weekly`, the script runs continuously. Keep it running in a terminal or use system scheduler (cron/Task Scheduler).

### Backups taking too long

Use `--no-verify` to skip file verification:

```bash
python backup_scheduler.py --daily 02:00 --no-verify
```

## Best Practices

1. **Schedule during off-hours** - 2-4 AM is ideal to avoid peak usage
2. **Test first** - Run `--backup-now` to verify before scheduling
3. **Monitor logs** - Check `plex_backup_scheduler.log` regularly
4. **Keep enough backups** - At least 7-30 days recommended
5. **Use system scheduler** - More reliable than running Python continuously
6. **Backup to safe location** - Consider network storage

## Advanced: Backup to Remote Storage

Modify the backup directory to point to network storage:

```bash
# Mount network share (Linux/Mac)
python backup_scheduler.py --backup-dir /mnt/nas/plex-backups --daily 02:00

# SMB/Network path (Windows)
python backup_scheduler.py --backup-dir "\\nas\plex-backups" --daily 02:00
```

## Support

Having issues? Check:
1. `plex_backup_scheduler.log` for error messages
2. Run `--backup-now` to test immediately
3. Run `--list` to verify backups are being created
4. Check config.json for correct Plex settings
