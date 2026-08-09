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

cmds = [
    # Remove beacon and platform at 1202, 63-64, -372
    f"fill {cx-5} {cy} {cz-5} {cx+5} {cy+2} {cz+5} minecraft:air",
    # Remove beacon at player location
    "execute at @a run fill ~-5 ~-2 ~-5 ~5 ~2 ~5 minecraft:air",
    # Restore clean grass block floor at Y=62
    f"fill {cx-5} 62 {cz-5} {cx+5} 62 {cz+5} minecraft:grass_block",
    "execute at @a run setblock ~ ~-1 ~ minecraft:grass_block",
    # Kill dropped loot
    f"minecraft:kill @e[type=item,x={cx},y={cy},z={cz},distance=..30]",
    "execute at @a run minecraft:kill @e[type=item,distance=..30]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
