#!/usr/bin/env python3
"""
Server Restart Chat Listener
Polls latest server logs for any player typing 'yes' in chat.
When detected, broadcasts a 10s restart warning and triggers Exaroton restart.
"""

import urllib.request
import json
import time
import os

TOKEN = os.environ.get("EXAROTON_TOKEN", "")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID", "")

if not TOKEN or not SERVER_ID:
    with open(".env") as f:
        for line in f:
            if line.startswith("EXAROTON_TOKEN="): TOKEN = line.strip().split("=", 1)[1]
            if line.startswith("EXAROTON_SERVER_ID="): SERVER_ID = line.strip().split("=", 1)[1]

def send_cmd(cmd):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    req = urllib.request.Request(
        url,
        data=json.dumps({"command": cmd}).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status

def restart_server():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/restart/"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "Mozilla/5.0"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status

def get_logs():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs/"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        return data["data"]["content"].split("\n")

print("Listening for player 'yes' response in server logs...")
start_time = time.time()
while time.time() - start_time < 300:  # Timeout after 5 minutes
    try:
        lines = get_logs()
        for line in lines[-15:]:
            # Check if line is a chat line containing 'yes'
            # Typical chat formats: [Async Chat Thread/INFO]: <Player> yes or <.Player> yes
            if "CHAT" in line.upper() or ">" in line or ":" in line:
                msg_part = line.split(":", 3)[-1].strip().lower() if line.count(":") >= 3 else line.lower()
                if msg_part == "yes" or msg_part.endswith(" yes") or msg_part.startswith("yes "):
                    print("Detected 'yes' vote in chat line:", line)
                    send_cmd('tellraw @a [{"text":"[SERVER RESTART] Vote confirmed! Server restarting in 10 seconds...","color":"green","bold":true}]')
                    time.sleep(10)
                    restart_server()
                    print("Server restart initiated!")
                    exit(0)
    except Exception as e:
        print("Error checking logs:", e)
    time.sleep(3)

print("Poll timed out after 5 minutes without a 'yes' vote.")
