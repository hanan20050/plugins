import os, math, time, requests
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
min_x, max_x = cx - 14, cx + 15  # 1188 to 1217 (30x30 base)
min_z, max_z = cz - 14, cz + 15  # -386 to -357

cmds = []

# 1. Clear area up to Y=145 and kill all dropped item loot
cmds.append(f"fill {min_x-2} {cy} {min_z-2} {max_x+2} {cy+75} {max_z+2} air")
cmds.append(f"minecraft:kill @e[type=item,x={cx},y={cy+20},z={cz},distance=..45]")

# 2. Base Plaza Platform (Y=63)
cmds.append(f"fill {min_x} {cy} {min_z} {max_x} {cy} {max_z} polished_andesite")

# Eiffel Profile Exponential Curvature Function
# R(y) defines half-width of the tower at height y above base (from Y=0 to Y=60)
def get_radius(y):
    # Exponential curve starting at radius 14.5 at y=0 down to radius 1.5 at y=55
    if y <= 15:
        # Leg section curving inwards
        progress = y / 15.0
        return 14.5 - 5.5 * (progress ** 0.6)  # 14.5 down to 9.0
    elif y <= 30:
        # Middle section tapering from 9.0 down to 4.5
        progress = (y - 15) / 15.0
        return 9.0 - 4.5 * (progress ** 0.8)   # 9.0 down to 4.5
    else:
        # Top spire tapering from 4.5 down to 1.0
        progress = (y - 30) / 30.0
        return 4.5 - 3.5 * progress            # 4.5 down to 1.0

# Generate curved legs and shaft layers
for h in range(1, 58):
    y_level = cy + h
    r = get_radius(h)
    
    # 4 curved corner legs at lower levels (h <= 15)
    if h <= 15:
        leg_w = max(1, int(round(r * 0.3)))
        # NW Leg
        rx1, rz1 = int(round(cx - r)), int(round(cz - r))
        cmds.append(f"fill {rx1} {y_level} {rz1} {rx1+leg_w} {y_level} {rz1+leg_w} iron_block")
        # NE Leg
        rx2, rz2 = int(round(cx + r - leg_w)), int(round(cz - r))
        cmds.append(f"fill {rx2} {y_level} {rz2} {rx2+leg_w} {y_level} {rz2+leg_w} iron_block")
        # SW Leg
        rx3, rz3 = int(round(cx - r)), int(round(cz + r - leg_w))
        cmds.append(f"fill {rx3} {y_level} {rz3} {rx3+leg_w} {y_level} {rz3+leg_w} iron_block")
        # SE Leg
        rx4, rz4 = int(round(cx + r - leg_w)), int(round(cz + r - leg_w))
        cmds.append(f"fill {rx4} {y_level} {rz4} {rx4+leg_w} {y_level} {rz4+leg_w} iron_block")

        # Catenary Arch girders between legs at h=12 to h=15
        if h >= 12:
            cmds.append(f"fill {rx1+leg_w} {y_level} {rz1} {rx2} {y_level} {rz1} iron_bars")
            cmds.append(f"fill {rx3+leg_w} {y_level} {rz3} {rx4} {y_level} {rz3} iron_bars")
            cmds.append(f"fill {rx1} {y_level} {rz1+leg_w} {rx1} {y_level} {rz3} iron_bars")
            cmds.append(f"fill {rx2+leg_w} {y_level} {rz2+leg_w} {rx2+leg_w} {y_level} {rz4} iron_bars")
    else:
        # Merged shaft ring profile above Level 1
        rx_min, rx_max = int(round(cx - r)), int(round(cx + r))
        rz_min, rz_max = int(round(cz - r)), int(round(cz + r))
        
        cmds.append(f"fill {rx_min} {y_level} {rz_min} {rx_max} {y_level} {rz_max} iron_block outline")

        # Add lattice cross-bracing every 3 blocks
        if h % 3 == 0:
            cmds.append(f"fill {rx_min} {y_level} {rz_min} {rx_max} {y_level} {rz_max} iron_bars outline")

# Decks
# 1st Deck Platform at h=16 (Y = 79)
cmds.append(f"fill {cx-10} {cy+16} {cz-10} {cx+10} {cy+16} {cz+10} smooth_stone")
cmds.append(f"fill {cx-10} {cy+17} {cz-10} {cx+10} {cy+17} {cz+10} iron_bars outline")
for dx in [-8, 8]:
    for dz in [-8, 8]:
        cmds.append(f"setblock {cx+dx} {cy+16} {cz+dz} sea_lantern")

# 2nd Deck Platform at h=31 (Y = 94)
cmds.append(f"fill {cx-5} {cy+31} {cz-5} {cx+5} {cy+31} {cz+5} smooth_stone")
cmds.append(f"fill {cx-5} {cy+32} {cz-5} {cx+5} {cy+32} {cz+5} iron_bars outline")
for dx in [-4, 4]:
    for dz in [-4, 4]:
        cmds.append(f"setblock {cx+dx} {cy+31} {cz+dz} sea_lantern")

# Top Observation Cupola & Lantern (h=58 to h=64) -> Y=121 to Y=127
cmds.append(f"fill {cx-2} {cy+58} {cz-2} {cx+2} {cy+58} {cz+2} gold_block")
cmds.append(f"fill {cx-1} {cy+59} {cz-1} {cx+1} {cy+61} {cz+1} glass")
cmds.append(f"setblock {cx} {cy+60} {cz} sea_lantern")

# Radio Antenna Tip
cmds.append(f"fill {cx} {cy+62} {cz} {cx} {cy+66} {cz} end_rod")
cmds.append(f"setblock {cx} {cy+67} {cz} beacon")

# Second loot cleanup sweep
cmds.append(f"minecraft:kill @e[type=item,x={cx},y={cy+20},z={cz},distance=..45]")

print(f"Total realistic build commands: {len(cmds)}")

success_count = 0
for i, cmd in enumerate(cmds):
    status, text = send_cmd(cmd)
    if status == 200:
        success_count += 1
    else:
        print(f"Error on cmd #{i}: {cmd} -> Status {status}")
    time.sleep(0.04)

print(f"Finished building realistic Eiffel Tower! Successfully executed {success_count}/{len(cmds)} commands.")
