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

# STRICT 15x15 BOUNDARIES (7 blocks in each direction from center 1202, -372)
# X range: [1195, 1209] -> exactly 15 blocks (1209 - 1195 + 1 = 15)
# Z range: [-379, -365] -> exactly 15 blocks (-365 - (-379) + 1 = 15)
min_x, max_x = 1195, 1209
min_z, max_z = -379, -365

cmds = [
    # 1. Clear 15x15 region completely up to Y=85
    f"fill {min_x-2} {cy} {min_z-2} {max_x+2} {cy+22} {max_z+2} air",
    
    # 2. Immediately kill all dropped item loot in the area using vanilla namespace
    f"minecraft:kill @e[type=item,x={cx},y={cy+5},z={cz},distance=..30]",
    
    # 3. DOUBLE FLOOR BASE within exact 15x15 area
    # Floor Layer 1 (Y = 63 Base Foundation): Quartz Block
    f"fill {min_x} {cy} {min_z} {max_x} {cy} {max_z} quartz_block",
    
    # Floor Layer 2 (Y = 64 Upper Mataf Surface): Smooth Quartz
    f"fill {min_x} {cy+1} {min_z} {max_x} {cy+1} {max_z} smooth_quartz",
    
    # 4. OUTER BOUNDARY (Perimeter Wall at exact 15x15 edge)
    # Wall pillars & frame (Y=65 to Y=67)
    f"fill {min_x} {cy+2} {min_z} {max_x} {cy+5} {max_z} quartz_block outline",
    f"fill {min_x+1} {cy+2} {min_z+1} {max_x-1} {cy+5} {max_z-1} air",
    
    # Open Archways along boundary walls
    f"fill {min_x+1} {cy+2} {min_z} {max_x-1} {cy+4} {min_z} air",
    f"fill {min_x+1} {cy+2} {max_z} {max_x-1} {cy+4} {max_z} air",
    f"fill {min_x} {cy+2} {min_z+1} {min_x} {cy+4} {max_z-1} air",
    f"fill {max_x} {cy+2} {min_z+1} {max_x} {cy+4} {max_z-1} air",

    # Corner Pillars & Sea Lantern light beacons at boundary corners
    f"setblock {min_x} {cy+5} {min_z} chiseled_quartz_block",
    f"setblock {max_x} {cy+5} {min_z} chiseled_quartz_block",
    f"setblock {min_x} {cy+5} {max_z} chiseled_quartz_block",
    f"setblock {max_x} {cy+5} {max_z} chiseled_quartz_block",

    f"setblock {min_x} {cy+6} {min_z} sea_lantern",
    f"setblock {max_x} {cy+6} {min_z} sea_lantern",
    f"setblock {min_x} {cy+6} {max_z} sea_lantern",
    f"setblock {max_x} {cy+6} {max_z} sea_lantern",

    # 5. HOLLOW KAABA STRUCTURE (5x5x5 Cube centered at 1202, -372)
    # X: [1200, 1204], Z: [-374, -370], Y: [65, 69]
    f"fill {cx-2} {cy+2} {cz-2} {cx+2} {cy+6} {cz+2} black_concrete outline",
    f"fill {cx-1} {cy+2} {cz-1} {cx+1} {cy+5} {cz+1} air",  # Completely hollow inside
    
    # Interior Details (Gold Pillar, Light, Chain)
    f"setblock {cx} {cy+2} {cz} gold_block",
    f"setblock {cx} {cy+3} {cz} sea_lantern",
    f"setblock {cx} {cy+4} {cz} chain",

    # Golden Kiswah Trim (Gold Block outline around top edge Y=69)
    f"fill {cx-2} {cy+6} {cz-2} {cx+2} {cy+6} {cz+2} gold_block outline",
    
    # Golden Bab al-Kaaba Door (East wall, facing East)
    f"fill {cx+2} {cy+2} {cz} {cx+2} {cy+3} {cz} air",
    f"setblock {cx+2} {cy+2} {cz} dark_oak_door[half=lower,hinge=left,facing=east]",
    f"setblock {cx+2} {cy+3} {cz} dark_oak_door[half=upper,hinge=left,facing=east]",

    # 6. Hajar al-Aswad (SE Corner Lodestone)
    f"setblock {cx+2} {cy+2} {cz+2} lodestone",

    # 7. Hijr Ismail (Hateem semi-circular wall on West side)
    f"fill {cx-5} {cy+2} {cz-2} {cx-5} {cy+2} {cz+2} smooth_quartz_slab",
    f"setblock {cx-4} {cy+2} {cz-3} smooth_quartz_slab",
    f"setblock {cx-4} {cy+2} {cz+3} smooth_quartz_slab",

    # 8. Maqam Ibrahim
    f"setblock {cx+4} {cy+2} {cz+1} gold_block",
    f"setblock {cx+4} {cy+3} {cz+1} glass",

    # 9. Second item loot cleanup sweep
    f"minecraft:kill @e[type=item,x={cx},y={cy+5},z={cz},distance=..30]"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
