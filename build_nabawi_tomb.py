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

# Region bounds: X [1188, 1217], Z [-386, -357], Y max 78 (15 blocks height)
# Structure footprint: 22x22 blocks (X: 1192 to 1213, Z: -383 to -362)

commands = []

# 1. Clear area inside region for structure (Y=64 to 78)
commands.append(f"fill 1190 64 -384 1215 78 -359 minecraft:air")

# 2. Raudah Green & Floral Pattern Carpet Floor (Y=63)
commands.append(f"fill 1192 63 -383 1213 63 -362 minecraft:lime_carpet")
commands.append(f"fill 1194 63 -381 1211 63 -364 minecraft:green_carpet")

# 3. Outer Mosque Sandstone Walls (Y=64 to 69)
commands.append(f"fill 1192 64 -383 1213 69 -362 minecraft:cut_sandstone")
commands.append(f"fill 1193 64 -382 1212 69 -363 minecraft:air")

# Corner Pillars / Decorative Towers (Y=64 to 71)
corners = [(1192, -383), (1213, -383), (1192, -362), (1213, -362)]
for x, z in corners:
    commands.append(f"fill {x} 64 {z} {x} 71 {z} minecraft:smooth_sandstone")
    commands.append(f"setblock {x} 72 {z} minecraft:gold_block")

# Arched Entrances & Windows
commands.append(f"fill 1201 64 -383 1204 67 -383 minecraft:air") # North Entrance
commands.append(f"fill 1201 64 -362 1204 67 -362 minecraft:air") # South Entrance
commands.append(f"fill 1192 64 -374 1192 67 -371 minecraft:air") # West Entrance
commands.append(f"fill 1213 64 -374 1213 67 -371 minecraft:air") # East Entrance

# Decorative Arches around entrances
commands.append(f"fill 1201 67 -383 1204 67 -383 minecraft:smooth_sandstone_stairs[facing=south]")
commands.append(f"fill 1201 67 -362 1204 67 -362 minecraft:smooth_sandstone_stairs[facing=north]")

# 4. Inner Tomb Enclosure (Rawdah / Prophet's Chamber) (Y=64 to 68)
commands.append(f"fill 1198 64 -376 1206 67 -368 minecraft:raw_gold_block")
commands.append(f"fill 1199 64 -375 1205 67 -369 minecraft:air")
commands.append(f"fill 1200 65 -376 1204 66 -376 minecraft:yellow_stained_glass_pane")
commands.append(f"fill 1200 65 -368 1204 66 -368 minecraft:yellow_stained_glass_pane")
commands.append(f"fill 1198 65 -374 1198 66 -370 minecraft:yellow_stained_glass_pane")
commands.append(f"fill 1206 65 -374 1206 66 -370 minecraft:yellow_stained_glass_pane")

# Inner Sacred Tomb Chamber Partition (Green Velvet / Emerald & Gold Enclosure)
commands.append(f"fill 1200 64 -374 1204 67 -370 minecraft:dark_prismarine")
commands.append(f"fill 1201 64 -373 1203 66 -371 minecraft:gold_block")

# Lighting inside Inner Tomb
commands.append(f"setblock 1202 65 -372 minecraft:shroomlight")
commands.append(f"setblock 1202 67 -372 minecraft:sea_lantern")

# 5. Iconic Green Dome Roof (Y=70 to 76)
commands.append(f"fill 1197 70 -377 1207 70 -367 minecraft:smooth_quartz")
commands.append(f"fill 1198 70 -376 1206 70 -368 minecraft:air")
commands.append(f"fill 1198 71 -376 1206 71 -368 minecraft:emerald_block")
commands.append(f"fill 1199 71 -375 1205 71 -369 minecraft:air")
commands.append(f"fill 1199 72 -375 1205 72 -369 minecraft:dark_prismarine")
commands.append(f"fill 1200 72 -374 1204 72 -370 minecraft:air")
commands.append(f"fill 1200 73 -374 1204 73 -370 minecraft:dark_prismarine")
commands.append(f"fill 1201 73 -373 1203 73 -371 minecraft:air")
commands.append(f"fill 1201 74 -373 1203 74 -371 minecraft:emerald_block")
commands.append(f"setblock 1202 75 -372 minecraft:gold_block")
commands.append(f"setblock 1202 76 -372 minecraft:lightning_rod")

# 6. Minaret Tower (North-East Corner: 1211..1213, -383..-381, Y=64 to 77)
commands.append(f"fill 1211 64 -383 1213 74 -381 minecraft:quartz_block")
commands.append(f"fill 1212 64 -382 1212 73 -382 minecraft:air")
commands.append(f"fill 1210 75 -384 1214 75 -380 minecraft:smooth_quartz_slab")
commands.append(f"fill 1211 75 -383 1213 75 -381 minecraft:gold_block")
commands.append(f"setblock 1212 76 -382 minecraft:dark_prismarine")
commands.append(f"setblock 1212 77 -382 minecraft:lightning_rod")

# 7. Interior Chandeliers / Lighting
commands.append(f"setblock 1195 67 -380 minecraft:lantern[hanging=true]")
commands.append(f"setblock 1210 67 -380 minecraft:lantern[hanging=true]")
commands.append(f"setblock 1195 67 -365 minecraft:lantern[hanging=true]")
commands.append(f"setblock 1210 67 -365 minecraft:lantern[hanging=true]")

# Cleanup drops
commands.append(f"minecraft:kill @e[type=item,x={cx},y=70,z={cz},distance=..35]")

print(f"Total commands: {len(commands)}")
for i, cmd in enumerate(commands, 1):
    status, res = send_cmd(cmd)
    print(f"[{i}/{len(commands)}] {cmd[:65]}... -> {status}")
    time.sleep(0.12)

print("Build complete!")
