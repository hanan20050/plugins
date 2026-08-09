import os, time, requests
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
# Inside red outline: X [1189, 1216], Z [-385, -358] -> 28x28 usable inner area

cmds = []

# 1. Clear interior space up to Y=230 and clear loot
cmds.append(f"fill 1189 64 -385 1216 230 -358 minecraft:air")
cmds.append(f"minecraft:kill @e[type=item,x={cx},y=100,z={cz},distance=..50]")

# BURJ KHALIFA REALISTIC Y-SHAPED TRI-WING ARCHITECTURE
# 3 Wings: North Wing (Z-), South-East Wing (X+, Z+), South-West Wing (X-, Z+)

# TIER 1: Podium & Full Y-Shape Base (Y=64 to Y=90)
# Center Core 10x10
cmds.append(f"fill {cx-5} {cy+1} {cz-5} {cx+5} {cy+27} {cz+5} light_blue_stained_glass outline")
cmds.append(f"fill {cx-4} {cy+1} {cz-4} {cx+4} {cy+27} {cz+4} smooth_quartz")

# North Wing (X: 1197..1207, Z: -385..-377)
cmds.append(f"fill {cx-4} {cy+1} {cz-13} {cx+4} {cy+27} {cz-6} light_blue_stained_glass outline")
# SE Wing (X: 1203..1214, Z: -370..-360)
cmds.append(f"fill {cx+6} {cy+1} {cz+2} {cx+14} {cy+27} {cz+10} light_blue_stained_glass outline")
# SW Wing (X: 1190..1201, Z: -370..-360)
cmds.append(f"fill {cx-14} {cy+1} {cz+2} {cx-6} {cy+27} {cz+10} light_blue_stained_glass outline")

# Steel & Quartz Structural Accents for Glass Curtain Wall
for y in range(cy+1, cy+28, 4):
    cmds.append(f"fill {cx-4} {y} {cz-13} {cx+4} {y} {cz-13} smooth_quartz_slab")
    cmds.append(f"fill {cx+14} {y} {cz+2} {cx+14} {y} {cz+10} smooth_quartz_slab")
    cmds.append(f"fill {cx-14} {y} {cz+2} {cx-14} {y} {cz+10} smooth_quartz_slab")

# TIER 2: First Setback - Step down SW Wing (Y=91 to Y=115)
cmds.append(f"fill {cx-5} {cy+28} {cz-5} {cx+5} {cy+52} {cz+5} light_blue_stained_glass outline")
cmds.append(f"fill {cx-4} {cy+28} {cz-11} {cx+4} {cy+52} {cz-6} light_blue_stained_glass outline") # North Wing shortened
cmds.append(f"fill {cx+6} {cy+28} {cz+2} {cx+12} {cy+52} {cz+8} light_blue_stained_glass outline")  # SE Wing shortened
cmds.append(f"fill {cx-10} {cy+28} {cz+2} {cx-6} {cy+52} {cz+6} light_blue_stained_glass outline")  # SW Wing set back

# TIER 3: Second Setback - Step down SE Wing (Y=116 to Y=140)
cmds.append(f"fill {cx-4} {cy+53} {cz-4} {cx+4} {cy+77} {cz+4} light_blue_stained_glass outline")
cmds.append(f"fill {cx-3} {cy+53} {cz-9} {cx+3} {cy+77} {cz-5} light_blue_stained_glass outline") # North Wing further shortened
cmds.append(f"fill {cx+5} {cy+53} {cz+1} {cx+8} {cy+77} {cz+5} light_blue_stained_glass outline")  # SE Wing set back

# TIER 4: Third Setback - Step down North Wing & Tapering Core (Y=141 to Y=165)
cmds.append(f"fill {cx-3} {cy+78} {cz-3} {cx+3} {cy+102} {cz+3} light_blue_stained_glass outline")
cmds.append(f"fill {cx-2} {cy+78} {cz-6} {cx+2} {cy+102} {cz-4} light_blue_stained_glass outline") # North Wing cap

# TIER 5: Upper Central Hexagonal Core (Y=166 to Y=185)
cmds.append(f"fill {cx-2} {cy+103} {cz-2} {cx+2} {cy+122} {cz+2} cyan_stained_glass outline")
cmds.append(f"fill {cx-1} {cy+103} {cz-1} {cx+1} {cy+122} {cz+1} smooth_quartz")

# TIER 6: Pinnacle Spire Shaft (Y=186 to Y=210)
cmds.append(f"fill {cx-1} {cy+123} {cz-1} {cx+1} {cy+147} {cz+1} iron_block")
cmds.append(f"setblock {cx} {cy+135} {cz} sea_lantern")

# TIER 7: Stainless Steel Spire Antenna & Beacon (Y=211 to Y=222)
cmds.append(f"fill {cx} {cy+148} {cz} {cx} {cy+158} {cz} end_rod")
cmds.append(f"setblock {cx} {cy+159} {cz} beacon")

# Illumination Sea Lanterns inside core
for y_lit in range(cy+10, cy+180, 20):
    cmds.append(f"setblock {cx} {y_lit} {cz} sea_lantern")

# Final item loot cleanup
cmds.append(f"minecraft:kill @e[type=item,x={cx},y=120,z={cz},distance=..60]")

print(f"Total commands to execute: {len(cmds)}")

success_count = 0
for i, cmd in enumerate(cmds):
    status, text = send_cmd(cmd)
    if status == 200:
        success_count += 1
    else:
        print(f"Error on cmd #{i}: {cmd} -> Status {status}")
    time.sleep(0.04)

print(f"Finished building Burj Khalifa! Successfully executed {success_count}/{len(cmds)} commands.")
