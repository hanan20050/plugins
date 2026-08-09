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
min_x, max_x = cx - 7, cx + 7  # 1195 to 1209 (15 blocks wide)
min_z, max_z = cz - 7, cz + 7  # -379 to -365 (15 blocks long)

# Kaaba central cube (5x5x5)
kx_min, kx_max = cx - 2, cx + 2
kz_min, kz_max = cz - 2, cz + 2

cmds = [
    # 1. Full 15x15 White Marble Mataf Floor (Smooth Quartz platform)
    f"fill {min_x} {cy} {min_z} {max_x} {cy} {max_z} smooth_quartz",
    
    # 2. Outer 15x15 Perimeter Lighting & Boundary (Quartz Slabs & End Rod Lantern Posts at corners)
    f"setblock {min_x} {cy+1} {min_z} end_rod",
    f"setblock {min_x} {cy+2} {min_z} lantern[hanging=false]",
    f"setblock {max_x} {cy+1} {min_z} end_rod",
    f"setblock {max_x} {cy+2} {min_z} lantern[hanging=false]",
    f"setblock {min_x} {cy+1} {max_z} end_rod",
    f"setblock {min_x} {cy+2} {max_z} lantern[hanging=false]",
    f"setblock {max_x} {cy+1} {max_z} end_rod",
    f"setblock {max_x} {cy+2} {max_z} lantern[hanging=false]",

    # 3. Kaaba Main Black Cube Body (5x5x5 Black Concrete)
    f"fill {kx_min} {cy+1} {kz_min} {kx_max} {cy+5} {kz_max} black_concrete",
    
    # 4. Golden Kiswah Calligraphy Trim (Gold Blocks outline at top edge Y=67)
    f"fill {kx_min} {cy+5} {kz_min} {kx_max} {cy+5} {kz_max} gold_block outline",
    f"fill {kx_min+1} {cy+5} {kz_min+1} {kx_max-1} {cy+5} {kz_max-1} black_concrete",
    
    # 5. Golden Door (Bab al-Kaaba on East side)
    f"setblock {kx_max} {cy+2} {cz} gold_block",
    f"setblock {kx_max} {cy+3} {cz} gold_block",
    
    # 6. Hajar al-Aswad (Black Stone in Silver Lodestone casing at SE Corner)
    f"setblock {kx_max} {cy+2} {kz_max} lodestone",
    
    # 7. Hijr Ismail (Hateem semi-circular wall on West side)
    f"fill {cx-5} {cy+1} {cz-2} {cx-5} {cy+1} {cz+2} smooth_quartz_slab",
    f"setblock {cx-4} {cy+1} {cz-3} smooth_quartz_slab",
    f"setblock {cx-4} {cy+1} {cz+3} smooth_quartz_slab",
    
    # 8. Maqam Ibrahim (Golden Glass Enclosure)
    f"setblock {cx+4} {cy+1} {cz+1} gold_block",
    f"setblock {cx+4} {cy+2} {cz+1} glass"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
