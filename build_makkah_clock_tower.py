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
# Region inner footprint: X [1188, 1217], Z [-386, -357]

cmds = []

# 1. Clear volume (Y=63 to 125) inside test1
cmds.append("fill 1188 63 -386 1217 125 -357 minecraft:air")

# 2. Podium Base (Y=63 to 70) Footprint: X [1190, 1214], Z [-384, -360]
cmds.append("fill 1190 63 -384 1214 70 -360 minecraft:smooth_sandstone")
cmds.append("fill 1191 64 -383 1213 70 -361 minecraft:air")

# Podium Arched Entrances & Golden Accents
cmds.append("fill 1200 64 -384 1204 67 -384 minecraft:air") # North Entrance
cmds.append("fill 1200 64 -360 1204 67 -360 minecraft:air") # South Entrance
cmds.append("fill 1190 64 -374 1190 67 -370 minecraft:air") # West Entrance
cmds.append("fill 1214 64 -374 1214 67 -370 minecraft:air") # East Entrance
cmds.append("fill 1190 70 -384 1214 70 -360 minecraft:gold_block") # Podium Trim Ring

# Ground Atrium Interior (Y=64..69)
cmds.append("fill 1192 63 -382 1212 63 -362 minecraft:polished_diorite") # Marble floor
cmds.append("fill 1199 64 -377 1205 64 -377 minecraft:quartz_stairs[facing=south]") # Reception
cmds.append("setblock 1202 64 -377 minecraft:gold_block")
cmds.append("setblock 1202 69 -372 minecraft:sea_lantern") # Chandelier

# 3. Main Tower Shaft (Y=71 to 95) Footprint: X [1193, 1211], Z [-381, -363]
cmds.append("fill 1193 71 -381 1211 95 -363 minecraft:quartz_pillar")
cmds.append("fill 1194 71 -380 1210 95 -364 minecraft:emerald_block") # Green Glass look
cmds.append("fill 1195 71 -379 1209 95 -365 minecraft:air")

# Tower Floor Interiors (Y=76, Y=83, Y=90)
for y_floor in [76, 83, 90]:
    cmds.append(f"fill 1195 {y_floor} -379 1209 {y_floor} -365 minecraft:smooth_quartz")
    cmds.append(f"setblock 1197 {y_floor+1} -377 minecraft:green_bed[facing=north]")
    cmds.append(f"setblock 1207 {y_floor+1} -377 minecraft:green_bed[facing=north]")
    cmds.append(f"setblock 1202 {y_floor+3} -372 minecraft:sea_lantern")

# Central Elevator Shaft (Y=64 to 105)
cmds.append("fill 1201 64 -372 1203 105 -372 minecraft:glass")
cmds.append("fill 1202 64 -372 1202 105 -372 minecraft:chain")

# 4. Clock Housing Platform & 4-Sided Clock Face (Y=96 to 105)
# Clock Face Base Box (X: 1195..1209, Z: -379..-365)
cmds.append("fill 1195 96 -379 1209 105 -365 minecraft:gold_block")
cmds.append("fill 1196 96 -378 1208 105 -366 minecraft:sea_lantern") # Internal Backlight
cmds.append("fill 1197 96 -377 1207 105 -367 minecraft:air")

# Clock Faces (White Quartz & Black Concrete hands on 4 sides)
# North Clock Face (Z=-379)
cmds.append("fill 1197 97 -379 1207 104 -379 minecraft:smooth_quartz")
cmds.append("fill 1201 98 -379 1203 103 -379 minecraft:black_concrete") # Vertical hand
cmds.append("fill 1199 100 -379 1205 100 -379 minecraft:black_concrete") # Horizontal hand
cmds.append("setblock 1202 100 -379 minecraft:gold_block") # Center pivot

# South Clock Face (Z=-365)
cmds.append("fill 1197 97 -365 1207 104 -365 minecraft:smooth_quartz")
cmds.append("fill 1201 98 -365 1203 103 -365 minecraft:black_concrete")
cmds.append("fill 1199 100 -365 1205 100 -365 minecraft:black_concrete")
cmds.append("setblock 1202 100 -365 minecraft:gold_block")

# West Clock Face (X=1195)
cmds.append("fill 1195 97 -377 1195 104 -367 minecraft:smooth_quartz")
cmds.append("fill 1195 98 -374 1195 103 -370 minecraft:black_concrete")
cmds.append("fill 1195 100 -376 1195 100 -368 minecraft:black_concrete")
cmds.append("setblock 1195 100 -372 minecraft:gold_block")

# East Clock Face (X=1209)
cmds.append("fill 1209 97 -377 1209 104 -367 minecraft:smooth_quartz")
cmds.append("fill 1209 98 -374 1209 103 -370 minecraft:black_concrete")
cmds.append("fill 1209 100 -376 1209 100 -368 minecraft:black_concrete")
cmds.append("setblock 1209 100 -372 minecraft:gold_block")

# 5. Golden Stepped Crown & Spire (Y=106 to 118)
cmds.append("fill 1196 106 -378 1208 107 -366 minecraft:gold_block")
cmds.append("fill 1197 108 -377 1207 109 -367 minecraft:gold_block")
cmds.append("fill 1198 110 -376 1206 111 -368 minecraft:gold_block")
cmds.append("fill 1199 112 -375 1205 113 -369 minecraft:gold_block")
cmds.append("fill 1200 114 -374 1204 115 -370 minecraft:emerald_block")

# Spire Shaft (Y=116 to 119)
cmds.append("fill 1201 116 -373 1203 119 -371 minecraft:gold_block")

# 6. Crescent Moon Finial (Y=120 to 125)
cmds.append("setblock 1202 120 -372 minecraft:lightning_rod")
cmds.append("fill 1201 121 -372 1203 121 -372 minecraft:gold_block")
cmds.append("setblock 1200 122 -372 minecraft:gold_block")
cmds.append("setblock 1204 122 -372 minecraft:gold_block")
cmds.append("setblock 1200 123 -372 minecraft:gold_block")
cmds.append("setblock 1204 123 -372 minecraft:gold_block")
cmds.append("fill 1201 124 -372 1203 124 -372 minecraft:gold_block")
cmds.append("setblock 1202 125 -372 minecraft:sea_lantern") # Glowing Tip

# 7. Red Cement Outer Border & Grass Base Restoration (Y=63)
min_x, max_x = 1188, 1217
min_z, max_z = -386, -357
cmds.append(f"fill {min_x} 63 {min_z} {max_x} 63 {min_z} minecraft:red_concrete")
cmds.append(f"fill {min_x} 63 {max_z} {max_x} 63 {max_z} minecraft:red_concrete")
cmds.append(f"fill {min_x} 63 {min_z} {min_x} 63 {max_z} minecraft:red_concrete")
cmds.append(f"fill {max_x} 63 {min_z} {max_x} 63 {max_z} minecraft:red_concrete")

# Clear dropped items
cmds.append(f"minecraft:kill @e[type=item,x={cx},y=70,z={cz},distance=..60]")

print(f"Total commands to execute: {len(cmds)}")

for i, cmd in enumerate(cmds, 1):
    status, res = send_cmd(cmd)
    print(f"[{i}/{len(cmds)}] {cmd[:65]}... -> {status}")
    time.sleep(0.12)

print("Makkah Clock Tower build complete!")
