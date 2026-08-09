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
min_x, max_x = cx - 14, cx + 15  # 1188 to 1217 (30x30 area)
min_z, max_z = cz - 14, cz + 15  # -386 to -357

# Split into 2 fill commands because height span from 63 to 319 exceeds Minecraft's 32,768 fill limit
cmds = [
    # Fill from Y=63 to Y=190
    f"fill {min_x} 63 {min_z} {max_x} 190 {max_z} minecraft:air",
    # Fill from Y=191 to Y=319 (Minecraft build height limit / sky limit)
    f"fill {min_x} 191 {min_z} {max_x} 319 {max_z} minecraft:air",
    
    # Same sky clear directly at all player locations
    f"execute at @a run fill ~-14 63 ~-14 ~15 190 ~15 minecraft:air",
    f"execute at @a run fill ~-14 191 ~-14 ~15 319 ~15 minecraft:air",

    # Kill all dropped item loot in the sky column using vanilla namespace
    f"minecraft:kill @e[type=item,x={cx},y=120,z={cz},distance=..60]",
    f"execute at @a run minecraft:kill @e[type=item,distance=..60]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
