#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")

def send_private_message(player_name, message):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    cmd = f"msg {player_name} {message}"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    return res.stdout

def main():
    player_name = "hanansaleh"
    total_messages = 25
    interval = 2

    print(f"🚀 [Railway Demo] Sending message to {player_name} {total_messages} times (every {interval}s)...")
    for i in range(1, total_messages + 1):
        msg_text = f"§6[Railway Worker Test] §eMessage {i}/{total_messages}: §btesting 24/7 on Railway!"
        res = send_private_message(player_name, msg_text)
        print(f"[{i}/{total_messages}] Sent to {player_name} -> Response: {res.strip()}")
        if i < total_messages:
            time.sleep(interval)

    print("🎉 Railway demo test completed!")

if __name__ == "__main__":
    main()
