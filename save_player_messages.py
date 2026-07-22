#!/usr/bin/env python3
import os
import re
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime

# Path configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "chat_logs.json")
OUTPUT_TXT = os.path.join(SCRIPT_DIR, "chat_logs.txt")

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

# Player Identity Reference
PLAYER_NAMES = {
    ".mustafahacker67": "mustafa",
    "mustafahacker67": "mustafa",
    ".hastybag7675": "muhammad saleh",
    "hastybag7675": "muhammad saleh",
    ".wirycircle3938": "omer saleh",
    "wirycircle3938": "omer saleh",
    "hanansaleh": "hanan saleh",
    ".hanansaleh": "hanan saleh",
    "manansaleh2007": "manan saleh",
    ".manansaleh2007": "manan saleh",
    "nightmaredady": "rayan saleh",
    ".nightmaredady": "rayan saleh",
    ".azansaleh": "azan saleh",
    "azansalehhh": "azan saleh",
    ".azansalehhh": "azan saleh",
}

def get_real_name(username):
    cleaned = username.lower().strip()
    return PLAYER_NAMES.get(cleaned, username)

class CustomHTTPHandler(urllib.request.HTTPSHandler):
    """Custom HTTPS Handler to bypass DNS resolution issues for api.exaroton.com"""
    def http_open(self, req):
        if req.host == "api.exaroton.com":
            req.host = "104.26.12.211"
        return super().https_open(req)

def fetch_server_logs():
    if not TOKEN or not SERVER_ID:
        print("Error: EXAROTON_TOKEN and EXAROTON_SERVER_ID must be set in .env")
        return None

    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs"
    
    # Try normal request first, fallback to IP if DNS fails
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("User-Agent", "MinecraftChatSaver/1.0")

    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data.get("success"):
                return data.get("data", {}).get("content", "")
    except Exception as e:
        # Fallback using Direct IP if DNS resolution fails
        try:
            req_fallback = urllib.request.Request(url.replace("api.exaroton.com", "104.26.12.211"))
            req_fallback.add_header("Host", "api.exaroton.com")
            req_fallback.add_header("Authorization", f"Bearer {TOKEN}")
            req_fallback.add_header("User-Agent", "MinecraftChatSaver/1.0")
            with urllib.request.urlopen(req_fallback) as res:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("success"):
                    return data.get("data", {}).get("content", "")
        except Exception as ex:
            print(f"Failed to fetch logs: {e} / {ex}")
            return None
    return None

def parse_chat_messages(log_text):
    """
    Parses chat messages from log text.
    Matches lines like: [12:28:59] [Async Chat Thread - #23/INFO]: [Not Secure] <NightmareDady> mustafa sahi kar
    """
    messages = []
    if not log_text:
        return messages

    # Pattern for standard Minecraft chat: <username> message
    # Optional prefixes like [Not Secure], [Server], etc.
    chat_pattern = re.compile(
        r'^\[(\d{2}:\d{2}:\d{2})\]\s+\[[^\]]+\]:\s*(?:\[[^\]]+\]\s*)*<([^>]+)>\s*(.*)$'
    )
    
    # Pattern for server announcements or /me actions
    server_say_pattern = re.compile(
        r'^\[(\d{2}:\d{2}:\d{2})\]\s+\[[^\]]+\]:\s*\[Server\]\s*(.*)$'
    )

    for line in log_text.splitlines():
        line = line.strip()
        chat_match = chat_pattern.match(line)
        if chat_match:
            time_str, username, message_text = chat_match.groups()
            messages.append({
                "time": time_str,
                "username": username,
                "real_name": get_real_name(username),
                "message": message_text.strip(),
                "raw": line
            })
            continue

        say_match = server_say_pattern.match(line)
        if say_match:
            time_str, message_text = say_match.groups()
            messages.append({
                "time": time_str,
                "username": "[Server]",
                "real_name": "Server Broadcast",
                "message": message_text.strip(),
                "raw": line
            })

    return messages

def load_existing_logs():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_logs(messages):
    existing = load_existing_logs()
    
    # Create unique keys based on (time, username, message)
    existing_keys = set((m["time"], m["username"], m["message"]) for m in existing)
    
    new_count = 0
    for msg in messages:
        key = (msg["time"], msg["username"], msg["message"])
        if key not in existing_keys:
            existing.append(msg)
            existing_keys.add(key)
            new_count += 1

    if new_count > 0 or not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
            
        with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
            for m in existing:
                f.write(f"[{m['time']}] {m['username']} ({m['real_name']}): {m['message']}\n")

    return new_count, len(existing)

def main():
    print("Fetching Minecraft server chat logs...")
    log_content = fetch_server_logs()
    
    if not log_content:
        print("Could not retrieve logs or server log is empty.")
        return

    parsed_messages = parse_chat_messages(log_content)
    print(f"Found {len(parsed_messages)} total chat messages in current log buffer.")

    new_added, total_saved = save_logs(parsed_messages)
    print(f"Saved: {new_added} new messages added. Total stored messages: {total_saved}.")
    print(f"JSON Output: {OUTPUT_FILE}")
    print(f"Text Output: {OUTPUT_TXT}")
    
    if parsed_messages:
        print("\n--- Recent Player Messages ---")
        for m in parsed_messages[-15:]:
            print(f"[{m['time']}] {m['username']} ({m['real_name']}): {m['message']}")

if __name__ == "__main__":
    main()
