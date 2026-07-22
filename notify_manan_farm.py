#!/usr/bin/env python3
"""
24/7 Manan Join Notifier
-----------------------
Monitors Exaroton server player online status. Whenever Manan (manansaleh2007 or .manansaleh2007)
joins the server, it sends a personalized in-game message informing him that his farm is fixed and working now.

Supports:
- 24/7 background execution / loop mode (for GitHub Actions cron or local daemon)
- Session state tracking (only notifies on join event to avoid spam)
"""

import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
STATE_FILE = os.path.join(SCRIPT_DIR, "manan_notify_state.json")

# Load environment variables
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")

MANAN_USERNAMES = ["manansaleh2007", ".manansaleh2007"]

def send_exaroton_command(cmd):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        return data.get("success", False)
    except Exception:
        return False

def fetch_online_players():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-H", f"Authorization: Bearer {TOKEN}",
        url
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            players_info = data.get("data", {}).get("players", {})
            return [p.lower() for p in players_info.get("list", [])]
    except Exception as e:
        print(f"Error fetching online players: {e}")
    return []

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"manan_was_online": False, "notifications_sent": 0}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")

def notify_manan(player_name):
    print(f"🔔 Manan ({player_name}) joined! Sending in-game notification...")
    
    # Send styled tellraw chat message to Manan
    msg_json = json.dumps([
        "",
        {"text": "[Server Notification] ", "color": "gold", "bold": True},
        {"text": f"Hey Manan! Your farm region has been fixed. You can now build and use your farm!", "color": "green", "bold": True}
    ])
    
    tellraw_cmd = f"tellraw {player_name} {msg_json}"
    msg_cmd = f"msg {player_name} [Server] Your farm region is fixed and working now!"
    
    send_exaroton_command(tellraw_cmd)
    send_exaroton_command(msg_cmd)

def check_and_notify():
    state = load_state()
    online_players = fetch_online_players()
    
    is_manan_online = any(u.lower() in online_players for u in MANAN_USERNAMES)
    manan_username = next((u for u in MANAN_USERNAMES if u.lower() in online_players), "manansaleh2007")

    # Detect join event: was not online before, now online
    if is_manan_online and not state.get("manan_was_online", False):
        notify_manan(manan_username)
        state["manan_was_online"] = True
        state["notifications_sent"] = state.get("notifications_sent", 0) + 1
        state["last_notified"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save_state(state)
    elif not is_manan_online and state.get("manan_was_online", False):
        # Reset online state when he disconnects so he gets notified next time he joins
        print("Manan went offline. Resetting join notification trigger.")
        state["manan_was_online"] = False
        save_state(state)

def main():
    loop_mode = "--loop" in sys.argv or os.environ.get("LOOP_MODE", "").lower() == "true"
    duration = int(os.environ.get("LOOP_DURATION", "270"))
    interval = int(os.environ.get("POLL_INTERVAL", "3"))

    print(f"Starting Manan Join Notifier (Loop Mode: {loop_mode})...")
    
    start_time = time.time()
    while True:
        check_and_notify()
        if not loop_mode:
            break
        if time.time() - start_time >= duration:
            print("Loop duration reached.")
            break
        time.sleep(interval)

if __name__ == "__main__":
    main()
