import os, requests, time
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
# 30x30 Area: X [1187, 1216], Z [-387, -358]
min_x, max_x = cx - 14, cx + 15
min_z, max_z = cz - 14, cz + 15

print(f"Eiffel Tower Base: 30x30, Center ({cx}, {cz}), Base Y={cy}")

cmds = []

# Clear 30x30x65 space
cmds.append(f"fill {min_x} {cy} {min_z} {max_x} {cy+65} {max_z} air")

# 1. Base Platform (Y=63) - Stone Bricks & Polished Andesite lattice base
cmds.append(f"fill {min_x} {cy} {min_z} {max_x} {cy} {max_z} polished_andesite")

# 4 Corner Leg Foundations (Iron Blocks & Polished Andesite)
# Leg NW (1187, -387), Leg NE (1216, -387), Leg SW (1187, -358), Leg SE (1216, -358)
legs = [
    (min_x, min_z),
    (max_x-4, min_z),
    (min_x, max_z-4),
    (max_x-4, max_z-4)
]

for lx, lz in legs:
    # 5x5 Leg Base up to Level 1 Platform
    cmds.append(f"fill {lx} {cy+1} {lz} {lx+4} {cy+1} {lz+4} iron_block")
    cmds.append(f"fill {lx+1} {cy+2} {lz+1} {lx+3} {cy+12} {lz+3} iron_block")
    # Diagonal iron bars latticework
    cmds.append(f"fill {lx} {cy+2} {lz} {lx+4} {cy+12} {lz+4} iron_bars outline")

# 2. Grand Arches joining the 4 legs (Y=69 to Y=73)
cmds.append(f"fill {min_x+5} {cy+10} {min_z+2} {max_x-5} {cy+12} {min_z+2} iron_block")
cmds.append(f"fill {min_x+5} {cy+10} {max_z-2} {max_x-5} {cy+12} {max_z-2} iron_block")
cmds.append(f"fill {min_x+2} {cy+10} {min_z+5} {min_x+2} {cy+12} {max_z-5} iron_block")
cmds.append(f"fill {max_x-2} {cy+10} {min_z+5} {max_x-2} {cy+12} {max_z-5} iron_block")

# 3. First Platform Deck (Y=75) - 22x22 deck
p1_min_x, p1_max_x = cx - 10, cx + 10
p1_min_z, p1_max_z = cz - 10, cz + 10
cmds.append(f"fill {p1_min_x} {cy+12} {p1_min_z} {p1_max_x} {cy+12} {p1_max_z} smooth_stone")
cmds.append(f"fill {p1_min_x} {cy+13} {p1_min_z} {p1_max_x} {cy+13} {p1_max_z} iron_bars outline")
# Platform 1 Illumination
for px in [p1_min_x+2, p1_max_x-2]:
    for pz in [p1_min_z+2, p1_max_z-2]:
        cmds.append(f"setblock {px} {cy+12} {pz} sea_lantern")

# 4. Middle Tower Section (Tapering 14x14 up to Level 2 Platform at Y=88)
m_min_x, m_max_x = cx - 6, cx + 6
m_min_z, m_max_z = cz - 6, cz + 6
cmds.append(f"fill {m_min_x} {cy+14} {m_min_z} {m_max_x} {cy+25} {m_max_z} iron_block outline")
cmds.append(f"fill {m_min_x+1} {cy+14} {m_min_z+1} {m_max_x-1} {cy+25} {m_max_z-1} air")

# Diagonal support girders inside middle section
for y in range(cy+14, cy+25, 3):
    cmds.append(f"fill {m_min_x} {y} {m_min_z} {m_max_x} {y} {m_max_z} iron_bars outline")

# 5. Second Platform Deck (Y=89) - 14x14 deck
cmds.append(f"fill {m_min_x-1} {cy+26} {m_min_z-1} {m_max_x+1} {cy+26} {m_max_z+1} smooth_stone")
cmds.append(f"fill {m_min_x-1} {cy+27} {m_min_z-1} {m_max_x+1} {cy+27} {m_max_z+1} iron_bars outline")
cmds.append(f"setblock {cx-4} {cy+26} {cz-4} sea_lantern")
cmds.append(f"setblock {cx+4} {cy+26} {cz-4} sea_lantern")
cmds.append(f"setblock {cx-4} {cy+26} {cz+4} sea_lantern")
cmds.append(f"setblock {cx+4} {cy+26} {cz+4} sea_lantern")

# 6. Upper Spire Tower Shaft (Tapering 6x6 -> 4x4 -> 2x2 up to Y=115)
s1_min_x, s1_max_x = cx - 3, cx + 3
s1_min_z, s1_max_z = cz - 3, cz + 3
cmds.append(f"fill {s1_min_x} {cy+28} {s1_min_z} {s1_max_x} {cy+40} {s1_max_z} iron_block outline")
cmds.append(f"fill {s1_min_x+1} {cy+28} {s1_min_z+1} {s1_max_x-1} {cy+40} {s1_max_z-1} air")

# Narrowing shaft (4x4) Y=104 to Y=115
cmds.append(f"fill {cx-1} {cy+41} {cz-1} {cx+2} {cy+52} {cz+2} iron_block outline")
cmds.append(f"fill {cx} {cy+41} {cz} {cx+1} {cy+52} {cz+1} air")

# 7. Top Observation Dome & Beacon Spire (Y=116 to Y=125)
cmds.append(f"fill {cx-2} {cy+53} {cz-2} {cx+3} {cy+53} {cz+3} gold_block")
cmds.append(f"fill {cx-1} {cy+54} {cz-1} {cx+2} {cy+56} {cz+2} glass")
cmds.append(f"setblock {cx} {cy+55} {cz} sea_lantern")

# Radio Spire Antenna & Beacon Tip (Y=120 to Y=125)
cmds.append(f"fill {cx} {cy+57} {cz} {cx} {cy+62} {cz} lightning_rod")
cmds.append(f"setblock {cx} {cy+63} {cz} beacon")

print(f"Total commands to execute: {len(cmds)}")

success_count = 0
for i, cmd in enumerate(cmds):
    status, text = send_cmd(cmd)
    if status == 200:
        success_count += 1
    else:
        print(f"Error on cmd #{i}: {cmd} -> Status {status}")
    time.sleep(0.05)

print(f"Finished building Eiffel Tower! Successfully executed {success_count}/{len(cmds)} commands.")
