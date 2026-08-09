import os, sys, requests, time

# Fetch env vars
token = None
server_id = None

with open('/Users/hanansaleh/Documents/GitHub/plugins/.env') as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            if k == 'EXAROTON_TOKEN': token = v
            elif k == 'EXAROTON_SERVER_ID': server_id = v

def send_cmd(cmd):
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Using --resolve or direct request handling if needed
    resp = requests.post(url, headers=headers, json={"command": cmd})
    return resp.status_code

print("Script template ready")
