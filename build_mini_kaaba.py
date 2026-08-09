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

# Mini Kaaba (5x5x5 cube) centered at (1202, 63, -372)
# X: [1200, 1204], Z: [-374, -370], Y: [63, 67]
kx_min, kx_max = cx - 2, cx + 2
kz_min, kz_max = cz - 2, cz + 2

cmds = [
    # 1. Base Marble Courtyard Floor (11x11 smooth quartz)
    f"fill {cx-5} {cy} {cz-5} {cx+5} {cy} {cz+5} smooth_quartz",
    
    # 2. Kaaba Main Black Cube Body (5x5x5 Black Concrete / Obsidian)
    f"fill {kx_min} {cy+1} {kz_min} {kx_max} {cy+5} {kz_max} black_concrete",
    
    # 3. Golden Kiswah Trim (Gold Blocks around top edge at Y = 67)
    f"fill {kx_min} {cy+5} {kz_min} {kx_max} {cy+5} {kz_max} gold_block outline",
    
    # 4. Golden Door (Bab al-Kaaba on East side / facing East X max)
    f"setblock {kx_max} {cy+2} {cz} gold_block",
    f"setblock {kx_max} {cy+3} {cz} gold_block",
    f"setblock {kx_max+1} {cy+2} {cz} gold_block",
    
    # 5. Hajar al-Aswad (Black Stone in Silver/Quartz Casing at SE Corner)
    f"setblock {kx_max} {cy+2} {kz_max} lodestone",
    
    # 6. Roof accent (Black Concrete powder / Slabs)
    f"fill {kx_min+1} {cy+5} {kz_min+1} {kx_max-1} {cy+5} {kz_max-1} black_concrete",
    
    # 7. Maqam Ibrahim accent in Courtyard (Glass & Gold enclosure)
    f"setblock {cx+4} {cy+1} {cz+1} gold_block",
    f"setblock {cx+4} {cy+2} {cz+1} glass"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
