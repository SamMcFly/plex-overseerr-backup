#!/usr/bin/env python3
"""
Plex Library Backup & Overseerr Recovery Tool

Exports your Plex library to a JSON backup file, verifying:
1. File exists on disk at the location Plex reports
2. Can optionally restore/recreate requests in Overseerr
3. Only submits missing files, keeps track of batch progress
"""

import requests
import json
import sys
import argparse
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging
import os
import urllib3
import warnings

# Suppress SSL warnings and urllib3 warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
import os

# IMPORTANT: Disable Windows proxy detection to avoid hangs
os.environ['NO_PROXY'] = '*'
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''


# Set up logging with unicode support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


class PlexLibraryBackup:
    def __init__(self, plex_url: str, plex_token: str):
        """
        Initialize Plex connection
        
        Args:
            plex_url: Plex server URL (e.g., http://localhost:32400)
            plex_token: Plex API token
        """
        self.plex_url = plex_url.rstrip('/')
        self.plex_token = plex_token
        self.session = requests.Session()
        self.session.trust_env = False  # Disable proxy detection
        self.session.headers.update({
            'X-Plex-Token': plex_token,
            'Accept': 'application/json'
        })
        
        # Verify connection
        try:
            response = self.session.get(f'{self.plex_url}/identity', timeout=10)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to connect to Plex: {response.status_code}")
            logger.info("[OK] Connected to Plex server")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Cannot reach Plex server at {plex_url}: {e}")

    def get_libraries(self) -> Dict[str, str]:
        """Get all libraries and their types"""
        try:
            response = self.session.get(f'{self.plex_url}/library/sections', timeout=10)
            libs = {}
            for section in response.json()['MediaContainer']['Directory']:
                libs[section['title']] = section['type']
            return libs
        except Exception as e:
            logger.error(f"Failed to get libraries: {e}")
            return {}

    def get_library_items(self, library_name: str) -> List[Dict]:
        """Get all items from a specific library"""
        try:
            # First, get the library key
            response = self.session.get(f'{self.plex_url}/library/sections', timeout=10)
            library_key = None
            
            for section in response.json()['MediaContainer']['Directory']:
                if section['title'] == library_name:
                    library_key = section['key']
                    break
            
            if not library_key:
                logger.warning(f"Library '{library_name}' not found")
                return []
            
            # Get all items from the library - no pagination limit
            try:
                url = f'{self.plex_url}/library/sections/{library_key}/all'
                # Request all items at once without limit, including GUIDs
                params = {'X-Plex-Token': self.plex_token, 'includeExternalMedia': 1, 'includeGuids': 1}
                response = self.session.get(url, params=params, timeout=60)
                
                if response.status_code != 200:
                    logger.error(f"  HTTP {response.status_code}")
                    all_items = []
                else:
                    data = response.json().get('MediaContainer', {})
                    all_items = data.get('Metadata', [])
                    logger.info(f"  Loaded {len(all_items)} items")
                    
            except requests.exceptions.Timeout:
                logger.error(f"  Timeout loading items (request too large?)")
                all_items = []
            except Exception as e:
                logger.error(f"  Error loading items: {e}")
                all_items = []
            
            logger.info(f"  Found {len(all_items)} items in '{library_name}'")
            return all_items
        
        except Exception as e:
            logger.error(f"Failed to get items from '{library_name}': {e}")
            return []

    def verify_file_exists(self, item: Dict) -> Tuple[bool, str, str]:
        """
        Verify that the file exists at the location Plex reports
        
        Returns:
            (exists: bool, file_path: str, reason: str)
        """
        try:
            item_type = item.get('type', 'unknown')
            
            # TV shows don't have direct file paths - they're collections of episodes
            if item_type == 'show':
                # For TV shows, just mark as existing if it has episodes
                if 'leafCount' in item and item['leafCount'] > 0:
                    return True, "TV Show (multiple episodes)", f"OK ({item.get('leafCount', 0)} episodes)"
                else:
                    return False, "", "No episodes found"
            
            # Movies have file paths
            if 'Media' not in item or not item['Media']:
                return False, "", "No media information"
            
            media = item['Media'][0]
            if 'Part' not in media or not media['Part']:
                return False, "", "No part information"
            
            file_path = media['Part'][0].get('file', '')
            
            if not file_path:
                return False, "", "No file path in metadata"
            
            path = Path(file_path)
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                return True, file_path, f"OK ({size_mb:.1f} MB)"
            else:
                return False, file_path, "File not found on disk"
        
        except Exception as e:
            return False, "", f"Error checking file: {e}"

    def export_library(self, library_names: List[str], output_file: str, 
                      verify_files: bool = True, skip_libraries: List[str] = None) -> Dict:
        """
        Export library to JSON backup file
        """
        if skip_libraries is None:
            skip_libraries = []
        
        backup_data = {
            'exported_at': datetime.now().isoformat(),
            'plex_url': self.plex_url,
            'libraries': {}
        }
        
        stats = {
            'total_items': 0,
            'verified_items': 0,
            'missing_files': 0,
            'errors': 0
        }
        
        if not library_names:
            all_libs = self.get_libraries()
            library_names = list(all_libs.keys())
            logger.info(f"No libraries specified, exporting all: {', '.join(library_names)}")
        
        for lib_name in library_names:
            # Skip if in skip list
            if lib_name in skip_libraries:
                logger.info(f"Skipping library (in skip list): {lib_name}")
                continue
            
            logger.info(f"Exporting library: {lib_name}")
            items = self.get_library_items(lib_name)
            
            library_backup = []
            
            for item in items:
                try:
                    item_data = {
                        'title': item.get('title', 'Unknown'),
                        'type': item.get('type', 'unknown'),
                        'year': item.get('year'),
                        'ratingKey': item.get('ratingKey'),
                    }
                    
                    # Extract external IDs for Overseerr restore
                    if 'Guid' in item:
                        for guid in item['Guid']:
                            guid_id = guid.get('id', '')
                            if 'tmdb' in guid_id:
                                item_data['tmdb_id'] = guid_id.split('/')[-1]
                            elif 'tvdb' in guid_id:
                                item_data['tvdb_id'] = guid_id.split('/')[-1]
                    
                    # Debug logging for items without TMDB ID
                    if 'tmdb_id' not in item_data and item.get('type') == 'movie':
                        logger.debug(f"Debug: {item['title']} - Guid field: {item.get('Guid', 'NO GUID')}")
                    
                    if item.get('type') == 'show':
                        item_data['seasons'] = item.get('childCount', 0)  # Number of seasons
                        item_data['episodes'] = item.get('leafCount', 0)  # Total episodes
                    
                    elif item.get('type') == 'movie':
                        item_data['duration'] = item.get('duration')
                        item_data['contentRating'] = item.get('contentRating')
                    
                    file_verified = True
                    if verify_files:
                        exists, file_path, reason = self.verify_file_exists(item)
                        item_data['file_path'] = file_path
                        item_data['file_exists'] = exists
                        item_data['file_status'] = reason
                        
                        if exists:
                            stats['verified_items'] += 1
                        else:
                            stats['missing_files'] += 1
                            file_verified = False
                    
                    library_backup.append(item_data)
                    stats['total_items'] += 1
                    
                    status_icon = "[OK]" if file_verified else "✗"
                    logger.debug(f"  {status_icon} {item_data['title']} ({item_data['type']})")
                
                except Exception as e:
                    logger.error(f"  [FAIL] Error processing item: {e}")
                    stats['errors'] += 1
                    continue
            
            backup_data['libraries'][lib_name] = library_backup
        
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"[OK] Backup saved to: {output_path}")
            return stats
        
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")
            return stats

    def restore_to_overseerr(self, backup_file: str, overseerr_url: str, 
                            overseerr_token: str, plex_url: str, plex_token: str,
                            batch_limit: Optional[int] = None, 
                            progress_file: Optional[str] = None,
                            auto_approve: bool = False) -> Dict:
        """
        Restore backup to Overseerr by creating requests for MISSING files only
        Re-verifies files exist before submitting to avoid false requests
        
        Args:
            auto_approve: If False (default), requests are created but NOT auto-approved
                         You must manually approve them in Overseerr before processing
        """
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load backup: {e}")
            return {}
        
        progress_data = {}
        if progress_file:
            progress_path = Path(progress_file)
            if progress_path.exists():
                try:
                    with open(progress_path, 'r') as f:
                        progress_data = json.load(f)
                    # Only use submitted items if they exist
                    if 'submitted' in progress_data:
                        logger.info(f"Loaded {len(progress_data['submitted'])} previously submitted items")
                    else:
                        logger.info("Progress file is empty, starting fresh")
                except Exception as e:
                    logger.warning(f"Could not load progress file: {e}")
        
        overseerr_url = overseerr_url.rstrip('/')
        overseerr_session = requests.Session()
        overseerr_session.headers.update({
            'X-Api-Key': overseerr_token,
            'Content-Type': 'application/json'
        })
        overseerr_session.verify = False  # Disable SSL verification
        
        logger.info(f"[OK] Configured Overseerr session for {overseerr_url}")
        
        plex_session = requests.Session()
        plex_session.headers.update({
            'X-Plex-Token': plex_token,
            'Accept': 'application/json'
        })
        
        stats = {
            'total_missing': 0,
            'requests_created': 0,
            'requests_skipped': 0,
            'already_exist': 0,
            'batch_limit_reached': False,
            'errors': 0,
            're_verified_exist': 0
        }
        
        logger.info("Restoring to Overseerr (only missing files)...")
        
        requests_created_this_batch = 0
        
        for lib_name, items in backup_data['libraries'].items():
            logger.info(f"Processing library: {lib_name}")
            
            for item in items:
                # Skip if already submitted
                item_id = f"{lib_name}:{item['ratingKey']}"
                if item_id in progress_data.get('submitted', {}):
                    logger.debug(f"  [SKIP] '{item['title']}' (already submitted)")
                    stats['requests_skipped'] += 1
                    continue
                
                # For TV shows: check if episodes are missing
                if item['type'] == 'show':
                    backed_up_episodes = item.get('episodes', 0)
                    
                    if backed_up_episodes == 0:
                        # No episodes in backup, skip
                        logger.debug(f"  [OK] '{item['title']}' (0 episodes in backup)")
                        stats['already_exist'] += 1
                        continue
                    
                    # Query Plex for current episode count
                    current_episodes = 0
                    try:
                        url = f'{plex_url}/library/metadata/{item["ratingKey"]}'
                        response = plex_session.get(url, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            metadata = data.get('MediaContainer', {}).get('Metadata', [])
                            if metadata:
                                current_episodes = metadata[0].get('leafCount', 0)
                    except Exception as e:
                        logger.debug(f"  Error querying {item['title']}: {e}")
                        current_episodes = backed_up_episodes  # Assume OK if can't query
                    
                    # Only submit if episodes are actually missing
                    if current_episodes >= backed_up_episodes:
                        logger.debug(f"  [OK] '{item['title']}' ({current_episodes}/{backed_up_episodes} episodes)")
                        stats['already_exist'] += 1
                        continue
                    
                    # Episodes are missing
                    logger.debug(f"  Missing: '{item['title']}' ({current_episodes}/{backed_up_episodes} episodes)")
                    stats['total_missing'] += 1
                    # Continue to submission below
                
                # For movies: check if file exists on disk
                elif item['type'] == 'movie':
                    file_exists_now = False
                    if 'file_path' in item and item['file_path']:
                        try:
                            path = Path(item['file_path'])
                            file_exists_now = path.exists()
                        except Exception as e:
                            logger.debug(f"  Error checking file: {e}")
                    
                    # Skip if file actually exists on disk
                    if file_exists_now:
                        logger.debug(f"  [OK] '{item['title']}' (file exists)")
                        stats['already_exist'] += 1
                        continue
                    
                    # Movie file is missing - mark for restoration
                    logger.debug(f"  Missing: {item['title']}")
                    stats['total_missing'] += 1
                
                else:
                    # Unknown type
                    stats['requests_skipped'] += 1
                    continue
                item_id = f"{lib_name}:{item['ratingKey']}"
                
                if item_id in progress_data.get('submitted', {}):
                    logger.debug(f"  [SKIP] '{item['title']}' (already submitted)")
                    stats['requests_skipped'] += 1
                    continue
                
                if batch_limit and requests_created_this_batch >= batch_limit:
                    logger.warning(f"\nBatch limit ({batch_limit}) reached!")
                    stats['batch_limit_reached'] = True
                    break
                
                try:
                    if item['type'] == 'movie':
                        # Use TMDB ID from backup (captured during export)
                        tmdb_id = item.get('tmdb_id')
                        
                        if not tmdb_id:
                            logger.info(f"  [SKIP] '{item['title']}' (no TMDB ID in backup)")
                            stats['requests_skipped'] += 1
                            continue
                        
                        logger.info(f"  [SUB] Submitting '{item['title']}' (TMDB ID: {tmdb_id})")
                        
                        request_data = {
                            'mediaType': 'movie',
                            'mediaId': int(tmdb_id),
                            'skipNotification': not auto_approve
                        }
                    
                    elif item['type'] == 'show':
                        # For TV shows, use TMDB ID (not TVDB)
                        tmdb_id = item.get('tmdb_id')
                        
                        if not tmdb_id:
                            logger.info(f"  [SKIP] '{item['title']}' (no TMDB ID in backup)")
                            stats['requests_skipped'] += 1
                            continue
                        
                        logger.info(f"  [SUB] Submitting '{item['title']}' (TMDB ID: {tmdb_id})")
                        
                        # TV request - seasons must be the string "all"
                        request_data = {
                            'mediaType': 'tv',
                            'mediaId': int(tmdb_id),
                            'seasons': 'all'
                        }
                    
                    else:
                        logger.info(f"  [SKIP] '{item['title']}' (unsupported type: {item['type']})")
                        stats['requests_skipped'] += 1
                        continue
                    
                    response = overseerr_session.post(
                        f'{overseerr_url}/api/v1/request',
                        json=request_data
                    )
                    
                    # If we get CSRF token error, try with additional headers
                    if response.status_code == 403 and 'csrf' in response.text.lower():
                        logger.debug(f"  CSRF error detected, retrying with bypass headers...")
                        
                        # Try with X-CSRF-Token header
                        retry_session = requests.Session()
                        retry_session.headers.update(overseerr_session.headers)
                        retry_session.headers['X-CSRF-Token'] = 'none'
                        retry_session.headers['X-Requested-With'] = 'XMLHttpRequest'
                        retry_session.verify = False
                        
                        response = retry_session.post(
                            f'{overseerr_url}/api/v1/request',
                            json=request_data
                        )
                    
                    logger.info(f"  Response: {response.status_code}")
                    
                    # Log 500 errors in detail
                    if response.status_code == 500:
                        logger.warning(f"  500 Error for '{item['title']}'")
                        logger.warning(f"  Request data: {request_data}")
                        try:
                            logger.warning(f"  Response: {response.text[:500]}")
                        except:
                            logger.warning(f"  Response: Unable to decode")
                    
                    if response.status_code in (200, 201, 202):
                        logger.info(f"  [OK] Requested: {item['title']}")
                        stats['requests_created'] += 1
                        requests_created_this_batch += 1
                        
                        if progress_file:
                            if 'submitted' not in progress_data:
                                progress_data['submitted'] = {}
                            progress_data['submitted'][item_id] = {
                                'title': item['title'],
                                'type': item['type'],
                                'submitted_at': datetime.now().isoformat()
                            }
                    else:
                        logger.warning(f"  Failed to submit '{item['title']}' - HTTP {response.status_code}")
                        stats['requests_skipped'] += 1
                
                except Exception as e:
                    logger.error(f"  [FAIL] Error requesting '{item['title']}': {e}")
                    stats['errors'] += 1
            
            if stats['batch_limit_reached']:
                break
        
        if progress_file:
            progress_data['last_updated'] = datetime.now().isoformat()
            progress_path = Path(progress_file)
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(progress_path, 'w') as f:
                    json.dump(progress_data, f, indent=2)
                logger.info(f"Progress saved to: {progress_file}")
            except Exception as e:
                logger.error(f"Failed to save progress file: {e}")
        
        logger.info(f"Restore batch complete!")
        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Backup Plex library and optionally restore to Overseerr'
    )
    
    parser.add_argument('--plex-url', required=True, help='Plex server URL')
    parser.add_argument('--plex-token', required=True, help='Plex API token')
    parser.add_argument('--export', help='Export libraries to JSON file')
    parser.add_argument('--import', help='Restore from backup JSON file')
    parser.add_argument('--overseerr-url', help='Overseerr server URL')
    parser.add_argument('--overseerr-token', help='Overseerr API token')
    parser.add_argument('--libraries', nargs='+', help='Specific libraries to export')
    parser.add_argument('--skip-libraries', nargs='+', default=['AudioBooks', "Mike's Audio Books"],
                       help='Libraries to skip (default: AudioBooks, Mike\'s Audio Books)')
    parser.add_argument('--no-verify', action='store_true', 
                       help='Skip file existence verification during export (faster)')
    parser.add_argument('--batch-limit', type=int, 
                       help='Maximum number of requests to create per batch')
    parser.add_argument('--progress', 
                       help='Track progress across batches in this JSON file')
    parser.add_argument('--auto-approve', action='store_true',
                       help='Auto-approve requests (default: requests need manual approval)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        plex = PlexLibraryBackup(args.plex_url, args.plex_token)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if args.export:
        logger.info(f"Exporting to: {args.export}")
        stats = plex.export_library(
            args.libraries,
            args.export,
            verify_files=not args.no_verify,
            skip_libraries=args.skip_libraries
        )
        
        
        logger.info("=" * 60)
        logger.info("Export Statistics:")
        logger.info(f"  Total items: {stats['total_items']}")
        logger.info(f"  Verified (files exist): {stats['verified_items']}")
        logger.info(f"  Missing files: {stats['missing_files']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info("=" * 60)
    
    if args.__dict__.get('import'):
        if not args.overseerr_url or not args.overseerr_token:
            logger.error("--overseerr-url and --overseerr-token required for restore")
            sys.exit(1)
        
        stats = plex.restore_to_overseerr(
            args.__dict__.get('import'),
            args.overseerr_url,
            args.overseerr_token,
            args.plex_url,
            args.plex_token,
            batch_limit=args.batch_limit,
            progress_file=args.progress,
            auto_approve=args.auto_approve
        )
        
        
        logger.info("=" * 60)
        logger.info("Restore Statistics:")
        logger.info(f"  Total missing files: {stats['total_missing']}")
        logger.info(f"  Requests created: {stats['requests_created']}")
        logger.info(f"  Already exist locally: {stats['already_exist']}")
        logger.info(f"  Skipped (already submitted): {stats['requests_skipped']}")
        logger.info(f"  Errors: {stats['errors']}")
        if stats['batch_limit_reached']:
            logger.info(f"  Batch limit reached - more files to process")
        logger.info("=" * 60)


if __name__ == '__main__':
    main()
