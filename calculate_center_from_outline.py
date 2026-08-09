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

# Outline boundaries: X [1188, 1217], Z [-386, -357] -> 30x30 blocks
# Exact mathematical center formula:
# min_x + (max_x - min_x) // 2 = 1188 + (1217 - 1188) // 2 = 1188 + 14 = 1202
# min_z + (max_z - min_z) // 2 = -386 + (-357 - (-386)) // 2 = -386 + 14 = -372
# Center point = (1202, 63, -372)

cx, cy, cz = 1202, 63, -372

tellraw_cmd = 'execute as @a run tellraw @s [{"text":"[Center Found] Calculated Center of 30x30 Red Outline: X=1202, Y=63, Z=-372 (Marked with Gold Block & Beacon)","color":"yellow","bold":true}]'

cmds = [
    f"fill 1188 63 -386 1217 63 -357 red_concrete outline",
    f"fill 1189 63 -385 1216 63 -358 grass_block",
    f"setblock {cx} {cy} {cz} gold_block",
    f"setblock {cx} {cy+1} {cz} beacon",
    tellraw_cmd
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
