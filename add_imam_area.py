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
hz_min = cz - 5  # -377 (North Wall)

cmds = [
    # 1. Expand Mihrab Niche (Center North Wall)
    f"fill {cx-1} {cy+1} {hz_min} {cx+1} {cy+4} {hz_min} chiseled_quartz_block",
    f"fill {cx} {cy+1} {hz_min} {cx} {cy+3} {hz_min} air",  # Niche recess
    f"setblock {cx} {cy+1} {hz_min} gold_block",
    f"setblock {cx} {cy+2} {hz_min} sea_lantern",
    f"setblock {cx} {cy+3} {hz_min} smooth_quartz_stairs[facing=south,half=top]",

    # 2. Imam's Prayer Rug in front of Mihrab
    f"setblock {cx} {cy+1} {hz_min+1} gold_block",
    f"setblock {cx} {cy+1} {hz_min+2} red_carpet",
    f"setblock {cx-1} {cy+1} {hz_min+2} yellow_carpet",
    f"setblock {cx+1} {cy+1} {hz_min+2} yellow_carpet",

    # 3. Minbar (Imam's Pulpit/Staircase to the right / East side of Mihrab)
    f"setblock {cx+2} {cy+1} {hz_min+1} quartz_stairs[facing=south]",
    f"setblock {cx+2} {cy+2} {hz_min} quartz_stairs[facing=south]",
    f"setblock {cx+2} {cy+3} {hz_min} quartz_block",
    f"setblock {cx+2} {cy+4} {hz_min} lantern[hanging=false]",

    # 4. Quran Stand (Lectern) for the Imam
    f"setblock {cx-2} {cy+1} {hz_min+1} lectern[facing=south]",
    f"setblock {cx-2} {cy+2} {hz_min+1} lantern[hanging=false]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
