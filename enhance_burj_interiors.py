import os, requests, time
from urllib3.util import connection

_orig_create_connection = connection.create_connection
def patched_create_connection(address, *args, **kwargs):
    host, port = address
    if host == 'api.exaroton.com':
        host = '104.26.12.211'
    return _orig_create_connection((host, port), *args, **kwargs)
connection.create_connection = patched_create_connection

token, server_id = None, None
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

cmds = []

# --- GROUND FLOOR ATRIUM (Y=64..67) ---
# Reception Desk (X: 1198..1206, Z: -380)
cmds.append("fill 1199 64 -380 1205 64 -380 minecraft:quartz_stairs[facing=south]")
cmds.append("setblock 1202 64 -380 minecraft:gold_block")
# Receptionist End Rod light & Armor Stands / Decor
cmds.append("setblock 1199 65 -380 minecraft:end_rod[facing=up]")
cmds.append("setblock 1205 65 -380 minecraft:end_rod[facing=up]")
# Atrium Seating Lounges (Left & Right of Fountain)
cmds.append("fill 1195 64 -373 1195 64 -371 minecraft:dark_oak_stairs[facing=east]")
cmds.append("fill 1209 64 -373 1209 64 -371 minecraft:dark_oak_stairs[facing=west]")
cmds.append("setblock 1195 64 -372 minecraft:dark_oak_slab")
cmds.append("setblock 1209 64 -372 minecraft:dark_oak_slab")

# --- FLOOR 1: DUPLEX SUITE (Y=68..72) ---
# En-Suite Bathroom (West Wing X: 1197..1199, Z: -375..-371)
cmds.append("fill 1197 69 -375 1197 71 -371 minecraft:smooth_quartz") # Partition wall
cmds.append("setblock 1197 69 -373 minecraft:dark_oak_door[facing=east,half=lower]")
cmds.append("setblock 1197 70 -373 minecraft:dark_oak_door[facing=east,half=upper]")
# Jacuzzi Tub
cmds.append("fill 1198 69 -375 1199 69 -374 minecraft:water")
cmds.append("fill 1198 69 -376 1199 69 -376 minecraft:quartz_stairs[facing=south]")
cmds.append("setblock 1198 70 -375 minecraft:tripwire_hook")
# Vanity Mirror & Basin
cmds.append("setblock 1198 69 -371 minecraft:cauldron")
cmds.append("setblock 1198 70 -371 minecraft:light_blue_stained_glass") # Mirror
# Main Bedroom Wardrobe & TV
cmds.append("fill 1204 69 -379 1206 70 -379 minecraft:dark_oak_trapdoor[facing=south,open=false]") # Wardrobe
cmds.append("fill 1201 70 -378 1203 70 -378 minecraft:black_concrete") # TV Screen
cmds.append("setblock 1202 69 -378 minecraft:bookshelf")

# --- FLOOR 2: ROYAL SUITE (Y=73..77) ---
# En-Suite Bathroom & Spa (East Wing X: 1205..1207, Z: -375..-371)
cmds.append("fill 1205 74 -375 1205 76 -371 minecraft:smooth_quartz") # Partition wall
cmds.append("setblock 1205 74 -373 minecraft:spruce_door[facing=west,half=lower]")
cmds.append("setblock 1205 75 -373 minecraft:spruce_door[facing=west,half=upper]")
# Marble Bathtub
cmds.append("fill 1206 74 -375 1207 74 -374 minecraft:water")
cmds.append("setblock 1206 75 -375 minecraft:tripwire_hook")
cmds.append("setblock 1206 74 -371 minecraft:cauldron")
# Living Room Lounge Couch & Coffee Table
cmds.append("fill 1197 74 -368 1199 74 -368 minecraft:cyan_carpet")
cmds.append("fill 1197 74 -369 1197 74 -367 minecraft:warped_stairs[facing=east]")
cmds.append("setblock 1198 74 -368 minecraft:smooth_quartz_slab") # Coffee Table
# Large Royal TV & Entertainment Console
cmds.append("fill 1200 75 -378 1204 76 -378 minecraft:black_concrete")
cmds.append("fill 1200 74 -378 1204 74 -378 minecraft:jukebox")

# --- FLOOR 3: SKY RESTAURANT & LOUNGE (Y=83..87) ---
# Buffet Bar / Kitchen Counter
cmds.append("fill 1200 84 -379 1204 84 -379 minecraft:polished_blackstone_brick_stairs[facing=south]")
cmds.append("setblock 1202 84 -379 minecraft:gold_block")
# Dining Chairs for tables
cmds.append("setblock 1197 84 -376 minecraft:birch_stairs[facing=east]")
cmds.append("setblock 1199 84 -376 minecraft:birch_stairs[facing=west]")
cmds.append("setblock 1197 84 -368 minecraft:birch_stairs[facing=east]")
cmds.append("setblock 1199 84 -368 minecraft:birch_stairs[facing=west]")
cmds.append("setblock 1205 84 -376 minecraft:birch_stairs[facing=east]")
cmds.append("setblock 1207 84 -376 minecraft:birch_stairs[facing=west]")
cmds.append("setblock 1205 84 -368 minecraft:birch_stairs[facing=east]")
cmds.append("setblock 1207 84 -368 minecraft:birch_stairs[facing=west]")
# Potted Flowers on Dining Tables
cmds.append("setblock 1198 86 -376 minecraft:flower_pot")
cmds.append("setblock 1206 86 -376 minecraft:flower_pot")

# Clear dropped loot
cmds.append(f"minecraft:kill @e[type=item,x={cx},y=75,z={cz},distance=..50]")

print(f"Total interior commands: {len(cmds)}")
for i, cmd in enumerate(cmds, 1):
    status, res = send_cmd(cmd)
    print(f"[{i}/{len(cmds)}] {cmd[:65]}... -> {status}")
    time.sleep(0.12)

print("Interior detail enhance complete!")
