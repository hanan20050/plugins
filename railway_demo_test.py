#!/usr/bin/env python3
"""
Railway Worker Connectivity & Message Test Script
Sends 3 demo broadcast messages via Exaroton API to confirm Railway background container activity.
"""

import os
import sys
import json
import time
import subprocess

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

def get_token():
    return os.environ.get("EXAROTON_TOKEN") or HARDCODED_TOKEN

def get_server_id():
    return os.environ.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

def send_exaroton_command(cmd):
    token = get_token()
    server_id = get_server_id()
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            print(f"✅ Console Executed: {cmd}")
            return True
        else:
            print(f"❌ Command Error: {data.get('error')} | Output: {res.stdout}")
            return False
    except Exception:
        print(f"Response: {res.stdout}")
        return False

# Flag file so demo messages run only once per container startup
TEST_STATE_FILE = "/tmp/railway_demo_sent.flag"

def send_demo_messages():
    if os.path.exists(TEST_STATE_FILE):
        return

    print("🚀 Sending 3 Demo Test Broadcast Messages from Railway Container...")

    messages = [
        [{"text": "[RAILWAY DEMO 1/3] ", "color": "green", "bold": True}, {"text": "🚀 Railway Worker Container is ONLINE and connected!", "color": "yellow"}],
        [{"text": "[RAILWAY DEMO 2/3] ", "color": "green", "bold": True}, {"text": "⚡ Polling interval: 10 seconds | Monitoring active!", "color": "aqua"}],
        [{"text": "[RAILWAY DEMO 3/3] ", "color": "green", "bold": True}, {"text": "✅ Anti-Exploit Trade System is ready to catch exploits!", "color": "gold"}]
    ]

    for idx, msg in enumerate(messages, 1):
        tellraw_cmd = f'tellraw @a {json.dumps(msg)}'
        send_exaroton_command(tellraw_cmd)
        time.sleep(2)

    with open(TEST_STATE_FILE, "w") as f:
        f.write("sent")

if __name__ == "__main__":
    send_demo_messages()
