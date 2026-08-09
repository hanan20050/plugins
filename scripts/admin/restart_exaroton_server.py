#!/usr/bin/env python3
import os
import json
import subprocess

def load_env():
    token, server_id = None, None
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.startswith("EXAROTON_TOKEN="):
                    token = line.strip().split("=", 1)[1].strip("'\"")
                elif line.startswith("EXAROTON_SERVER_ID="):
                    server_id = line.strip().split("=", 1)[1].strip("'\"")
    return token, server_id

def restart_server():
    token, server_id = load_env()
    url = f"https://api.exaroton.com/v1/servers/{server_id}/restart/"
    
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json"
    ]
    
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    print("Restart API Response:", res.stdout)
    return res.stdout

if __name__ == "__main__":
    restart_server()
