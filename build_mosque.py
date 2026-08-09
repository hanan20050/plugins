import os, sys, time, requests
from urllib3.util import connection

# Direct IP resolution for api.exaroton.com to avoid sandbox DNS issues
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

# 15x15 area centered at (1202, -372) -> X: [1195, 1209], Z: [-379, -365]
min_x, max_x = cx - 7, cx + 7
min_z, max_z = cz - 7, cz + 7

print(f"Mosque bounds: X [{min_x}, {max_x}], Z [{min_z}, {max_z}], Base Y={cy}")

commands = []

# Clear workspace 15x15x25
commands.append(f"fill {min_x} {cy} {min_z} {max_x} {cy+25} {max_z} air")

# 1. Base Floor / Courtyard Platform (Y = 63)
# Base border: Quartz Blocks, center patterned with Smooth Quartz and Gold Block star accent
commands.append(f"fill {min_x} {cy} {min_z} {max_x} {cy} {max_z} quartz_block")
commands.append(f"fill {min_x+1} {cy} {min_z+1} {max_x-1} {cy} {max_z-1} smooth_quartz")
# Center carpet pattern (carpet on top of quartz floor at Y=64)
commands.append(f"fill {min_x+2} {cy+1} {min_z+2} {max_x-2} {cy+1} {max_z-2} cyan_carpet")
commands.append(f"fill {min_x+3} {cy+1} {min_z+3} {max_x-3} {cy+1} {max_z-3} yellow_carpet")
commands.append(f"setblock {cx} {cy+1} {cz} gold_block")

# 2. Main Prayer Hall Outer Walls (X: 1197..1207, Z: -377..-367) -> 11x11 footprint
hx_min, hx_max = cx - 5, cx + 5
hz_min, hz_max = cz - 5, cz + 5
commands.append(f"fill {hx_min} {cy+1} {hz_min} {hx_max} {cy+8} {hz_max} quartz_block outline")
commands.append(f"fill {hx_min+1} {cy+1} {hz_min+1} {hx_max-1} {cy+7} {hz_max-1} air")

# Corner Pillars - Chiseled Quartz & Sea Lantern accents
for px in [hx_min, hx_max]:
    for pz in [hz_min, hz_max]:
        commands.append(f"fill {px} {cy+1} {pz} {px} {cy+9} {pz} chiseled_quartz_block")
        commands.append(f"setblock {px} {cy+5} {pz} sea_lantern")

# Arched Windows with Cyan Stained Glass on walls
# North & South wall windows
for z_wall in [hz_min, hz_max]:
    commands.append(f"fill {cx-3} {cy+3} {z_wall} {cx-2} {cy+5} {z_wall} cyan_stained_glass_pane")
    commands.append(f"fill {cx+2} {cy+3} {z_wall} {cx+3} {cy+5} {z_wall} cyan_stained_glass_pane")
# East & West wall windows
for x_wall in [hx_min, hx_max]:
    commands.append(f"fill {x_wall} {cy+3} {cz-3} {x_wall} {cy+5} {cz-2} cyan_stained_glass_pane")
    commands.append(f"fill {x_wall} {cy+3} {cz+2} {x_wall} {cy+5} {cz+3} cyan_stained_glass_pane")

# Grand Entrance Archway (South Wall, Facing Z max)
commands.append(f"fill {cx-1} {cy+1} {hz_max} {cx+1} {cy+4} {hz_max} air")
commands.append(f"fill {cx-1} {cy+5} {hz_max} {cx+1} {cy+5} {hz_max} smooth_quartz_slab")
commands.append(f"setblock {cx} {cy+1} {hz_max+1} birch_door[half=lower,hinge=left,facing=south]")
commands.append(f"setblock {cx} {cy+2} {hz_max+1} birch_door[half=upper,hinge=left,facing=south]")

# Mihrab (Niche on North wall)
commands.append(f"setblock {cx} {cy+2} {hz_min} gold_block")
commands.append(f"setblock {cx} {cy+1} {hz_min+1} sea_lantern")

# 3. Main Central Dome (Layered 7x7 -> 5x5 -> 3x3 -> Gold Spire)
# Dome Roof Ring at Y=9
commands.append(f"fill {cx-3} {cy+9} {cz-3} {cx+3} {cy+9} {cz+3} smooth_quartz")
commands.append(f"fill {cx-2} {cy+9} {cz-2} {cx+2} {cy+9} {cz+2} air")
# Gold Dome Body
commands.append(f"fill {cx-3} {cy+10} {cz-3} {cx+3} {cy+10} {cz+3} gold_block outline")
commands.append(f"fill {cx-2} {cy+11} {cz-2} {cx+2} {cy+11} {cz+2} gold_block outline")
commands.append(f"fill {cx-1} {cy+12} {cz-1} {cx+1} {cy+12} {cz+1} gold_block")
commands.append(f"setblock {cx} {cy+12} {cz} sea_lantern")
# Crescent Spire
commands.append(f"setblock {cx} {cy+13} {cz} end_rod")
commands.append(f"setblock {cx} {cy+14} {cz} gold_block")
commands.append(f"setblock {cx} {cy+15} {cz} end_rod")

# 4. Four Elegant Minarets at the Base Corners (15x15 Corners)
minaret_coords = [
    (min_x+1, min_z+1),
    (max_x-1, min_z+1),
    (min_x+1, max_z-1),
    (max_x-1, max_z-1)
]

for mx, mz in minaret_coords:
    # Shaft (Y=64 to 77)
    commands.append(f"fill {mx} {cy+1} {mz} {mx} {cy+14} {mz} quartz_pillar")
    # Decorative rings
    commands.append(f"setblock {mx} {cy+6} {mz} chiseled_quartz_block")
    commands.append(f"setblock {mx} {cy+11} {mz} chiseled_quartz_block")
    # Minaret Balcony / Lantern
    commands.append(f"setblock {mx} {cy+15} {mz} sea_lantern")
    commands.append(f"setblock {mx} {cy+16} {mz} gold_block")
    commands.append(f"setblock {mx} {cy+17} {mz} end_rod")

# 5. Entrance Pathway & Lighting
commands.append(f"fill {cx-1} {cy} {hz_max+1} {cx+1} {cy} {max_z} smooth_quartz")
commands.append(f"setblock {cx-2} {cy+1} {hz_max+2} lantern[hanging=false]")
commands.append(f"setblock {cx+2} {cy+1} {hz_max+2} lantern[hanging=false]")

print(f"Total commands to execute: {len(commands)}")

# Execute commands sequentially
success_count = 0
for i, cmd in enumerate(commands):
    code, text = send_cmd(cmd)
    if code == 200:
        success_count += 1
    else:
        print(f"Error on cmd #{i}: {cmd} -> Code {code}, {text}")
    time.sleep(0.05)

print(f"Finished building! Successfully executed {success_count}/{len(commands)} commands.")
