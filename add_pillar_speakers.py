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
hx_min, hx_max = cx - 5, cx + 5
hz_min, hz_max = cz - 5, cz + 5

# Corner Pillars are at (hx_min, hz_min), (hx_max, hz_min), (hx_min, hz_max), (hx_max, hz_max)
# Place Jukebox speakers facing inward/towards prayer hall at Y = cy + 6 (height 69)
# Also add speakers to top of minarets at Y = 78
cmds = [
    # Interior Pillar Speakers (Jukeboxes on pillars pointing into the hall)
    f"setblock {hx_min+1} {cy+6} {hz_min+1} jukebox",
    f"setblock {hx_max-1} {cy+6} {hz_min+1} jukebox",
    f"setblock {hx_min+1} {cy+6} {hz_max-1} jukebox",
    f"setblock {hx_max-1} {cy+6} {hz_max-1} jukebox",
    
    # Outer Minaret Horn Speakers (Note Blocks / Jukeboxes on Minaret balconies Y=78)
    f"setblock {cx-6} {cy+15} {cz-6} note_block",
    f"setblock {cx+6} {cy+15} {cz-6} note_block",
    f"setblock {cx-6} {cy+15} {cz+6} note_block",
    f"setblock {cx+6} {cy+15} {cz+6} note_block",
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
