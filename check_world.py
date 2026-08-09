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

# Execute vanilla fill in world dimension explicitly & place beacon indicator
print("Executing explicit world fill and marker...")
send_cmd(f"execute in minecraft:overworld run fill 1187 63 -387 1217 120 -357 minecraft:air")
send_cmd(f"execute in minecraft:overworld run setblock {cx} 63 {cz} minecraft:gold_block")
send_cmd(f"execute in minecraft:overworld run setblock {cx} 64 {cz} minecraft:beacon")
send_cmd(f"execute in minecraft:overworld run minecraft:kill @e[type=item,x={cx},y=63,z={cz},distance=..60]")

