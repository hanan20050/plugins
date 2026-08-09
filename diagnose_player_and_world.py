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

print("Getting player dimensions & exact locations...")
send_cmd("execute as @a run data get entity @s Dimension")
send_cmd("execute as @a run data get entity @s Pos")

# Place glowing beacons directly in front of all online players
send_cmd("execute at @a run fill ~-2 ~-1 ~-2 ~2 ~-1 ~2 minecraft:red_concrete")
send_cmd("execute at @a run setblock ~ ~ ~ minecraft:beacon")

