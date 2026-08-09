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
min_x, max_x = cx - 7, cx + 7
min_z, max_z = cz - 7, cz + 7

cmds = []

# 1. Grand Center Chandelier under dome center (hanging down from Y=74)
cmds.append(f"setblock {cx} {cy+10} {cz} chain")
cmds.append(f"setblock {cx} {cy+9} {cz} chain")
cmds.append(f"setblock {cx} {cy+8} {cz} sea_lantern")
# Chandelier arms & hanging lanterns
cmds.append(f"setblock {cx-1} {cy+8} {cz} quartz_slab[type=bottom]")
cmds.append(f"setblock {cx+1} {cy+8} {cz} quartz_slab[type=bottom]")
cmds.append(f"setblock {cx} {cy+8} {cz-1} quartz_slab[type=bottom]")
cmds.append(f"setblock {cx} {cy+8} {cz+1} quartz_slab[type=bottom]")

cmds.append(f"setblock {cx-1} {cy+7} {cz} lantern[hanging=true]")
cmds.append(f"setblock {cx+1} {cy+7} {cz} lantern[hanging=true]")
cmds.append(f"setblock {cx} {cy+7} {cz-1} lantern[hanging=true]")
cmds.append(f"setblock {cx} {cy+7} {cz+1} lantern[hanging=true]")

# 2. In-ground Glowstone/Sea Lantern floor lighting accents along prayer hall perimeter
for x in range(cx-4, cx+5, 2):
    cmds.append(f"setblock {x} {cy} {cz-4} sea_lantern")
    cmds.append(f"setblock {x} {cy} {cz+4} sea_lantern")

for z in range(cz-4, cz+5, 2):
    cmds.append(f"setblock {cx-4} {cy} {z} sea_lantern")
    cmds.append(f"setblock {cx+4} {cy} {z} sea_lantern")

# Re-overlay carpets over floor lights where applicable
for x in range(cx-4, cx+5, 2):
    cmds.append(f"setblock {x} {cy+1} {cz-4} cyan_carpet")
    cmds.append(f"setblock {x} {cy+1} {cz+4} cyan_carpet")

# 3. Outdoor Courtyard & Entrance Lantern Posts
cmds.append(f"setblock {cx-2} {cy+1} {max_z-1} end_rod")
cmds.append(f"setblock {cx-2} {cy+2} {max_z-1} lantern[hanging=false]")
cmds.append(f"setblock {cx+2} {cy+1} {max_z-1} end_rod")
cmds.append(f"setblock {cx+2} {cy+2} {max_z-1} lantern[hanging=false]")

cmds.append(f"setblock {cx-2} {cy+1} {min_z+1} end_rod")
cmds.append(f"setblock {cx-2} {cy+2} {min_z+1} lantern[hanging=false]")
cmds.append(f"setblock {cx+2} {cy+1} {min_z+1} end_rod")
cmds.append(f"setblock {cx+2} {cy+2} {min_z+1} lantern[hanging=false]")

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
