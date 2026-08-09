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
# Region test1 bounds: X [1188, 1217], Z [-386, -357], Y [63, 313]
min_x, max_x = 1188, 1217
min_z, max_z = -386, -357

# Split into fill chunks due to block volume limit
cmds = [
    f"fill {min_x} 63 {min_z} {max_x} 150 {max_z} minecraft:air",
    f"fill {min_x} 151 {min_z} {max_x} 235 {max_z} minecraft:air",
    f"fill {min_x} 236 {min_z} {max_x} 319 {max_z} minecraft:air",
    f"minecraft:kill @e[type=item,x={cx},y=120,z={cz},distance=..60]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
