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
min_x, max_x = cx - 25, cx + 25  # 1177 to 1227
min_z, max_z = cz - 25, cz + 25  # -397 to -347

cmds = [
    # 1. Fill wide 50x50 area from Y=50 up to Y=160 with air
    f"fill {min_x} 50 {min_z} {max_x} 160 {max_z} air",
    # 2. Restore ground layer at Y=62 with grass_block so ground is clean
    f"fill {min_x} 62 {min_z} {max_x} 62 {max_z} grass_block",
    # 3. Kill all dropped item loot in wide 60-block radius
    f"minecraft:kill @e[type=item,x={cx},y=70,z={cz},distance=..60]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
