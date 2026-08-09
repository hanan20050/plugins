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
hz_max = cz + 5  # -367

# Fill wall frame around entrance to close open gaps cleanly
cmds = [
    # Frame sides
    f"fill {cx-2} {cy+1} {hz_max} {cx-2} {cy+5} {hz_max} quartz_block",
    f"fill {cx+2} {cy+1} {hz_max} {cx+2} {cy+5} {hz_max} quartz_block",
    # Arch above double door
    f"fill {cx-1} {cy+3} {hz_max} {cx+1} {cy+5} {hz_max} chiseled_quartz_block",
    f"setblock {cx} {cy+3} {hz_max} sea_lantern",
    # Double Birch Doors (2-block wide entrance)
    f"setblock {cx-1} {cy+1} {hz_max} dark_oak_door[half=lower,hinge=left,facing=south]",
    f"setblock {cx-1} {cy+2} {hz_max} dark_oak_door[half=upper,hinge=left,facing=south]",
    f"setblock {cx} {cy+1} {hz_max} dark_oak_door[half=right,hinge=right,facing=south]",
    f"setblock {cx} {cy+2} {hz_max} dark_oak_door[half=right,hinge=right,facing=south]",
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
