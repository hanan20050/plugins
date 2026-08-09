import os
import sys
import json
import time
import subprocess
import urllib.request

TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = "cEuS61sZvNEFS3aB"

def send_command(cmd):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    subprocess.run(curl_cmd, capture_output=True)

def get_logs():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "GET", url,
        "-H", f"Authorization: Bearer {TOKEN}"
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            return data.get("data", {}).get("content", "")
    except Exception:
        pass
    return ""

def main():
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "lp group default permission info"
    print(f"Sending command: {cmd}")
    send_command(cmd)
    
    print("Waiting 3 seconds for log update...")
    time.sleep(3)
    
    logs = get_logs()
    lines = logs.split("\n")
    
    # Find the output of the command
    print("--- Console Output ---")
    found_output = False
    for line in lines[-50:]:
        if "[luckperms-command-executor/INFO]" in line or "[LP]" in line:
            print(line)
            found_output = True
    if not found_output:
        print("No LuckPerms output found in recent logs. Last 10 lines of console:")
        for line in lines[-10:]:
            print(line)

if __name__ == "__main__":
    main()
