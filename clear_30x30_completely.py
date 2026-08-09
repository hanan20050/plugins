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

cmds = [
    # Clear entire 30x30 area at coordinates (1202, -372) from Y=63 to Y=150
    f"fill {min_x} {cy} {min_z} {max_x} {cy+87} {max_z} minecraft:air",
    # Clear 30x30 area at every online player location
    f"execute at @a run fill ~-14 ~ ~-14 ~15 ~80 ~15 minecraft:air",
    # Kill all dropped item loot
    f"minecraft:kill @e[type=item,x={cx},y=70,z={cz},distance=..40]",
    f"execute at @a run minecraft:kill @e[type=item,distance=..40]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
