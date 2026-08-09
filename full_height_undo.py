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
min_x, max_x = cx - 20, cx + 20
min_z, max_z = cz - 20, cz + 20

cmds = [
    # Clear full height from Y=63 up to sky limit Y=319 across entire 40x40 area
    f"fill {min_x} 63 {min_z} {max_x} 190 {max_z} minecraft:air",
    f"fill {min_x} 191 {min_z} {max_x} 319 {max_z} minecraft:air",
    
    # Restore clean grass block floor at Y=62
    f"fill {min_x} 62 {min_z} {max_x} 62 {max_z} minecraft:grass_block",

    # Kill all dropped item loot across full vertical height column
    f"minecraft:kill @e[type=item,x={cx},y=120,z={cz},distance=..60]",
    f"execute at @a run minecraft:kill @e[type=item,distance=..60]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
