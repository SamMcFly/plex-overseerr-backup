#!/usr/bin/env python3
"""
Plex Backup Scheduler - Automate backups with retention policy
Runs backups on a schedule and automatically cleans up old backups
"""

import os
import sys
import json
import argparse
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
import time
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('plex_backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupScheduler:
    """Manages scheduled backups and retention"""
    
    def __init__(self, config_file='config.json', backup_dir='backups'):
        self.config_file = Path(config_file)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from config.json"""
        if not self.config_file.exists():
            logger.error(f"Config file not found: {self.config_file}")
            logger.error("Run ui.py first to create configuration")
            sys.exit(1)
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required = ['plex_url', 'plex_token']
            missing = [k for k in required if not config.get(k)]
            if missing:
                logger.error(f"Missing config fields: {missing}")
                logger.error("Configure in ui.py first")
                sys.exit(1)
            
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def run_backup(self, verify_files=True, libraries=None):
        """Execute backup using plex_overseerr_backup.py"""
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"plex_library_{timestamp}.json"
            
            logger.info("="*60)
            logger.info(f"Starting backup: {backup_file.name}")
            logger.info("="*60)
            
            # Build command
            cmd = [
                sys.executable, '-u', 'plex_overseerr_backup.py',
                '--plex-url', self.config['plex_url'],
                '--plex-token', self.config['plex_token'],
                '--export', str(backup_file)
            ]
            
            if not verify_files:
                cmd.append('--no-verify')
            
            if libraries:
                cmd.extend(['--libraries'] + libraries)
            
            # Run backup
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Log output
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)
            
            if result.returncode == 0:
                logger.info(f"✓ Backup successful: {backup_file}")
                logger.info(f"  File size: {backup_file.stat().st_size / 1024:.1f} KB")
                return backup_file
            else:
                logger.error(f"✗ Backup failed with code {result.returncode}")
                return None
                
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return None
    
    def cleanup_old_backups(self, days_to_keep=30):
        """Remove backups older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_timestamp = cutoff_date.timestamp()
            
            removed_count = 0
            removed_size = 0
            
            for backup_file in sorted(self.backup_dir.glob('plex_library_*.json')):
                file_mtime = backup_file.stat().st_mtime
                
                if file_mtime < cutoff_timestamp:
                    file_size = backup_file.stat().st_size
                    backup_file.unlink()
                    removed_count += 1
                    removed_size += file_size
                    logger.info(f"Removed old backup: {backup_file.name}")
            
            if removed_count > 0:
                logger.info(f"Cleanup complete: Removed {removed_count} backups ({removed_size / 1024:.1f} KB)")
            else:
                logger.info(f"No backups older than {days_to_keep} days")
        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def list_backups(self):
        """List all existing backups"""
        backups = sorted(self.backup_dir.glob('plex_library_*.json'), reverse=True)
        
        if not backups:
            logger.info("No backups found")
            return
        
        logger.info("\nBackup History:")
        logger.info("-" * 80)
        
        for backup in backups:
            stat = backup.stat()
            size_kb = stat.st_size / 1024
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"  {backup.name}")
            logger.info(f"    Modified: {mtime}")
            logger.info(f"    Size: {size_kb:.1f} KB")
        
        logger.info("-" * 80)
        logger.info(f"Total backups: {len(backups)}")
    
    def schedule_daily(self, hour=2, minute=0, verify_files=True, cleanup_days=30):
        """Schedule daily backup at specified time"""
        time_str = f"{hour:02d}:{minute:02d}"
        
        def backup_job():
            self.run_backup(verify_files=verify_files)
            self.cleanup_old_backups(days_to_keep=cleanup_days)
        
        schedule.every().day.at(time_str).do(backup_job)
        logger.info(f"Scheduled daily backup at {time_str}")
        
        return self._run_scheduler()
    
    def schedule_weekly(self, day='sunday', hour=2, minute=0, verify_files=True, cleanup_days=30):
        """Schedule weekly backup on specified day"""
        day = day.lower()
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        if day not in valid_days:
            logger.error(f"Invalid day: {day}. Use: {', '.join(valid_days)}")
            return False
        
        time_str = f"{hour:02d}:{minute:02d}"
        
        def backup_job():
            self.run_backup(verify_files=verify_files)
            self.cleanup_old_backups(days_to_keep=cleanup_days)
        
        day_method = getattr(schedule.every(), day)
        day_method.at(time_str).do(backup_job)
        logger.info(f"Scheduled weekly backup on {day} at {time_str}")
        
        return self._run_scheduler()
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        logger.info("Scheduler running. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped")
            return True
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Automate Plex backups with retention policy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # One-time backup now
  python backup_scheduler.py --backup-now

  # One-time backup with cleanup
  python backup_scheduler.py --backup-now --cleanup 30

  # Schedule daily at 2 AM with verification
  python backup_scheduler.py --daily 02:00 --verify

  # Schedule weekly on Sunday at 2 AM
  python backup_scheduler.py --weekly sunday 02:00

  # List existing backups
  python backup_scheduler.py --list

  # Manual cleanup (remove backups older than 60 days)
  python backup_scheduler.py --cleanup 60
        """
    )
    
    parser.add_argument('--config', default='config.json',
                       help='Config file (default: config.json)')
    parser.add_argument('--backup-dir', default='backups',
                       help='Backup directory (default: backups)')
    parser.add_argument('--backup-now', action='store_true',
                       help='Run backup immediately')
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip file verification (faster)')
    parser.add_argument('--list', action='store_true',
                       help='List all backups')
    parser.add_argument('--cleanup', type=int, metavar='DAYS',
                       help='Remove backups older than DAYS')
    parser.add_argument('--daily', metavar='HH:MM',
                       help='Schedule daily backup at HH:MM (24-hour format)')
    parser.add_argument('--weekly', nargs=2, metavar=('DAY', 'HH:MM'),
                       help='Schedule weekly backup (e.g., sunday 02:00)')
    parser.add_argument('--verify', action='store_true', default=True,
                       help='Verify files exist during backup (default: True)')
    parser.add_argument('--retention', type=int, default=30, metavar='DAYS',
                       help='Days to keep backups (default: 30)')
    
    args = parser.parse_args()
    
    # Create scheduler
    scheduler = BackupScheduler(args.config, args.backup_dir)
    
    # Handle list command
    if args.list:
        scheduler.list_backups()
        return
    
    # Handle one-time backup
    if args.backup_now:
        scheduler.run_backup(verify_files=not args.no_verify)
        if args.cleanup:
            scheduler.cleanup_old_backups(days_to_keep=args.cleanup)
        return
    
    # Handle cleanup only
    if args.cleanup:
        scheduler.cleanup_old_backups(days_to_keep=args.cleanup)
        return
    
    # Handle scheduling
    verify = args.verify and not args.no_verify
    
    if args.daily:
        try:
            hour, minute = map(int, args.daily.split(':'))
            scheduler.schedule_daily(
                hour=hour,
                minute=minute,
                verify_files=verify,
                cleanup_days=args.retention
            )
        except ValueError:
            logger.error(f"Invalid time format: {args.daily}. Use HH:MM")
            sys.exit(1)
    
    elif args.weekly:
        try:
            day, time_str = args.weekly
            hour, minute = map(int, time_str.split(':'))
            scheduler.schedule_weekly(
                day=day,
                hour=hour,
                minute=minute,
                verify_files=verify,
                cleanup_days=args.retention
            )
        except ValueError:
            logger.error(f"Invalid time format: {time_str}. Use HH:MM")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
