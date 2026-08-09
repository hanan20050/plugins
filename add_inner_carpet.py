import os, requests
from urllib3.util import connection

_orig_create_connection = connection.create_connection
def patched_create_connection(address, *args, **kwargs):
    host, port = address
    if host == "api.exaroton.com":
        host = "104.26.12.211"
    return _orig_create_connection((host, port), *args, **kwargs)

connection.create_connection = patched_create_connection

token = None
server_id = None
with open('/Users/hanansaleh/Documents/GitHub/plugins/.env') as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            if k.strip() == 'EXAROTON_TOKEN': token = v.strip()
            elif k.strip() == 'EXAROTON_SERVER_ID': server_id = v.strip()

def send_cmd(cmd):
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json={"command": cmd})
    return r.status_code, r.text

cx, cy, cz = 1202, 63, -372
hx_min, hx_max = cx - 4, cx + 4  # 1198 to 1206
hz_min, hz_max = cz - 4, cz + 4  # -376 to -368

# Carpet layer at Y = 64 (cy + 1) inside prayer hall
cmds = [
    # Full cyan carpet for interior floor
    f"fill {hx_min} {cy+1} {hz_min} {hx_max} {cy+1} {hz_max} cyan_carpet",
    # Red carpet prayer mat pathways/rows pattern inside
    f"fill {hx_min+1} {cy+1} {hz_min+1} {hx_max-1} {cy+1} {hz_min+1} red_carpet",
    f"fill {hx_min+1} {cy+1} {hz_min+3} {hx_max-1} {cy+1} {hz_min+3} red_carpet",
    f"fill {hx_min+1} {cy+1} {hz_min+5} {hx_max-1} {cy+1} {hz_min+5} red_carpet",
    # Yellow accent around central prayer area
    f"fill {cx-1} {cy+1} {cz-1} {cx+1} {cy+1} {cz+1} yellow_carpet",
    f"setblock {cx} {cy+1} {cz} gold_block"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
