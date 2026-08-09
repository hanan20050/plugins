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
# Region inner footprint: X [1189, 1216], Z [-385, -358]

cmds = []

# 1. Clear building volume (Y=64 to 95) inside test1
cmds.append(f"fill 1189 64 -385 1216 95 -358 minecraft:air")

# 2. Water Base / Island Surrounding Base (Y=63)
cmds.append(f"fill 1190 63 -384 1215 63 -359 minecraft:water")
# Core podium platform inside water (X: 1193..1211, Z: -381..-363)
cmds.append(f"fill 1193 63 -381 1211 63 -363 minecraft:smooth_quartz")

# 3. Main Outer V-Frame & Spine Towers (White Quartz Pillars)
# West Spine Tower (X=1194, Z: -380..-364)
cmds.append(f"fill 1194 64 -380 1195 90 -364 minecraft:quartz_pillar")
# East Spine Tower (X=1210, Z: -380..-364)
cmds.append(f"fill 1209 64 -380 1210 90 -364 minecraft:quartz_pillar")

# Cross Arch at Top (Y=90)
cmds.append(f"fill 1194 90 -380 1210 91 -364 minecraft:smooth_quartz")
cmds.append(f"fill 1196 90 -379 1208 90 -365 minecraft:air")

# 4. Curved Front Glass Sail (Light Blue Glass + Quartz Ribs)
# Layered sail curve pushing outward on Z axis
sail_layers = [
    (64, -381, -363, 1196, 1208),
    (67, -382, -362, 1196, 1208),
    (70, -383, -361, 1197, 1207),
    (73, -384, -360, 1197, 1207),
    (77, -384, -360, 1198, 1206),
    (81, -383, -361, 1198, 1206),
    (85, -382, -362, 1199, 1205),
    (88, -381, -363, 1200, 1204),
]

for y_bot, z_n, z_s, x1, x2 in sail_layers:
    y_top = min(y_bot + 2, 89)
    cmds.append(f"fill {x1} {y_bot} {z_n} {x2} {y_top} {z_n} minecraft:light_blue_stained_glass")
    cmds.append(f"fill {x1} {y_bot} {z_s} {x2} {y_top} {z_s} minecraft:light_blue_stained_glass")

# Back Curved Spine Wall (X=1202 center axis)
cmds.append(f"fill 1196 64 -372 1208 89 -372 minecraft:white_concrete")

# 5. Internal Floors & Luxury Suites
# Ground Floor Atrium (Y=64..67)
cmds.append(f"fill 1196 64 -379 1208 64 -365 minecraft:sea_lantern") # Illuminated floor pattern
cmds.append(f"fill 1197 64 -378 1207 64 -366 minecraft:gold_block")
# Atrium Fountain
cmds.append(f"fill 1200 64 -374 1204 64 -370 minecraft:water")
cmds.append(f"setblock 1202 65 -372 minecraft:sea_lantern")

# Suite Floor 1 (Y=68..72)
cmds.append(f"fill 1196 68 -379 1208 68 -365 minecraft:smooth_quartz")
cmds.append(f"fill 1197 69 -378 1207 72 -366 minecraft:air") # Room space
# Beds & Luxury Furniture Level 1
cmds.append(f"setblock 1198 69 -377 minecraft:red_bed[facing=north]")
cmds.append(f"setblock 1206 69 -377 minecraft:red_bed[facing=north]")
cmds.append(f"fill 1198 69 -368 1200 69 -368 minecraft:red_carpet")
cmds.append(f"fill 1204 69 -368 1206 69 -368 minecraft:red_carpet")
cmds.append(f"setblock 1202 72 -372 minecraft:glowstone") # Chandelier

# Suite Floor 2 (Y=73..77)
cmds.append(f"fill 1196 73 -379 1208 73 -365 minecraft:smooth_quartz")
cmds.append(f"fill 1197 74 -378 1207 77 -366 minecraft:air")
cmds.append(f"setblock 1198 74 -377 minecraft:cyan_bed[facing=north]")
cmds.append(f"setblock 1206 74 -377 minecraft:cyan_bed[facing=north]")
cmds.append(f"fill 1201 74 -367 1203 74 -367 minecraft:bookshelf")
cmds.append(f"setblock 1202 77 -372 minecraft:glowstone")

# Sky Lounge / Restaurant Floor (Y=83..87)
cmds.append(f"fill 1196 83 -379 1208 83 -365 minecraft:birch_planks")
cmds.append(f"fill 1197 84 -378 1207 87 -366 minecraft:air")
# Tables & Seating
for tx in [1198, 1206]:
    for tz in [-376, -368]:
        cmds.append(f"setblock {tx} 84 {tz} minecraft:oak_fence")
        cmds.append(f"setblock {tx} 85 {tz} minecraft:heavy_weighted_pressure_plate")
cmds.append(f"setblock 1202 87 -372 minecraft:sea_lantern")

# Central Elevator Shaft (Glass & Sea Lanterns)
cmds.append(f"fill 1201 64 -372 1203 89 -372 minecraft:glass")
cmds.append(f"fill 1202 64 -372 1202 89 -372 minecraft:chain")

# 6. Cantilevered Sky View Restaurant (Extending out North Z: -385..-380 at Y=85)
cmds.append(f"fill 1199 85 -385 1205 85 -380 minecraft:smooth_quartz")
cmds.append(f"fill 1199 86 -385 1205 87 -380 minecraft:glass")
cmds.append(f"fill 1200 86 -384 1204 86 -381 minecraft:air")

# 7. Iconic Cantilevered Circular Helipad (South end Z: -363..-358 at Y=88)
# Circular Quartz Helipad
cmds.append(f"fill 1199 88 -363 1205 88 -358 minecraft:smooth_quartz")
cmds.append(f"fill 1200 88 -364 1204 88 -357 minecraft:smooth_quartz")
# Yellow & Black 'H' Markings
cmds.append(f"fill 1200 89 -362 1204 89 -359 minecraft:yellow_concrete")
cmds.append(f"setblock 1201 89 -361 minecraft:black_concrete")
cmds.append(f"setblock 1203 89 -361 minecraft:black_concrete")
cmds.append(f"fill 1201 89 -360 1203 89 -360 minecraft:black_concrete")
cmds.append(f"setblock 1201 89 -359 minecraft:black_concrete")
cmds.append(f"setblock 1203 89 -359 minecraft:black_concrete")

# Top Mast Spike (Y=91..95)
cmds.append(f"fill 1202 91 -372 1202 94 -372 minecraft:iron_bars")
cmds.append(f"setblock 1202 95 -372 minecraft:end_rod")

# 8. Clear dropped loot items
cmds.append(f"minecraft:kill @e[type=item,x={cx},y=75,z={cz},distance=..50]")

print(f"Total commands to execute: {len(cmds)}")

for i, cmd in enumerate(cmds, 1):
    status, res = send_cmd(cmd)
    print(f"[{i}/{len(cmds)}] {cmd[:65]}... -> {status}")
    time.sleep(0.12)

print("Burj Al Arab Build complete!")
