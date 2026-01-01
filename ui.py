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

# Suppress SSL warnings for self-signed certs
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Set up logging with unicode support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

VERSION = "3.1"


class Config:
    """Manage configuration file"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file)
        self.data = self._load()
    
    def _load(self):
        """Load config from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return {}
        return {}
    
    def save(self):
        """Save config to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            logger.warning("⚠️  Config saved with API tokens in plain text. Keep config.json secure!")
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


FAVICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAmUlEQVR42mNIq3uVVvM8veppeuXjjPKHGWX3MkvuZBbdyiq8kZV/NTvvcnbOxZys8zmZZ3LTT+WmnchLOZaXdDg/8WB+/P6CuL0FMbsKo3YURm4rCt9SFLaxOGR9cdDaksDVJf4rSv2WlfosYRi1YARb8J84MGoB8YAiC3BF8qgF9LOA5pE8mg9Gk+loPhitcEabLaMWUGoBAH+/pSbY2I7NAAAAAElFTkSuQmCC"

HTML = """<!DOCTYPE html>
<html>
<head>
<title>Plex Backup & Overseerr Restore</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/png" href="data:image/png;base64,""" + FAVICON_B64 + """">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}
.container{max-width:1000px;margin:0 auto;}
header{text-align:center;color:white;margin-bottom:30px;}
header h1{font-size:2.5em;margin-bottom:5px;}
header p{font-size:0.9em;opacity:0.9;margin-bottom:5px;}
.card{background:white;border-radius:10px;padding:25px;margin-bottom:20px;box-shadow:0 10px 30px rgba(0,0,0,0.3);}
.card h2{color:#667eea;margin-bottom:15px;font-size:1.5em;border-bottom:2px solid #667eea;padding-bottom:10px;}
.card h3{color:#764ba2;margin-top:20px;margin-bottom:10px;font-size:1.1em;}
.form-group{margin-bottom:15px;}
label{display:block;margin-bottom:5px;color:#333;font-weight:500;}
.help-text{font-size:0.85em;color:#666;margin-top:3px;font-style:italic;}
.help-section{background:#f0f4ff;border-left:4px solid #667eea;padding:12px;margin:15px 0;border-radius:5px;font-size:0.9em;color:#333;}
.warning-section{background:#fff3cd;border-left:4px solid #ffc107;padding:12px;margin:15px 0;border-radius:5px;font-size:0.9em;color:#856404;}
input[type="text"],input[type="number"],textarea{width:100%;padding:10px;border:1px solid #ddd;border-radius:5px;font-size:1em;font-family:inherit;}
input:focus,textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.1);}
button{padding:12px 20px;border:none;border-radius:5px;font-size:1em;font-weight:600;cursor:pointer;margin-right:10px;background:#667eea;color:white;}
button:hover{background:#5568d3;}
button:disabled{background:#ccc;cursor:not-allowed;}
button.secondary{background:#6c757d;}
button.secondary:hover{background:#5a6268;}
button.success{background:#48bb78;}
button.success:hover{background:#38a169;}
.file-input-wrapper{position:relative;}
.file-input-display{width:100%;padding:10px;border:1px solid #ddd;border-radius:5px;background:#f9f9f9;color:#666;cursor:pointer;display:block;text-align:center;}
.output{background:#f5f5f5;border:1px solid #ddd;border-radius:5px;padding:15px;max-height:500px;overflow-y:auto;font-family:monospace;font-size:0.85em;white-space:pre-wrap;margin-top:15px;display:none;}
.output.show{display:block;}
.status{padding:15px;border-radius:5px;margin-top:15px;display:none;}
.status.show{display:block;}
.status-success{background:#c6f6d5;color:#22543d;border-left:4px solid #48bb78;}
.status-error{background:#fed7d7;color:#742a2a;border-left:4px solid #f56565;}
.status-info{background:#bee3f8;color:#2c5282;border-left:4px solid #667eea;}
.status-text{display:flex;align-items:center;gap:10px;}
.spinner{display:inline-block;width:16px;height:16px;border:3px solid rgba(102,126,234,0.2);border-radius:50%;border-top-color:#667eea;animation:spin 0.8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.info{background:#edf2f7;border-left:4px solid #667eea;padding:15px;border-radius:5px;margin-bottom:15px;color:#2d3748;}
.tabs{display:flex;gap:5px;margin-bottom:20px;border-bottom:2px solid #eee;flex-wrap:wrap;}
.tab{padding:12px 15px;cursor:pointer;border:none;background:none;color:#666;border-bottom:3px solid transparent;font-weight:600;transition:all 0.2s;}
.tab:hover{color:#667eea;}
.tab.active{color:#667eea;border-bottom-color:#667eea;}
.tab-content{display:none;}
.tab-content.active{display:block;}
.last-backup{background:#e8f5e9;border-left:4px solid #4caf50;padding:12px;margin:15px 0;border-radius:5px;font-size:0.9em;color:#2e7d32;}

/* Selective restore styles */
.missing-list{max-height:400px;overflow-y:auto;border:1px solid #ddd;border-radius:5px;margin:15px 0;}
.missing-library{border-bottom:1px solid #eee;}
.missing-library:last-child{border-bottom:none;}
.library-header{background:#f8f9fa;padding:10px 15px;font-weight:600;color:#667eea;cursor:pointer;display:flex;align-items:center;gap:10px;}
.library-header:hover{background:#e9ecef;}
.library-header input[type="checkbox"]{width:18px;height:18px;cursor:pointer;}
.library-items{padding:0;display:none;}
.library-items.show{display:block;}
.missing-item{padding:10px 15px 10px 40px;border-top:1px solid #f0f0f0;display:flex;align-items:flex-start;gap:10px;}
.missing-item:hover{background:#fafafa;}
.missing-item input[type="checkbox"]{width:16px;height:16px;margin-top:3px;cursor:pointer;flex-shrink:0;}
.missing-item-info{flex:1;}
.missing-item-title{font-weight:500;color:#333;}
.missing-item-meta{font-size:0.85em;color:#666;margin-top:2px;}
.missing-item-type{display:inline-block;padding:2px 6px;border-radius:3px;font-size:0.75em;font-weight:600;text-transform:uppercase;margin-right:5px;}
.missing-item-type.movie{background:#e3f2fd;color:#1565c0;}
.missing-item-type.show{background:#f3e5f5;color:#7b1fa2;}
.selection-controls{display:flex;gap:10px;align-items:center;margin:15px 0;flex-wrap:wrap;}
.selection-count{color:#666;font-size:0.9em;}
.expand-collapse{font-size:0.85em;color:#667eea;cursor:pointer;margin-left:auto;}
.expand-collapse:hover{text-decoration:underline;}
</style>
</head>
<body>
<div class="container">
<header>
<h1>Plex Backup & Overseerr Restore</h1>
<p>Disaster recovery tool for Plex media libraries</p>
<p>v""" + VERSION + """</p>
</header>

<div class="card">
<h2>Setup</h2>
<div class="help-section"><strong>First Time Setup:</strong> Enter your Plex and Overseerr server details below, then click Test to verify the connection works.</div>
<div class="warning-section"><strong>⚠️ Security Notice:</strong> API tokens are stored in plain text in config.json. Keep this file secure and do not share it.</div>

<h3>Plex Server</h3>
<div class="form-group">
<label>Plex Server URL<span class="help-text">e.g., http://localhost:32400 or http://192.168.1.100:32400</span></label>
<input type="text" id="plexUrl" placeholder="http://localhost:32400">
</div>
<div class="form-group">
<label>Plex API Token<span class="help-text">Find this in Plex settings > Remote Access or get from account page</span></label>
<input type="text" id="plexToken">
</div>

<h3>Overseerr Server</h3>
<div class="form-group">
<label>Overseerr Server URL<span class="help-text">e.g., http://localhost:5055</span></label>
<input type="text" id="overseerrUrl" placeholder="http://localhost:5055">
</div>
<div class="form-group">
<label>Overseerr API Token<span class="help-text">Generate in Overseerr > Settings > API Keys</span></label>
<input type="text" id="overseerrToken">
</div>

<h3>Radarr Server (Optional - for Force Mode)</h3>
<div class="form-group">
<label>Radarr Server URL<span class="help-text">e.g., http://localhost:7878</span></label>
<input type="text" id="radarrUrl" placeholder="http://localhost:7878">
</div>
<div class="form-group">
<label>Radarr API Token<span class="help-text">Settings > General > API Key</span></label>
<input type="text" id="radarrToken">
</div>

<h3>Sonarr Server (Optional - for Force Mode)</h3>
<div class="form-group">
<label>Sonarr Server URL<span class="help-text">e.g., http://localhost:8989</span></label>
<input type="text" id="sonarrUrl" placeholder="http://localhost:8989">
</div>
<div class="form-group">
<label>Sonarr API Token<span class="help-text">Settings > General > API Key</span></label>
<input type="text" id="sonarrToken">
</div>

<h3>Backup Storage</h3>
<div class="form-group">
<label>Backup Directory<span class="help-text">Where to save backup JSON files (creates if doesn't exist)</span></label>
<input type="text" id="backupDir" value="./backups">
</div>

<button onclick="saveSettings()">Save Settings</button>
<button onclick="testConnection()">Test Connection</button>
<div id="settingsStatus" class="status"></div>
</div>

<div class="card">
<div class="tabs">
<button class="tab active" onclick="switchTab('backup')">Backup</button>
<button class="tab" onclick="switchTab('review')">Review & Select</button>
<button class="tab" onclick="switchTab('restore')">Restore (All)</button>
</div>

<div id="backup" class="tab-content active">
<h2>Create Backup</h2>
<div class="info">Backs up your Plex library metadata to a JSON file. Optionally verifies that all files still exist on disk.</div>
<div id="lastBackupInfo" class="last-backup" style="display:none;"></div>
<div class="help-section"><strong>What happens:</strong> Creates a JSON backup file containing your library metadata. If "Verify files" is checked, it also confirms each file exists on your storage.</div>

<div class="form-group">
<label>Libraries to backup (optional)<span class="help-text">Leave blank to backup all libraries. Enter one library name per line to backup specific libraries only.</span></label>
<textarea id="libraries" placeholder="Movies&#10;TV Shows" rows="4"></textarea>
</div>
<div class="form-group">
<label><input type="checkbox" id="verify" checked> Verify files exist on disk</label>
<span class="help-text">Slower but ensures accurate file status</span>
</div>
<div class="form-group">
<label><input type="checkbox" id="detailedEpisodes"> Detailed episode tracking (TV shows)</label>
<span class="help-text">Tracks individual episode files - much slower but enables per-episode and per-season restore</span>
</div>
<div class="form-group">
<label><input type="checkbox" id="compressBackup" checked> Compress backup (gzip)</label>
<span class="help-text">Reduces file size by 80-90%. Creates .json.gz file instead of .json</span>
</div>

<button id="backupBtn" onclick="startBackup()">Create Backup</button>
<div id="backupOutput" class="output"></div>
<div id="backupStatus" class="status"></div>
</div>

<div id="review" class="tab-content">
<h2>Review & Select Missing Files</h2>
<div class="info">Review missing files and select which ones to restore. Uncheck items you don't want to re-download (e.g., shows you've finished watching).</div>
<div class="help-section"><strong>How to use:</strong> Load a backup, review the missing items, uncheck anything you don't want, then click "Restore Selected" to submit requests to Overseerr.</div>

<div class="form-group">
<label>Select Backup File</label>
<div class="file-input-wrapper">
<label class="file-input-display" for="reviewFilePicker">Click to select backup JSON file...</label>
<input type="file" id="reviewFilePicker" accept=".json,.json.gz,.gz" onchange="selectReviewFile(this)" style="display:none;">
</div>
</div>
<input type="text" id="reviewFile" placeholder="Selected file" style="margin-top:10px;" readonly>
<button id="reviewBtn" onclick="loadMissingItems()">Load Missing Items</button>

<div id="selectionControls" class="selection-controls" style="display:none;">
<button class="secondary" onclick="selectAll()">Select All</button>
<button class="secondary" onclick="selectNone()">Select None</button>
<button class="secondary" onclick="selectMovies()">Movies Only</button>
<button class="secondary" onclick="selectShows()">Shows Only</button>
<span class="selection-count" id="selectionCount">0 selected</span>
<span class="expand-collapse" onclick="toggleAllLibraries()">Expand/Collapse All</span>
</div>

<div id="missingList" class="missing-list" style="display:none;"></div>

<div id="restoreSelectedControls" style="display:none;margin-top:15px;">
<div class="form-group">
<label><input type="checkbox" id="reviewForceRequest"> Force re-request (clear existing media data)</label>
<span class="help-text">Use when Overseerr/Radarr/Sonarr think files exist but they don't.</span>
</div>
<button id="restoreSelectedBtn" class="success" onclick="restoreSelected()">Restore Selected</button>
</div>

<div id="reviewOutput" class="output"></div>
<div id="reviewStatus" class="status"></div>
</div>

<div id="restore" class="tab-content">
<h2>Restore All Missing Files</h2>
<div class="info">Creates requests in Overseerr for ALL files that are missing from your Plex library. Use "Review & Select" tab if you want to choose specific items.</div>
<div class="help-section"><strong>How it works:</strong> Compares current Plex library to backup and submits Overseerr requests for missing items. You then approve them in Overseerr and they download automatically.</div>

<div class="form-group">
<label>Select Backup File</label>
<div class="file-input-wrapper">
<label class="file-input-display" for="restoreFilePicker">Click to select backup JSON file...</label>
<input type="file" id="restoreFilePicker" accept=".json,.json.gz,.gz" onchange="selectRestoreFile(this)" style="display:none;">
</div>
</div>
<input type="text" id="restoreFile" placeholder="Selected file" style="margin-top:10px;" readonly>

<div class="form-group">
<label>Batch Size<span class="help-text">How many requests to create per batch. Use smaller sizes to avoid overloading Overseerr.</span></label>
<input type="number" id="batchSize" value="10" min="1">
</div>

<div class="form-group">
<label><input type="checkbox" id="forceRequest"> Force re-request (clear existing media data)</label>
<span class="help-text">Use when Overseerr/Radarr/Sonarr think files exist but they don't. Clears their records so items can be re-requested.</span>
</div>

<div class="help-section">
<strong>Batch Mode:</strong> Creates limited requests and tracks progress. Click Batch again to create more.<br/>
<strong>Full Mode:</strong> Creates all missing requests at once. Use with caution.<br/>
<strong>Force Mode:</strong> Enable to clear entries from Overseerr, Radarr, and Sonarr (if configured) before requesting.
</div>

<button id="restoreBatchBtn" onclick="startRestoreBatch()">Batch (Limited)</button>
<button id="restoreFullBtn" onclick="startRestoreFull()">Full (All at Once)</button>
<div id="restoreOutput" class="output"></div>
<div id="restoreStatus" class="status"></div>
</div>

</div>
</div>

<script>
// Global state for missing items
let missingItemsData = [];
let currentBackupFile = '';

document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    loadLastBackupInfo();
});

function switchTab(n) {
    document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(e => e.classList.remove('active'));
    document.getElementById(n).classList.add('active');
    event.target.classList.add('active');
}

function loadSettings() {
    fetch('/api/settings').then(r => r.json()).then(d => {
        document.getElementById('plexUrl').value = d.plex_url || '';
        document.getElementById('plexToken').value = d.plex_token || '';
        document.getElementById('overseerrUrl').value = d.overseerr_url || '';
        document.getElementById('overseerrToken').value = d.overseerr_token || '';
        document.getElementById('radarrUrl').value = d.radarr_url || '';
        document.getElementById('radarrToken').value = d.radarr_token || '';
        document.getElementById('sonarrUrl').value = d.sonarr_url || '';
        document.getElementById('sonarrToken').value = d.sonarr_token || '';
        document.getElementById('backupDir').value = d.backup_dir || './backups';
    });
}

function loadLastBackupInfo() {
    fetch('/api/last-backup').then(r => r.json()).then(d => {
        if (d.success && d.last_backup) {
            const el = document.getElementById('lastBackupInfo');
            el.innerHTML = '<strong>Last backup:</strong> ' + d.last_backup.name + ' (' + d.last_backup.date + ', ' + d.last_backup.size + ')';
            el.style.display = 'block';
        }
    });
}

function saveSettings() {
    const s = {
        plex_url: document.getElementById('plexUrl').value,
        plex_token: document.getElementById('plexToken').value,
        overseerr_url: document.getElementById('overseerrUrl').value,
        overseerr_token: document.getElementById('overseerrToken').value,
        radarr_url: document.getElementById('radarrUrl').value,
        radarr_token: document.getElementById('radarrToken').value,
        sonarr_url: document.getElementById('sonarrUrl').value,
        sonarr_token: document.getElementById('sonarrToken').value,
        backup_dir: document.getElementById('backupDir').value
    };
    fetch('/api/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(s)
    }).then(r => r.json()).then(d => showStatus('settingsStatus', 'Settings saved! (Note: Tokens stored in plain text)', 'success'));
}

function testConnection() {
    showStatus('settingsStatus', 'Testing connections...', 'info');
    fetch('/api/test-connection').then(r => r.json()).then(d => 
        showStatus('settingsStatus', d.success ? (d.message || 'Connection OK!') : 'Failed: ' + d.error, d.success ? 'success' : 'error')
    );
}

function selectReviewFile(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const path = file.webkitRelativePath || file.name;
        document.getElementById('reviewFile').value = path;
        // Reset the list when a new file is selected
        document.getElementById('missingList').style.display = 'none';
        document.getElementById('selectionControls').style.display = 'none';
        document.getElementById('restoreSelectedControls').style.display = 'none';
        missingItemsData = [];
    }
}

function selectRestoreFile(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const path = file.webkitRelativePath || file.name;
        document.getElementById('restoreFile').value = path;
    }
}

function startBackup() {
    const b = document.getElementById('backupDir').value,
          v = document.getElementById('verify').checked,
          d = document.getElementById('detailedEpisodes').checked,
          c = document.getElementById('compressBackup').checked,
          t = document.getElementById('libraries').value.split(String.fromCharCode(10)).map(x => x.trim()).filter(x => x);
    
    document.getElementById('backupBtn').disabled = true;
    showOutput('backupOutput');
    showStatusLoading('backupStatus', d ? 'Scanning Plex library with detailed episode tracking (this may take a while)...' : 'Scanning Plex library...');
    
    fetch('/api/backup', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({backup_dir: b, verify_files: v, detailed_episodes: d, compress: c, libraries: t})
    }).then(r => r.json()).then(d => {
        document.getElementById('backupOutput').textContent = d.output || 'No output';
        showStatus('backupStatus', d.success ? 'Backup complete: ' + d.file : 'Failed: ' + d.error, d.success ? 'success' : 'error');
        loadLastBackupInfo();
    }).catch(e => showStatus('backupStatus', 'Error: ' + e, 'error'))
    .finally(() => { document.getElementById('backupBtn').disabled = false; });
}

function loadMissingItems() {
    const f = document.getElementById('reviewFile').value;
    if (!f) {
        showStatus('reviewStatus', 'Please select a backup file', 'error');
        return;
    }
    
    currentBackupFile = f;
    document.getElementById('reviewBtn').disabled = true;
    showStatusLoading('reviewStatus', 'Analyzing backup...');
    
    fetch('/api/get-missing-items', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({backup_file: f})
    }).then(r => r.json()).then(d => {
        if (d.success) {
            missingItemsData = d.items;
            renderMissingList(d.items, d.by_library);
            document.getElementById('selectionControls').style.display = 'flex';
            document.getElementById('missingList').style.display = 'block';
            document.getElementById('restoreSelectedControls').style.display = 'block';
            updateSelectionCount();
            showStatus('reviewStatus', 'Found ' + d.total + ' missing items. Select which ones to restore.', 'success');
        } else {
            showStatus('reviewStatus', 'Failed: ' + d.error, 'error');
        }
    }).catch(e => showStatus('reviewStatus', 'Error: ' + e, 'error'))
    .finally(() => { document.getElementById('reviewBtn').disabled = false; });
}

function renderMissingList(items, byLibrary) {
    const container = document.getElementById('missingList');
    let html = '';
    
    for (const libName of Object.keys(byLibrary).sort()) {
        const libItems = byLibrary[libName];
        if (libItems.length === 0) continue;
        
        const libId = 'lib_' + libName.replace(/[^a-zA-Z0-9]/g, '_');
        
        html += '<div class="missing-library">';
        html += '<div class="library-header" onclick="toggleLibrary(\\'' + libId + '\\')">';
        html += '<input type="checkbox" checked onclick="event.stopPropagation();toggleLibraryItems(\\'' + libId + '\\', this.checked)">';
        html += '<span>' + escapeHtml(libName) + ' (' + libItems.length + ' items)</span>';
        html += '</div>';
        html += '<div class="library-items" id="' + libId + '">';
        
        for (const item of libItems) {
            const itemId = item.id || (item.title + '_' + (item.year || ''));
            const typeClass = item.type === 'movie' ? 'movie' : 'show';
            const yearStr = item.year ? ' (' + item.year + ')' : '';
            const metaInfo = item.reason || '';
            
            html += '<div class="missing-item">';
            html += '<input type="checkbox" checked data-library="' + libId + '" data-item-id="' + escapeHtml(itemId) + '" data-type="' + item.type + '" onchange="updateSelectionCount()">';
            html += '<div class="missing-item-info">';
            html += '<div class="missing-item-title">';
            html += '<span class="missing-item-type ' + typeClass + '">' + item.type + '</span>';
            html += escapeHtml(item.title) + yearStr;
            html += '</div>';
            if (metaInfo) {
                html += '<div class="missing-item-meta">' + escapeHtml(metaInfo) + '</div>';
            }
            html += '</div></div>';
        }
        
        html += '</div></div>';
    }
    
    container.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function toggleLibrary(libId) {
    const el = document.getElementById(libId);
    el.classList.toggle('show');
}

function toggleAllLibraries() {
    const items = document.querySelectorAll('.library-items');
    const anyHidden = Array.from(items).some(el => !el.classList.contains('show'));
    items.forEach(el => {
        if (anyHidden) {
            el.classList.add('show');
        } else {
            el.classList.remove('show');
        }
    });
}

function toggleLibraryItems(libId, checked) {
    const checkboxes = document.querySelectorAll('input[data-library="' + libId + '"]');
    checkboxes.forEach(cb => cb.checked = checked);
    updateSelectionCount();
}

function selectAll() {
    document.querySelectorAll('.missing-item input[type="checkbox"]').forEach(cb => cb.checked = true);
    document.querySelectorAll('.library-header input[type="checkbox"]').forEach(cb => cb.checked = true);
    updateSelectionCount();
}

function selectNone() {
    document.querySelectorAll('.missing-item input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.querySelectorAll('.library-header input[type="checkbox"]').forEach(cb => cb.checked = false);
    updateSelectionCount();
}

function selectMovies() {
    document.querySelectorAll('.missing-item input[type="checkbox"]').forEach(cb => {
        cb.checked = cb.dataset.type === 'movie';
    });
    updateLibraryHeaderCheckboxes();
    updateSelectionCount();
}

function selectShows() {
    document.querySelectorAll('.missing-item input[type="checkbox"]').forEach(cb => {
        cb.checked = cb.dataset.type === 'show';
    });
    updateLibraryHeaderCheckboxes();
    updateSelectionCount();
}

function updateLibraryHeaderCheckboxes() {
    document.querySelectorAll('.missing-library').forEach(lib => {
        const header = lib.querySelector('.library-header input[type="checkbox"]');
        const items = lib.querySelectorAll('.missing-item input[type="checkbox"]');
        const checkedItems = lib.querySelectorAll('.missing-item input[type="checkbox"]:checked');
        header.checked = checkedItems.length === items.length;
        header.indeterminate = checkedItems.length > 0 && checkedItems.length < items.length;
    });
}

function updateSelectionCount() {
    const checked = document.querySelectorAll('.missing-item input[type="checkbox"]:checked').length;
    const total = document.querySelectorAll('.missing-item input[type="checkbox"]').length;
    document.getElementById('selectionCount').textContent = checked + ' of ' + total + ' selected';
    updateLibraryHeaderCheckboxes();
}

function getSelectedItems() {
    const selected = [];
    document.querySelectorAll('.missing-item input[type="checkbox"]:checked').forEach(cb => {
        const itemId = cb.dataset.itemId;
        // Find the matching item in our data
        for (const item of missingItemsData) {
            const id = item.id || (item.title + '_' + (item.year || ''));
            if (id === itemId) {
                selected.push(item);
                break;
            }
        }
    });
    return selected;
}

function restoreSelected() {
    const selected = getSelectedItems();
    if (selected.length === 0) {
        showStatus('reviewStatus', 'No items selected', 'error');
        return;
    }
    
    const force = document.getElementById('reviewForceRequest').checked;
    
    if (!confirm('Create requests for ' + selected.length + ' selected items?' + (force ? ' Force mode will clear existing media data.' : ''))) {
        return;
    }
    
    document.getElementById('restoreSelectedBtn').disabled = true;
    showOutput('reviewOutput');
    showStatusLoading('reviewStatus', 'Creating requests for ' + selected.length + ' items...');
    
    fetch('/api/restore-selected', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            backup_file: currentBackupFile,
            selected_items: selected,
            force: force
        })
    }).then(r => r.json()).then(d => {
        document.getElementById('reviewOutput').textContent = d.output || 'No output';
        showStatus('reviewStatus', d.success ? 'Restore complete - check Overseerr for new requests' : 'Failed: ' + d.error, d.success ? 'success' : 'error');
    }).catch(e => showStatus('reviewStatus', 'Error: ' + e, 'error'))
    .finally(() => { document.getElementById('restoreSelectedBtn').disabled = false; });
}

function startRestoreBatch() {
    const b = document.getElementById('restoreFile').value,
          s = parseInt(document.getElementById('batchSize').value),
          f = document.getElementById('forceRequest').checked;
    
    if (!b) {
        showStatus('restoreStatus', 'Please select a backup file', 'error');
        return;
    }
    
    document.getElementById('restoreBatchBtn').disabled = true;
    showOutput('restoreOutput');
    showStatusLoading('restoreStatus', f ? 'Creating requests with force mode (batch size: ' + s + ')...' : 'Creating requests (batch size: ' + s + ')...');
    
    fetch('/api/restore-batch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({backup_file: b, batch_limit: s, force: f})
    }).then(r => r.json()).then(d => {
        document.getElementById('restoreOutput').textContent = d.output || 'No output';
        showStatus('restoreStatus', d.success ? 'Batch complete - check Overseerr for new requests' : 'Failed: ' + d.error, d.success ? 'success' : 'error');
    }).catch(e => showStatus('restoreStatus', 'Error', 'error'))
    .finally(() => { document.getElementById('restoreBatchBtn').disabled = false; });
}

function startRestoreFull() {
    const b = document.getElementById('restoreFile').value,
          s = parseInt(document.getElementById('batchSize').value),
          f = document.getElementById('forceRequest').checked;
    
    if (!b) {
        showStatus('restoreStatus', 'Please select a backup file', 'error');
        return;
    }
    
    if (!confirm('Create requests for ALL missing items?' + (f ? ' Force mode will clear existing media data.' : '') + ' This may create many requests in Overseerr.')) {
        return;
    }
    
    document.getElementById('restoreFullBtn').disabled = true;
    showOutput('restoreOutput');
    showStatusLoading('restoreStatus', f ? 'Creating all requests with force mode...' : 'Creating all requests...');
    
    fetch('/api/restore-full', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({backup_file: b, batch_limit: s, force: f})
    }).then(r => r.json()).then(d => {
        document.getElementById('restoreOutput').textContent = d.output || 'No output';
        showStatus('restoreStatus', d.success ? 'All requests created - check Overseerr' : 'Failed: ' + d.error, d.success ? 'success' : 'error');
    }).catch(e => showStatus('restoreStatus', 'Error', 'error'))
    .finally(() => { document.getElementById('restoreFullBtn').disabled = false; });
}

function showStatus(e, m, t) {
    const el = document.getElementById(e);
    el.innerHTML = '<div class="status-text">' + m + '</div>';
    el.className = 'status show status-' + t;
}

function showStatusLoading(e, m) {
    const el = document.getElementById(e);
    el.innerHTML = '<div class="status-text"><span class="spinner"></span> ' + m + '</div>';
    el.className = 'status show status-info';
}

function showOutput(e) {
    document.getElementById(e).classList.add('show');
}
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/favicon.ico')
def favicon():
    """Serve favicon to avoid 404 errors"""
    import base64
    from flask import Response
    icon_data = base64.b64decode(FAVICON_B64)
    return Response(icon_data, mimetype='image/png')


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify({
            'plex_url': config.get('plex_url', ''),
            'plex_token': config.get('plex_token', ''),
            'overseerr_url': config.get('overseerr_url', ''),
            'overseerr_token': config.get('overseerr_token', ''),
            'radarr_url': config.get('radarr_url', ''),
            'radarr_token': config.get('radarr_token', ''),
            'sonarr_url': config.get('sonarr_url', ''),
            'sonarr_token': config.get('sonarr_token', ''),
            'backup_dir': config.get('backup_dir', './backups')
        })
    data = request.json
    config.set('plex_url', data.get('plex_url', ''))
    config.set('plex_token', data.get('plex_token', ''))
    config.set('overseerr_url', data.get('overseerr_url', ''))
    config.set('overseerr_token', data.get('overseerr_token', ''))
    config.set('radarr_url', data.get('radarr_url', ''))
    config.set('radarr_token', data.get('radarr_token', ''))
    config.set('sonarr_url', data.get('sonarr_url', ''))
    config.set('sonarr_token', data.get('sonarr_token', ''))
    config.set('backup_dir', data.get('backup_dir', './backups'))
    return jsonify({'success': True})


@app.route('/api/test-connection')
def test_connection():
    import requests as req
    
    results = []
    
    # Test Plex
    plex_url = config.get('plex_url', '')
    plex_token = config.get('plex_token', '')
    
    if not plex_url or not plex_token:
        return jsonify({'success': False, 'error': 'Plex URL and token required'})
    
    try:
        session = req.Session()
        session.trust_env = False
        session.verify = False
        response = session.get(
            f'{plex_url.rstrip("/")}/identity',
            headers={'X-Plex-Token': plex_token, 'Accept': 'application/json'},
            timeout=10
        )
        if response.status_code == 200:
            results.append('Plex: OK')
        else:
            return jsonify({'success': False, 'error': f'Plex: HTTP {response.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Plex: {str(e)}'})
    
    # Test Overseerr (optional but recommended)
    overseerr_url = config.get('overseerr_url', '')
    overseerr_token = config.get('overseerr_token', '')
    
    if overseerr_url and overseerr_token:
        try:
            response = session.get(
                f'{overseerr_url.rstrip("/")}/api/v1/status',
                headers={'X-Api-Key': overseerr_token},
                timeout=10
            )
            if response.status_code == 200:
                results.append('Overseerr: OK')
            else:
                results.append(f'Overseerr: HTTP {response.status_code}')
        except Exception as e:
            results.append(f'Overseerr: {str(e)}')
    
    # Test Radarr (optional)
    radarr_url = config.get('radarr_url', '')
    radarr_token = config.get('radarr_token', '')
    
    if radarr_url and radarr_token:
        try:
            response = session.get(
                f'{radarr_url.rstrip("/")}/api/v3/system/status',
                headers={'X-Api-Key': radarr_token},
                timeout=10
            )
            if response.status_code == 200:
                results.append('Radarr: OK')
            else:
                results.append(f'Radarr: HTTP {response.status_code}')
        except Exception as e:
            results.append(f'Radarr: {str(e)}')
    
    # Test Sonarr (optional)
    sonarr_url = config.get('sonarr_url', '')
    sonarr_token = config.get('sonarr_token', '')
    
    if sonarr_url and sonarr_token:
        try:
            response = session.get(
                f'{sonarr_url.rstrip("/")}/api/v3/system/status',
                headers={'X-Api-Key': sonarr_token},
                timeout=10
            )
            if response.status_code == 200:
                results.append('Sonarr: OK')
            else:
                results.append(f'Sonarr: HTTP {response.status_code}')
        except Exception as e:
            results.append(f'Sonarr: {str(e)}')
    
    return jsonify({'success': True, 'message': ' | '.join(results)})


@app.route('/api/last-backup')
def last_backup():
    """Get info about the most recent backup"""
    try:
        backup_dir = Path(config.get('backup_dir', './backups'))
        if not backup_dir.exists():
            return jsonify({'success': False, 'error': 'Backup directory does not exist'})
        
        # Find both .json and .json.gz backups
        json_backups = list(backup_dir.glob('plex_library_*.json'))
        gz_backups = list(backup_dir.glob('plex_library_*.json.gz'))
        all_backups = json_backups + gz_backups
        
        # Sort by modification time, newest first
        all_backups = sorted(all_backups, key=lambda f: f.stat().st_mtime, reverse=True)
        
        if not all_backups:
            return jsonify({'success': False, 'error': 'No backups found'})
        
        latest = all_backups[0]
        stat = latest.stat()
        size_kb = stat.st_size / 1024
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        return jsonify({
            'success': True,
            'last_backup': {
                'name': latest.name,
                'path': str(latest),
                'date': mtime,
                'size': f'{size_kb:.1f} KB'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/backup', methods=['POST'])
def backup():
    try:
        data = request.json
        script = Path('plex_overseerr_backup.py')
        if not script.exists():
            return jsonify({'success': False, 'error': 'plex_overseerr_backup.py not found', 'output': ''})
        
        backup_dir = Path(data.get('backup_dir', './backups'))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"plex_library_{timestamp}.json"
        
        cmd = [sys.executable, '-u', str(script), '--plex-url', config.get('plex_url', ''), '--plex-token', config.get('plex_token', ''), '--export', str(backup_file)]
        
        if not data.get('verify_files', True):
            cmd.append('--no-verify')
        
        if data.get('detailed_episodes', False):
            cmd.append('--detailed-episodes')
        
        libraries = data.get('libraries', [])
        if libraries:
            cmd.extend(['--libraries'] + libraries)
        
        logger.info(f"Running backup to {backup_file}")
        if data.get('detailed_episodes'):
            logger.info("Detailed episode tracking enabled - this may take a while")
        output = []
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.getcwd(), bufsize=1, encoding='utf-8', errors='replace')
        for line in iter(process.stdout.readline, ''):
            if line:
                output.append(line.rstrip())
        process.wait()
        
        # Handle compression if requested (default: True)
        compress = data.get('compress', True)
        final_file = backup_file
        
        if compress and process.returncode == 0 and backup_file.exists():
            import gzip
            import shutil
            compressed_file = Path(str(backup_file) + '.gz')
            try:
                original_size = backup_file.stat().st_size
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb', compresslevel=9) as f_out:
                        shutil.copyfileobj(f_in, f_out)
                compressed_size = compressed_file.stat().st_size
                reduction = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                # Remove original, keep compressed
                backup_file.unlink()
                final_file = compressed_file
                output.append(f"Compressed: {original_size/1024:.1f} KB → {compressed_size/1024:.1f} KB ({reduction:.1f}% reduction)")
                logger.info(f"Compressed backup: {original_size/1024:.1f} KB → {compressed_size/1024:.1f} KB ({reduction:.1f}% reduction)")
            except Exception as e:
                logger.warning(f"Compression failed: {e}")
                output.append(f"Compression failed: {e}")
        
        return jsonify({'success': process.returncode == 0, 'output': '\n'.join(output), 'file': str(final_file)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'output': ''})


def load_backup_file(backup_file_path):
    """Load and decompress backup file if needed"""
    import gzip
    
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
        return None, f'Backup file not found: {backup_file_path}'
    
    try:
        # Check if it's gzipped
        if str(backup_file).endswith('.gz'):
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
        else:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
        return backup_data, backup_file
    except Exception as e:
        return None, f'Error loading backup: {e}'


def analyze_missing_items(backup_data):
    """Analyze backup and return missing items with full metadata"""
    missing_items = []
    by_library = {}
    
    for lib_name, items in backup_data.get('libraries', {}).items():
        by_library[lib_name] = []
        
        for item in items:
            is_missing = False
            reason = ""
            
            if item['type'] == 'movie':
                file_path = item.get('file_path', '')
                if file_path:
                    try:
                        path = Path(file_path)
                        if not path.exists():
                            is_missing = True
                            reason = "File not found on disk"
                        else:
                            size_mb = path.stat().st_size / (1024 * 1024)
                            reason = f"OK ({size_mb:.1f} MB)"
                    except Exception as e:
                        is_missing = True
                        reason = f"Error checking: {e}"
                else:
                    is_missing = not item.get('file_exists', True)
                    reason = item.get('file_status', 'Unknown')
            
            elif item['type'] == 'show':
                if item.get('detailed') and 'season_details' in item:
                    missing_eps = []
                    total_eps = 0
                    
                    for season in item['season_details']:
                        season_num = season.get('season_num', 0)
                        
                        for ep in season.get('episodes', []):
                            total_eps += 1
                            file_path = ep.get('file_path', '')
                            ep_num = ep.get('episode_num', 0)
                            
                            ep_missing = False
                            if file_path:
                                try:
                                    if not Path(file_path).exists():
                                        ep_missing = True
                                except:
                                    ep_missing = True
                            elif not ep.get('file_exists', True):
                                ep_missing = True
                            
                            if ep_missing:
                                missing_eps.append(f"S{season_num:02d}E{ep_num:02d}")
                    
                    if missing_eps:
                        is_missing = True
                        if len(missing_eps) <= 10:
                            reason = f"Missing episodes: {', '.join(missing_eps)}"
                        else:
                            reason = f"Missing {len(missing_eps)}/{total_eps} episodes"
                        item['missing_episodes_list'] = missing_eps
                    else:
                        reason = f"TV Show: {total_eps} episodes (all present)"
                else:
                    episodes = item.get('episodes', 0)
                    seasons = item.get('seasons', 0)
                    reason = f"TV Show: {seasons} seasons, {episodes} episodes"
                    is_missing = (episodes == 0)
            
            if is_missing:
                # Create a unique ID for the item
                item_id = f"{item.get('title', 'Unknown')}_{item.get('year', '')}"
                
                missing_item = {
                    'id': item_id,
                    'library': lib_name,
                    'title': item.get('title', 'Unknown'),
                    'type': item['type'],
                    'year': item.get('year'),
                    'reason': reason,
                    'tmdb_id': item.get('tmdb_id'),
                    'tvdb_id': item.get('tvdb_id'),
                    'imdb_id': item.get('imdb_id'),
                }
                
                # Include episode details for shows
                if item['type'] == 'show':
                    missing_item['seasons'] = item.get('seasons')
                    missing_item['episodes'] = item.get('episodes')
                    if item.get('missing_episodes_list'):
                        missing_item['missing_episodes_list'] = item['missing_episodes_list']
                
                missing_items.append(missing_item)
                by_library[lib_name].append(missing_item)
    
    return missing_items, by_library


@app.route('/api/get-missing-items', methods=['POST'])
def get_missing_items():
    """Get missing items as JSON for selective restore"""
    try:
        data = request.json
        backup_file_path = data['backup_file']
        
        result, backup_file_or_error = load_backup_file(backup_file_path)
        if result is None:
            return jsonify({'success': False, 'error': backup_file_or_error})
        
        backup_data = result
        missing_items, by_library = analyze_missing_items(backup_data)
        
        return jsonify({
            'success': True,
            'items': missing_items,
            'by_library': by_library,
            'total': len(missing_items)
        })
    except Exception as e:
        logger.error(f"Get missing items error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/review-missing', methods=['POST'])
def review_missing():
    """Original review endpoint - returns text output"""
    try:
        data = request.json
        backup_file_path = data['backup_file']
        
        result, backup_file_or_error = load_backup_file(backup_file_path)
        if result is None:
            return jsonify({'success': False, 'error': backup_file_or_error, 'output': ''})
        
        backup_data = result
        backup_file = backup_file_or_error
        
        missing_items, by_library = analyze_missing_items(backup_data)
        
        # Format output
        output = "="*80 + "\n"
        output += "MISSING FILES REPORT\n"
        output += f"Backup: {backup_file.name}\n"
        output += f"Exported: {backup_data.get('exported_at', 'Unknown')}\n"
        if 'stats' in backup_data:
            output += f"Original Stats: {backup_data['stats'].get('total_items', '?')} items, "
            output += f"{backup_data['stats'].get('movies', '?')} movies, "
            output += f"{backup_data['stats'].get('shows', '?')} shows\n"
        output += "="*80 + "\n\n"
        
        for lib_name in sorted(by_library.keys()):
            items = by_library[lib_name]
            if items:
                output += f"\n--- {lib_name} ({len(items)} missing) ---\n"
                for item in items:
                    year = f" ({item.get('year')})" if item.get('year') else ""
                    item_type = item.get('type', 'unknown')
                    output += f"  [{item_type.upper()}] {item.get('title', 'Unknown')}{year}\n"
                    if item.get('reason'):
                        output += f"         {item.get('reason')}\n"
                output += "\n"
        
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


@app.route('/api/restore-selected', methods=['POST'])
def restore_selected():
    """Restore only selected items to Overseerr"""
    try:
        import requests as req
        import time
        import urllib3
        
        # Suppress SSL warnings if needed
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        data = request.json
        selected_items = data.get('selected_items', [])
        force = data.get('force', False)
        
        if not selected_items:
            return jsonify({'success': False, 'error': 'No items selected', 'output': ''})
        
        overseerr_url = config.get('overseerr_url', '').rstrip('/')
        overseerr_token = config.get('overseerr_token', '')
        
        if not overseerr_url or not overseerr_token:
            return jsonify({'success': False, 'error': 'Overseerr URL and token required', 'output': ''})
        
        # Create session - try with SSL verification first
        session = req.Session()
        session.trust_env = False
        session.headers.update({
            'X-Api-Key': overseerr_token,
            'Content-Type': 'application/json'
        })
        
        output = []
        stats = {'created': 0, 'skipped': 0, 'errors': 0}
        
        output.append(f"Processing {len(selected_items)} selected items...")
        output.append("")
        
        for item in selected_items:
            title = item.get('title', 'Unknown')
            item_type = item.get('type', 'movie')
            year = item.get('year', '')
            tmdb_id = item.get('tmdb_id')
            
            try:
                # Both movies and TV shows need TMDB ID for Overseerr
                if not tmdb_id:
                    output.append(f"[SKIP] {title} - No TMDB ID")
                    stats['skipped'] += 1
                    continue
                
                if item_type == 'movie':
                    request_data = {
                        'mediaType': 'movie',
                        'mediaId': int(tmdb_id)
                    }
                else:
                    # TV show - request all seasons
                    request_data = {
                        'mediaType': 'tv',
                        'mediaId': int(tmdb_id),
                        'seasons': 'all'
                    }
                
                # Submit request
                response = session.post(
                    f'{overseerr_url}/api/v1/request',
                    json=request_data,
                    timeout=30
                )
                
                if response.status_code in (200, 201, 202):
                    output.append(f"[OK] {title} ({year}) - Request created")
                    stats['created'] += 1
                elif response.status_code == 409:
                    output.append(f"[EXISTS] {title} ({year}) - Already requested or available")
                    stats['skipped'] += 1
                else:
                    output.append(f"[FAIL] {title} ({year}) - HTTP {response.status_code}")
                    stats['errors'] += 1
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                output.append(f"[ERROR] {title} - {str(e)}")
                stats['errors'] += 1
        
        output.append("")
        output.append("="*50)
        output.append("SUMMARY")
        output.append(f"  Requests created: {stats['created']}")
        output.append(f"  Skipped: {stats['skipped']}")
        output.append(f"  Errors: {stats['errors']}")
        output.append("="*50)
        
        return jsonify({
            'success': True,
            'output': '\n'.join(output),
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Restore selected error: {e}", exc_info=True)
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
        
        # Add --force flag if requested
        if data.get('force', False):
            cmd.append('--force')
            logger.info("Force mode enabled - will clear existing media data before requesting")
            
            # Add Radarr credentials if configured
            radarr_url = config.get('radarr_url', '')
            radarr_token = config.get('radarr_token', '')
            if radarr_url and radarr_token:
                cmd.extend(['--radarr-url', radarr_url, '--radarr-token', radarr_token])
                logger.info(f"  Radarr integration enabled: {radarr_url}")
            
            # Add Sonarr credentials if configured
            sonarr_url = config.get('sonarr_url', '')
            sonarr_token = config.get('sonarr_token', '')
            if sonarr_url and sonarr_token:
                cmd.extend(['--sonarr-url', sonarr_url, '--sonarr-token', sonarr_token])
                logger.info(f"  Sonarr integration enabled: {sonarr_url}")
        
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
    logger.warning("⚠️  Note: API tokens are stored in plain text in config.json")
    logger.info("")
    logger.info("="*60)
    logger.info("Press CTRL+C to stop")
    logger.info("="*60)
    logger.info("")
    app.run(host='localhost', port=5000, debug=False)
