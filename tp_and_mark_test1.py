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

cx, cy, cz = 1202, 64, -372

# 1. Teleport player to region test1 center
send_cmd("execute as @a run tp @s 1202 64 -372")
# 2. Place bright Diamond Block platform & Beacon at test1 center
send_cmd("fill 1198 63 -376 1206 63 -368 minecraft:diamond_block")
send_cmd("setblock 1202 64 -372 minecraft:beacon")
send_cmd("execute as @a run tellraw @s [{\"text\":\"[System] Teleported you directly to region test1 center! (Diamond Block & Beacon)\",\"color\":\"aqua\",\"bold\":true}]")

