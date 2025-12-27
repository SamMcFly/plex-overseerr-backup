#!/usr/bin/env python3
"""
Plex Library Backup & Overseerr Recovery Tool - Web UI
Simple web interface for backup and restoration operations
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import logging

try:
    from flask import Flask, render_template_string, request, jsonify
except ImportError:
    print("Flask is required. Install with: pip install flask")
    sys.exit(1)


# Set up logging with unicode support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

VERSION = "2.7"


class Config:
    """Manage configuration file"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file)
        self.data = self._load()
    
    def _load(self):
        """Load config from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return {}
        return {}
    
    def save(self):
        """Save config to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get config value"""
        return self.data.get(key, default)
    
    def set(self, key, value):
        """Set config value"""
        self.data[key] = value
        self.save()


app = Flask(__name__)
config = Config()

HTML = """<!DOCTYPE html><html><head><title>Plex Backup & Overseerr Restore</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>*{margin:0;padding:0;box-sizing:border-box;}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}.container{max-width:1000px;margin:0 auto;}header{text-align:center;color:white;margin-bottom:30px;}header h1{font-size:2.5em;margin-bottom:5px;}header p{font-size:0.9em;opacity:0.9;margin-bottom:5px;}.card{background:white;border-radius:10px;padding:25px;margin-bottom:20px;box-shadow:0 10px 30px rgba(0,0,0,0.3);}.card h2{color:#667eea;margin-bottom:15px;font-size:1.5em;border-bottom:2px solid #667eea;padding-bottom:10px;}.card h3{color:#764ba2;margin-top:20px;margin-bottom:10px;font-size:1.1em;}.form-group{margin-bottom:15px;}label{display:block;margin-bottom:5px;color:#333;font-weight:500;}.help-text{font-size:0.85em;color:#666;margin-top:3px;font-style:italic;}.help-section{background:#f0f4ff;border-left:4px solid #667eea;padding:12px;margin:15px 0;border-radius:5px;font-size:0.9em;color:#333;}input[type="text"],input[type="number"],textarea{width:100%;padding:10px;border:1px solid #ddd;border-radius:5px;font-size:1em;font-family:inherit;}input:focus,textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1);}button{padding:12px 20px;border:none;border-radius:5px;font-size:1em;font-weight:600;cursor:pointer;margin-right:10px;background:#667eea;color:white;}button:hover{background:#5568d3;}.file-input-wrapper{position:relative;}.file-input-display{width:100%;padding:10px;border:1px solid #ddd;border-radius:5px;background:#f9f9f9;color:#666;cursor:pointer;display:block;text-align:center;}.output{background:#f5f5f5;border:1px solid #ddd;border-radius:5px;padding:15px;max-height:500px;overflow-y:auto;font-family:monospace;font-size:0.85em;white-space:pre-wrap;margin-top:15px;display:none;}.output.show{display:block;}.status{padding:15px;border-radius:5px;margin-top:15px;display:none;}.status.show{display:block;}.status-success{background:#c6f6d5;color:#22543d;border-left:4px solid #48bb78;}.status-error{background:#fed7d7;color:#742a2a;border-left:4px solid #f56565;}.status-info{background:#bee3f8;color:#2c5282;border-left:4px solid #667eea;}.status-text{display:flex;align-items:center;gap:10px;}.spinner{display:inline-block;width:16px;height:16px;border:3px solid rgba(102,126,234,0.2);border-radius:50%;border-top-color:#667eea;animation:spin 0.8s linear infinite;}@keyframes spin{to{transform:rotate(360deg);}}.info{background:#edf2f7;border-left:4px solid #667eea;padding:15px;border-radius:5px;margin-bottom:15px;color:#2d3748;}.tabs{display:flex;gap:5px;margin-bottom:20px;border-bottom:2px solid #eee;flex-wrap:wrap;}.tab{padding:12px 15px;cursor:pointer;border:none;background:none;color:#666;border-bottom:3px solid transparent;font-weight:600;transition:all 0.2s;}.tab:hover{color:#667eea;}.tab.active{color:#667eea;border-bottom-color:#667eea;}.tab-content{display:none;}.tab-content.active{display:block;}</style></head><body><div class="container"><header><h1>Plex Backup & Overseerr Restore</h1><p>Disaster recovery tool for Plex media libraries</p><p>v""" + VERSION + """</p></header><div class="card"><h2>Setup</h2><div class="help-section"><strong>First Time Setup:</strong> Enter your Plex and Overseerr server details below, then click Test to verify the connection works.</div><h3>Plex Server</h3><div class="form-group"><label>Plex Server URL<span class="help-text">e.g., http://localhost:32400 or http://192.168.1.100:32400</span></label><input type="text" id="plexUrl" placeholder="http://localhost:32400"></div><div class="form-group"><label>Plex API Token<span class="help-text">Find this in Plex settings > Remote Access or get from account page</span></label><input type="text" id="plexToken"></div><h3>Overseerr Server</h3><div class="form-group"><label>Overseerr Server URL<span class="help-text">e.g., http://localhost:5055</span></label><input type="text" id="overseerrUrl" placeholder="http://localhost:5055"></div><div class="form-group"><label>Overseerr API Token<span class="help-text">Generate in Overseerr > Settings > API Keys</span></label><input type="text" id="overseerrToken"></div><h3>Backup Storage</h3><div class="form-group"><label>Backup Directory<span class="help-text">Where to save backup JSON files (creates if doesn't exist)</span></label><input type="text" id="backupDir" value="./backups"></div><button onclick="saveSettings()">Save Settings</button><button onclick="testConnection()">Test Connection</button><div id="settingsStatus" class="status"></div></div><div class="card"><div class="tabs"><button class="tab active" onclick="switchTab('backup')">Backup</button><button class="tab" onclick="switchTab('review')">Review Missing</button><button class="tab" onclick="switchTab('restore')">Restore</button></div><div id="backup" class="tab-content active"><h2>Create Backup</h2><div class="info">Backs up your Plex library metadata to a JSON file. Optionally verifies that all files still exist on disk.</div><div class="help-section"><strong>What happens:</strong> Creates a JSON backup file containing your library metadata. If "Verify files" is checked, it also confirms each file exists on your storage.</div><div class="form-group"><label>Libraries to backup (optional)<span class="help-text">Leave blank to backup all libraries. Enter one library name per line to backup specific libraries only.</span></label><textarea id="libraries" placeholder="Movies&#10;TV Shows" rows="4"></textarea></div><div class="form-group"><label><input type="checkbox" id="verify" checked> Verify files exist on disk</label><span class="help-text">Slower but ensures accurate file status</span></div><button id="backupBtn" onclick="startBackup()">Create Backup</button><div id="backupOutput" class="output"></div><div id="backupStatus" class="status"></div></div><div id="review" class="tab-content"><h2>Review Missing Files</h2><div class="info">Shows which files are missing from your library based on a backup.</div><div class="help-section"><strong>Use this to:</strong> See what files were missing at the time the backup was created, organized by library.</div><div class="form-group"><label>Select Backup File</label><div class="file-input-wrapper"><label class="file-input-display" for="reviewFilePicker">Click to select backup JSON file...</label><input type="file" id="reviewFilePicker" accept=".json" onchange="selectReviewFile(this)" style="display:none;"></div></div><input type="text" id="reviewFile" placeholder="Selected file" style="margin-top:10px;" readonly><button id="reviewBtn" onclick="reviewMissing()">Review Missing Files</button><div id="reviewOutput" class="output"></div><div id="reviewStatus" class="status"></div></div><div id="restore" class="tab-content"><h2>Restore Missing Files</h2><div class="info">Creates requests in Overseerr for files that are missing from your Plex library.</div><div class="help-section"><strong>How it works:</strong> Compares current Plex library to backup and submits Overseerr requests for missing items. You then approve them in Overseerr and they download automatically.</div><div class="form-group"><label>Select Backup File</label><div class="file-input-wrapper"><label class="file-input-display" for="restoreFilePicker">Click to select backup JSON file...</label><input type="file" id="restoreFilePicker" accept=".json" onchange="selectRestoreFile(this)" style="display:none;"></div></div><input type="text" id="restoreFile" placeholder="Selected file" style="margin-top:10px;" readonly><div class="form-group"><label>Batch Size<span class="help-text">How many requests to create per batch. Use smaller sizes to avoid overloading Overseerr.</span></label><input type="number" id="batchSize" value="10" min="1"></div><div class="help-section"><strong>Batch Mode:</strong> Creates limited requests and tracks progress. Click Batch again to create more. Use this to avoid overwhelming your system.<br/><strong>Full Mode:</strong> Creates all missing requests at once. Use with caution on large libraries.</div><button id="restoreBatchBtn" onclick="startRestoreBatch()">Batch (Limited)</button><button id="restoreFullBtn" onclick="startRestoreFull()">Full (All at Once)</button><div id="restoreOutput" class="output"></div><div id="restoreStatus" class="status"></div></div></div></div></body><script>document.addEventListener('DOMContentLoaded',loadSettings);function switchTab(n){document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));document.getElementById(n).classList.add('active');event.target.classList.add('active');}function loadSettings(){fetch('/api/settings').then(r=>r.json()).then(d=>{document.getElementById('plexUrl').value=d.plex_url||'';document.getElementById('plexToken').value=d.plex_token||'';document.getElementById('overseerrUrl').value=d.overseerr_url||'';document.getElementById('overseerrToken').value=d.overseerr_token||'';document.getElementById('backupDir').value=d.backup_dir||'./backups';});}function saveSettings(){const s={plex_url:document.getElementById('plexUrl').value,plex_token:document.getElementById('plexToken').value,overseerr_url:document.getElementById('overseerrUrl').value,overseerr_token:document.getElementById('overseerrToken').value,backup_dir:document.getElementById('backupDir').value};fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(s)}).then(r=>r.json()).then(d=>showStatus('settingsStatus','Settings saved!','success'));}function testConnection(){showStatus('settingsStatus','Testing...','info');fetch('/api/test-connection').then(r=>r.json()).then(d=>showStatus('settingsStatus',d.success?'Connection OK!':'Failed: '+d.error,d.success?'success':'error'));}function selectReviewFile(input){if(input.files&&input.files[0]){const file=input.files[0];const path=file.webkitRelativePath||file.name;document.getElementById('reviewFile').value=path;}}function selectRestoreFile(input){if(input.files&&input.files[0]){const file=input.files[0];const path=file.webkitRelativePath||file.name;document.getElementById('restoreFile').value=path;}}function startBackup(){const b=document.getElementById('backupDir').value,v=document.getElementById('verify').checked,t=document.getElementById('libraries').value.split(String.fromCharCode(10)).map(x=>x.trim()).filter(x=>x);document.getElementById('backupBtn').disabled=true;showOutput('backupOutput');showStatusLoading('backupStatus','Scanning Plex library...');fetch('/api/backup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({backup_dir:b,verify_files:v,libraries:t})}).then(r=>r.json()).then(d=>{document.getElementById('backupOutput').textContent=d.output||'No output';showStatus('backupStatus',d.success?'Backup complete: '+d.file:'Failed: '+d.error,d.success?'success':'error');}).catch(e=>showStatus('backupStatus','Error: '+e,'error')).finally(()=>{document.getElementById('backupBtn').disabled=false;});}function reviewMissing(){const f=document.getElementById('reviewFile').value;if(!f){showStatus('reviewStatus','Please select a backup file','error');return;}document.getElementById('reviewBtn').disabled=true;showOutput('reviewOutput');showStatusLoading('reviewStatus','Analyzing backup...');fetch('/api/review-missing',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({backup_file:f})}).then(r=>r.json()).then(d=>{document.getElementById('reviewOutput').textContent=d.output||'No output';showStatus('reviewStatus',d.success?'Found '+d.total+' missing files':'Failed: '+d.error,d.success?'success':'error');}).catch(e=>showStatus('reviewStatus','Error','error')).finally(()=>{document.getElementById('reviewBtn').disabled=false;});}function startRestoreBatch(){const b=document.getElementById('restoreFile').value,s=parseInt(document.getElementById('batchSize').value);if(!b){showStatus('restoreStatus','Please select a backup file','error');return;}document.getElementById('restoreBatchBtn').disabled=true;showOutput('restoreOutput');showStatusLoading('restoreStatus','Creating requests (batch size: '+s+')...');fetch('/api/restore-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({backup_file:b,batch_limit:s})}).then(r=>r.json()).then(d=>{document.getElementById('restoreOutput').textContent=d.output||'No output';showStatus('restoreStatus',d.success?'Batch complete - check Overseerr for new requests':'Failed: '+d.error,d.success?'success':'error');}).catch(e=>showStatus('restoreStatus','Error','error')).finally(()=>{document.getElementById('restoreBatchBtn').disabled=false;});}function startRestoreFull(){const b=document.getElementById('restoreFile').value,s=parseInt(document.getElementById('batchSize').value);if(!b){showStatus('restoreStatus','Please select a backup file','error');return;}if(!confirm('Create requests for ALL missing items? This may create many requests in Overseerr.')){return;}document.getElementById('restoreFullBtn').disabled=true;showOutput('restoreOutput');showStatusLoading('restoreStatus','Creating all requests...');fetch('/api/restore-full',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({backup_file:b,batch_limit:s})}).then(r=>r.json()).then(d=>{document.getElementById('restoreOutput').textContent=d.output||'No output';showStatus('restoreStatus',d.success?'All requests created - check Overseerr':'Failed: '+d.error,d.success?'success':'error');}).catch(e=>showStatus('restoreStatus','Error','error')).finally(()=>{document.getElementById('restoreFullBtn').disabled=false;});}function showStatus(e,m,t){const el=document.getElementById(e);el.innerHTML='<div class="status-text">'+m+'</div>';el.className='status show status-'+t;}function showStatusLoading(e,m){const el=document.getElementById(e);el.innerHTML='<div class="status-text"><span class="spinner"></span> '+m+'</div>';el.className='status show status-info';}function showOutput(e){document.getElementById(e).classList.add('show');}</script></html>"""

@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify({
            'plex_url': config.get('plex_url', ''),
            'plex_token': config.get('plex_token', ''),
            'overseerr_url': config.get('overseerr_url', ''),
            'overseerr_token': config.get('overseerr_token', ''),
            'backup_dir': config.get('backup_dir', './backups')
        })
    data = request.json
    config.set('plex_url', data.get('plex_url', ''))
    config.set('plex_token', data.get('plex_token', ''))
    config.set('overseerr_url', data.get('overseerr_url', ''))
    config.set('overseerr_token', data.get('overseerr_token', ''))
    config.set('backup_dir', data.get('backup_dir', './backups'))
    return jsonify({'success': True})


@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    import requests
    plex_url = config.get('plex_url', '')
    plex_token = config.get('plex_token', '')
    if not plex_url or not plex_token:
        return jsonify({'success': False, 'error': 'Configure Plex settings'})
    try:
        response = requests.get(f'{plex_url}/identity', headers={'X-Plex-Token': plex_token}, timeout=5)
        return jsonify({'success': response.status_code == 200})
    except:
        return jsonify({'success': False, 'error': 'Cannot reach Plex'})


@app.route('/api/backup', methods=['POST'])
def backup():
    try:
        data = request.json
        script = Path('plex_overseerr_backup.py')
        if not script.exists():
            return jsonify({'success': False, 'error': 'plex_overseerr_backup.py not found', 'output': ''})
        
        backup_dir = data.get('backup_dir', './backups')
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        backup_file = str(Path(backup_dir) / f"plex_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        cmd = [sys.executable, '-u', str(script), '--plex-url', config.get('plex_url', ''), '--plex-token', config.get('plex_token', ''), '--export', backup_file]
        if not data.get('verify_files', True):
            cmd.append('--no-verify')
        if data.get('libraries'):
            cmd.extend(['--libraries'] + data['libraries'])
        
        logger.info(f"Running backup: {backup_file}")
        output = []
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.getcwd(), bufsize=1, encoding='utf-8', errors='replace')
        for line in iter(process.stdout.readline, ''):
            if line:
                output.append(line.rstrip())
                logger.info(line.rstrip())
        process.wait()
        
        return jsonify({'success': process.returncode == 0 and Path(backup_file).exists(), 'output': '\n'.join(output), 'file': backup_file})
    except Exception as e:
        logger.error(f"Backup error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'output': ''})


@app.route('/api/review-missing', methods=['POST'])
def review_missing():
    """Review missing files from backup"""
    try:
        data = request.json
        backup_file_path = data['backup_file']
        
        # Try multiple possible paths
        possible_paths = [
            Path(backup_file_path),
            Path('./backups') / backup_file_path,
            Path(config.get('backup_dir', './backups')) / backup_file_path,
        ]
        
        backup_file = None
        for path in possible_paths:
            if path.exists():
                backup_file = path
                break
        
        if backup_file is None:
            logger.error(f"Backup file not found. Tried: {possible_paths}")
            return jsonify({'success': False, 'error': f'Backup file not found: {backup_file_path}', 'output': ''})
        
        logger.info(f"Found backup file at: {backup_file}")
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        missing_items = []
        
        for lib_name, items in backup_data['libraries'].items():
            for item in items:
                if not item.get('file_exists', False):
                    missing_items.append({
                        'library': lib_name,
                        'title': item.get('title', 'Unknown'),
                        'type': item.get('type', 'unknown'),
                        'year': item.get('year'),
                        'file_path': item.get('file_path', 'N/A'),
                        'status': item.get('file_status', 'Unknown')
                    })
        
        # Group by library
        by_library = {}
        for item in missing_items:
            lib = item['library']
            if lib not in by_library:
                by_library[lib] = []
            by_library[lib].append(item)
        
        # Build output
        output = f"MISSING FILES - {len(missing_items)} items\n"
        output += "="*80 + "\n\n"
        
        for lib_name in sorted(by_library.keys()):
            items = by_library[lib_name]
            output += f"{lib_name} ({len(items)} missing):\n"
            output += "-"*80 + "\n"
            
            for item in sorted(items, key=lambda x: x['title']):
                year_str = f" ({item['year']})" if item['year'] else ""
                output += f"  • {item['title']}{year_str}\n"
                output += f"    Type: {item['type']}\n"
                output += f"    Expected: {item['file_path']}\n"
                output += f"    Status: {item['status']}\n\n"
        
        output += "\n" + "="*80 + "\n"
        output += "SUMMARY\n"
        output += "="*80 + "\n"
        for lib_name in sorted(by_library.keys()):
            output += f"  {lib_name}: {len(by_library[lib_name])} missing\n"
        output += f"\nTotal missing: {len(missing_items)}\n"
        
        return jsonify({'success': True, 'output': output, 'total': len(missing_items)})
    except Exception as e:
        logger.error(f"Review error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'output': ''})


@app.route('/api/restore-batch', methods=['POST'])
def restore_batch():
    try:
        data = request.json
        script = Path('plex_overseerr_backup.py')
        if not script.exists():
            return jsonify({'success': False, 'error': 'plex_overseerr_backup.py not found', 'output': ''})
        
        backup_file_path = data['backup_file']
        
        # Try multiple possible paths
        possible_paths = [
            Path(backup_file_path),
            Path('./backups') / backup_file_path,
            Path(config.get('backup_dir', './backups')) / backup_file_path,
        ]
        
        backup_file = None
        for path in possible_paths:
            if path.exists():
                backup_file = path
                break
        
        if backup_file is None:
            return jsonify({'success': False, 'error': f'Backup file not found: {backup_file_path}', 'output': ''})
        
        progress_file = backup_file.parent / f"{backup_file.stem}_progress.json"
        cmd = [sys.executable, '-u', str(script), '--plex-url', config.get('plex_url', ''), '--plex-token', config.get('plex_token', ''), '--import', str(backup_file), '--overseerr-url', config.get('overseerr_url', ''), '--overseerr-token', config.get('overseerr_token', ''), '--batch-limit', str(data.get('batch_limit', 10)), '--progress', str(progress_file)]
        
        logger.info("Running restore batch")
        output = []
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.getcwd(), bufsize=1, encoding='utf-8', errors='replace')
        for line in iter(process.stdout.readline, ''):
            if line:
                output.append(line.rstrip())
        process.wait()
        return jsonify({'success': process.returncode == 0, 'output': '\n'.join(output)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'output': ''})


@app.route('/api/restore-full', methods=['POST'])
def restore_full():
    try:
        data = request.json
        all_output = []
        for i in range(100):
            batch_resp = restore_batch()
            batch_data = json.loads(batch_resp.get_data(as_text=True))
            all_output.append(f"\n--- Batch {i+1} ---\n{batch_data['output']}\n")
            if not batch_data['success'] or 'Batch limit reached' not in batch_data['output']:
                break
        return jsonify({'success': True, 'output': ''.join(all_output)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'output': ''})


if __name__ == '__main__':
    logger.info("="*60)
    logger.info(f"Plex Backup & Overseerr Restore v{VERSION}")
    logger.info("="*60)
    if not Path('plex_overseerr_backup.py').exists():
        logger.error("ERROR: plex_overseerr_backup.py not found!")
        sys.exit(1)
    logger.info("")
    logger.info("Starting web interface...")
    logger.info("")
    logger.info("Open your browser to: http://localhost:5000")
    logger.info("")
    logger.info("First time? Configure Plex and Overseerr settings on the Setup tab")
    logger.info("Then click 'Test Connection' to verify")
    logger.info("")
    logger.info("="*60)
    logger.info("Press CTRL+C to stop")
    logger.info("="*60)
    logger.info("")
    app.run(host='localhost', port=5000, debug=False)
