#!/usr/bin/env python3
"""
Lightweight Web Dashboard Server (with Dynamic Searchable Datalists)
---------------------------------------------------------------------
Uses Python's built-in `http.server` module to run a web dashboard UI.
Includes dynamic search dropdown menus (<datalist>) populated directly from
WorldGuard regions.yml and player identity maps!
"""

import os
import sys
import json
import re
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGIONS_FILE = os.path.join(BASE_DIR, "WorldGuard/worlds/world/regions.yml")

PLAYER_LIST = [
    {"name": "mustafa", "username": ".mustafahacker67"},
    {"name": "muhammad saleh", "username": ".HastyBag7675"},
    {"name": "omer saleh", "username": ".WiryCircle3938"},
    {"name": "hanan saleh", "username": "hanansaleh"},
    {"name": "manan saleh", "username": "manansaleh2007"},
    {"name": "rayan saleh", "username": "NightmareDady"},
    {"name": "azan saleh", "username": "azansalehhh"}
]

def get_region_list():
    if not os.path.exists(REGIONS_FILE):
        return []
    regions = []
    try:
        with open(REGIONS_FILE, "r") as f:
            for line in f:
                reg_match = re.match(r"^ {4}([a-zA-Z0-9_\-]+):", line)
                if reg_match:
                    rname = reg_match.group(1)
                    if rname not in regions and rname != "__global__":
                        regions.append(rname)
    except Exception:
        pass
    return regions

def run_script(cmd_list):
    try:
        res = subprocess.run([sys.executable] + cmd_list, cwd=BASE_DIR, capture_output=True, text=True)
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minecraft Admin Control Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --accent-emerald: #10b981;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-main);
            display: flex;
            min-height: 100vh;
        }

        .sidebar {
            width: 260px;
            background-color: #0b1120;
            border-right: 1px solid var(--border-color);
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            gap: 32px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
        }

        .brand-badge {
            background: linear-gradient(135deg, var(--accent-emerald), var(--accent-cyan));
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            color: #000;
            font-weight: 800;
        }

        .nav-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .nav-item {
            padding: 12px 16px;
            border-radius: 10px;
            color: var(--text-muted);
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nav-item:hover, .nav-item.active {
            background-color: rgba(255, 255, 255, 0.05);
            color: #fff;
        }

        .nav-item.active {
            border-left: 4px solid var(--accent-emerald);
            background-color: #1e293b;
        }

        .main-wrapper {
            flex: 1;
            padding: 32px 40px;
            overflow-y: auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }

        .header h1 {
            font-size: 1.8rem;
            font-weight: 700;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background-color: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-emerald);
            border-radius: 30px;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-emerald);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }

        .card-header {
            margin-bottom: 20px;
        }

        .card-header h2 {
            font-size: 1.25rem;
            font-weight: 600;
            color: #fff;
        }

        .card-header p {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 4px;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        input, select {
            background-color: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 12px 16px;
            color: #fff;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s ease;
        }

        input:focus, select:focus {
            border-color: var(--accent-cyan);
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 12px;
        }

        .checkbox-group input {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        .btn-group {
            display: flex;
            gap: 12px;
        }

        .btn {
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-emerald), #059669);
            color: #fff;
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--accent-yellow), #d97706);
            color: #fff;
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--accent-red), #dc2626);
            color: #fff;
        }

        .console-box {
            background-color: #090d16;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px;
            font-family: monospace;
            font-size: 0.9rem;
            color: #38bdf8;
            max-height: 250px;
            overflow-y: auto;
            white-space: pre-wrap;
            margin-top: 20px;
            display: none;
        }
    </style>
</head>
<body>

    <!-- Shared Searchable Datalists -->
    <datalist id="region-list">
        <!-- Populated via API -->
    </datalist>

    <datalist id="player-list">
        <!-- Populated via API -->
    </datalist>

    <div class="sidebar">
        <div class="brand">
            <div class="brand-badge">🎮</div>
            <span>Minecraft Dashboard</span>
        </div>
        <ul class="nav-list">
            <li class="nav-item active" onclick="showTab('sizer', event)">📐 Plot Sizer</li>
            <li class="nav-item" onclick="showTab('refund', event)">💎 Refund & Rollback</li>
            <li class="nav-item" onclick="showTab('floor', event)">🧱 Floor Generator</li>
            <li class="nav-item" onclick="showTab('members', event)">👤 Region Access</li>
        </ul>
    </div>

    <div class="main-wrapper">
        <div class="header">
            <h1>Server Management Studio</h1>
            <div class="status-badge">
                <span class="status-dot"></span>
                <span>Exaroton API Online</span>
            </div>
        </div>

        <!-- 1. PLOT SIZER TAB -->
        <div id="tab-sizer" class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <h2>Plot Sizer & Cutter (resize_plot.py)</h2>
                    <p>Redefine WorldGuard plot bounds to standard size categories with automatic undo backup.</p>
                </div>
                <form id="form-sizer">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Region ID (Search & Select)</label>
                            <input type="text" name="region" list="region-list" placeholder="Type or select region..." required>
                        </div>
                        <div class="form-group">
                            <label>Target Category</label>
                            <select name="category">
                                <option value="small">Small (8x8)</option>
                                <option value="normal">Normal (15x15)</option>
                                <option value="big">Big / Large (30x30)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Custom Height (Optional)</label>
                            <input type="number" name="height" placeholder="e.g. 15">
                        </div>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="sizer-dryrun" name="dry_run">
                        <label for="sizer-dryrun">Dry Run (Preview commands only)</label>
                    </div>
                    <br>
                    <div class="btn-group">
                        <button type="button" class="btn btn-primary" onclick="submitSizer(false)">📐 Resize Region</button>
                        <button type="button" class="btn btn-warning" onclick="submitSizer(true)">🔄 Undo Last Resize</button>
                    </div>
                </form>
                <div id="console-sizer" class="console-box"></div>
            </div>
        </div>

        <!-- 2. REFUND TAB -->
        <div id="tab-refund" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2>Upgrade Refund & Rollback (refund_upgrade.py)</h2>
                    <p>Calculates partial or full refunds, removes WorldGuard flags, and updates processed trades.</p>
                </div>
                <form id="form-refund">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Player Name (Search & Select)</label>
                            <input type="text" name="player" list="player-list" placeholder="Type or select player..." required>
                        </div>
                        <div class="form-group">
                            <label>Upgrade Type</label>
                            <select name="type">
                                <option value="pvp">PvP Protection (48 Emeralds)</option>
                                <option value="creeper">Creeper & Explosion (32 Emeralds)</option>
                                <option value="tnt">TNT Protection (32 Emeralds)</option>
                                <option value="mob">Mob Spawn Protection (64 Emeralds)</option>
                                <option value="fire">Fire Spread Protection (24 Emeralds)</option>
                                <option value="small_plot">Small Plot Expansion (32 Emeralds)</option>
                                <option value="all">ALL Protections & Upgrades</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Refund Percentage (%)</label>
                            <input type="number" name="percent" value="100" min="1" max="100">
                        </div>
                        <div class="form-group">
                            <label>Optional Plot Downsize</label>
                            <select name="downsize">
                                <option value="">Do Not Downsize</option>
                                <option value="small">Small (8x8)</option>
                                <option value="normal">Normal (15x15)</option>
                                <option value="big">Big (30x30)</option>
                            </select>
                        </div>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="refund-dryrun" name="dry_run">
                        <label for="refund-dryrun">Dry Run (Preview commands only)</label>
                    </div>
                    <br>
                    <div class="btn-group">
                        <button type="button" class="btn btn-danger" onclick="submitRefund()">💎 Execute Refund & Rollback</button>
                    </div>
                </form>
                <div id="console-refund" class="console-box"></div>
            </div>
        </div>

        <!-- 3. FLOOR GENERATOR TAB -->
        <div id="tab-floor" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2>Region Floor Generator (add_region_floor.py)</h2>
                    <p>Fills the bottom layer of a WorldGuard region with chosen material using Exaroton console.</p>
                </div>
                <form id="form-floor">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Region Name (Search & Select)</label>
                            <input type="text" name="region" list="region-list" placeholder="Type or select region..." required>
                        </div>
                        <div class="form-group">
                            <label>Floor Material Block</label>
                            <input type="text" name="material" placeholder="e.g. oak_planks, smooth_stone, grass_block">
                        </div>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="floor-dryrun" name="dry_run">
                        <label for="floor-dryrun">Dry Run (Preview fill command)</label>
                    </div>
                    <br>
                    <div class="btn-group">
                        <button type="button" class="btn btn-primary" onclick="submitFloor(false)">🧱 Generate Floor</button>
                        <button type="button" class="btn btn-warning" onclick="submitFloor(true)">🔄 Undo Floor Generation</button>
                    </div>
                </form>
                <div id="console-floor" class="console-box"></div>
            </div>
        </div>

        <!-- 4. REGION ACCESS TAB -->
        <div id="tab-members" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2>Region Access Manager (manage_region_players.py)</h2>
                    <p>Add/remove owners or members with auto player username resolution and rollback backup.</p>
                </div>
                <form id="form-members">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Region Name (Search & Select)</label>
                            <input type="text" name="region" list="region-list" placeholder="Type or select region..." required>
                        </div>
                        <div class="form-group">
                            <label>Action</label>
                            <select name="action">
                                <option value="addowner">Add Owner</option>
                                <option value="removeowner">Remove Owner</option>
                                <option value="addmember">Add Member</option>
                                <option value="removemember">Remove Member</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Player Name (Search & Select)</label>
                            <input type="text" name="player" list="player-list" placeholder="Type or select player..." required>
                        </div>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="members-dryrun" name="dry_run">
                        <label for="members-dryrun">Dry Run (Preview commands only)</label>
                    </div>
                    <br>
                    <div class="btn-group">
                        <button type="button" class="btn btn-primary" onclick="submitMembers(false)">👤 Update Region Access</button>
                        <button type="button" class="btn btn-warning" onclick="submitMembers(true)">🔄 Undo Access Changes</button>
                    </div>
                </form>
                <div id="console-members" class="console-box"></div>
            </div>
        </div>

    </div>

    <script>
        // Load Search Datalists on page load
        async function loadDatalists() {
            try {
                const resp = await fetch('/api/datalists');
                const data = await resp.json();
                
                const regList = document.getElementById('region-list');
                regList.innerHTML = '';
                data.regions.forEach(r => {
                    const opt = document.createElement('option');
                    opt.value = r;
                    regList.appendChild(opt);
                });

                const playList = document.getElementById('player-list');
                playList.innerHTML = '';
                data.players.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.name;
                    opt.label = p.name + ' (' + p.username + ')';
                    playList.appendChild(opt);
                });
            } catch(e) {
                console.error("Failed to load datalists:", e);
            }
        }

        document.addEventListener('DOMContentLoaded', loadDatalists);

        function showTab(tabId, evt) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            
            document.getElementById('tab-' + tabId).classList.add('active');
            if (evt && evt.currentTarget) {
                evt.currentTarget.classList.add('active');
            }
        }

        async function executeCommand(endpoint, data, consoleId) {
            const consoleBox = document.getElementById(consoleId);
            consoleBox.style.display = 'block';
            consoleBox.textContent = '⏳ Processing command...';

            try {
                const resp = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const res = await resp.json();
                consoleBox.textContent = res.stdout || res.stderr || 'Completed.';
            } catch(e) {
                consoleBox.textContent = '❌ API Error: ' + e;
            }
        }

        function submitSizer(isUndo) {
            const form = document.getElementById('form-sizer');
            const data = {
                region: form.region.value,
                category: form.category.value,
                height: form.height.value,
                dry_run: form.dry_run.checked,
                undo: isUndo
            };
            executeCommand('/api/sizer', data, 'console-sizer');
        }

        function submitRefund() {
            const form = document.getElementById('form-refund');
            const data = {
                player: form.player.value,
                type: form.type.value,
                percent: form.percent.value,
                downsize: form.downsize.value,
                dry_run: form.dry_run.checked
            };
            executeCommand('/api/refund', data, 'console-refund');
        }

        function submitFloor(isUndo) {
            const form = document.getElementById('form-floor');
            const data = {
                region: form.region.value,
                material: form.material.value,
                dry_run: form.dry_run.checked,
                undo: isUndo
            };
            executeCommand('/api/floor', data, 'console-floor');
        }

        function submitMembers(isUndo) {
            const form = document.getElementById('form-members');
            const data = {
                region: form.region.value,
                action: form.action.value,
                player: form.player.value,
                dry_run: form.dry_run.checked,
                undo: isUndo
            };
            executeCommand('/api/members', data, 'console-members');
        }
    </script>
</body>
</html>"""

class DashboardRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/datalists":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            result = {
                "regions": get_region_list(),
                "players": PLAYER_LIST
            }
            self.wfile.write(json.dumps(result).encode("utf-8"))
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode("utf-8")) if body else {}
        
        result = {"success": False, "stdout": "", "stderr": "Unknown endpoint"}
        
        if self.path == "/api/sizer":
            cmd = ["resize_plot.py", data.get("region")]
            if data.get("undo"):
                cmd.append("--undo")
            else:
                cmd.append(data.get("category", "normal"))
                if data.get("height"):
                    cmd.extend(["--height", str(data.get("height"))])
            if data.get("dry_run"):
                cmd.append("--dry-run")
            result = run_script(cmd)
            
        elif self.path == "/api/refund":
            cmd = ["refund_upgrade.py", data.get("player"), data.get("type")]
            if data.get("percent"):
                cmd.extend(["--percent", str(data.get("percent"))])
            if data.get("downsize"):
                cmd.extend(["--downsize", data.get("downsize")])
            if data.get("dry_run"):
                cmd.append("--dry-run")
            result = run_script(cmd)
            
        elif self.path == "/api/floor":
            cmd = ["add_region_floor.py", data.get("region")]
            if data.get("undo"):
                cmd.append("--undo")
            else:
                cmd.append(data.get("material", "oak_planks"))
            if data.get("dry_run"):
                cmd.append("--dry-run")
            result = run_script(cmd)
            
        elif self.path == "/api/members":
            cmd = ["manage_region_players.py", data.get("region")]
            if data.get("undo"):
                cmd.append("--undo")
            else:
                cmd.extend([data.get("action"), data.get("player")])
            if data.get("dry_run"):
                cmd.append("--dry-run")
            result = run_script(cmd)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))

def main():
    port = 5001
    server_address = ("", port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print(f"🚀 Dashboard running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")

if __name__ == "__main__":
    main()
