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
min_x, max_x = cx - 7, cx + 7  # 1195 to 1209
min_z, max_z = cz - 7, cz + 7  # -379 to -365

kx_min, kx_max = cx - 2, cx + 2
kz_min, kz_max = cz - 2, cz + 2

cmds = [
    # 1. Double Floor / Elevated Base Platform
    # Level 1 (Ground Floor Y=63): Quartz Block Base
    f"fill {min_x} {cy} {min_z} {max_x} {cy} {max_z} quartz_block",
    # Level 2 (Elevated Mataf Floor Y=64): Smooth Quartz Floor with border ring
    f"fill {min_x+1} {cy+1} {min_z+1} {max_x-1} {cy+1} {max_z-1} smooth_quartz",
    
    # 2. Hollow Interior Kaaba (5x5x5 hollow shell)
    f"fill {kx_min} {cy+2} {kz_min} {kx_max} {cy+6} {kz_max} black_concrete outline",
    f"fill {kx_min+1} {cy+2} {kz_min+1} {kx_max-1} {cy+5} {kz_max-1} air",  # Hollow center inside
    
    # Interior Detail: Gold & Sea Lantern interior pillars
    f"setblock {cx} {cy+2} {cz} gold_block",
    f"setblock {cx} {cy+3} {cz} sea_lantern",
    f"setblock {cx} {cy+4} {cz} chain",

    # Golden Kiswah Calligraphy Trim around outer top edge at Y=66
    f"fill {kx_min} {cy+6} {kz_min} {kx_max} {cy+6} {kz_max} gold_block outline",
    
    # Entrance Doorway into Hollow Interior (East Wall)
    f"fill {kx_max} {cy+2} {cz} {kx_max} {cy+3} {cz} air",
    f"setblock {kx_max} {cy+2} {cz} dark_oak_door[half=lower,hinge=left,facing=east]",
    f"setblock {kx_max} {cy+3} {cz} dark_oak_door[half=upper,hinge=left,facing=east]",

    # 3. Outer Mosque Boundary / Colonnade Portico (Double Floor Arcade around perimeter)
    f"fill {min_x} {cy+1} {min_z} {max_x} {cy+4} {max_z} quartz_block outline",
    f"fill {min_x+1} {cy+1} {min_z+1} {max_x-1} {cy+4} {max_z-1} air",
    
    # Archway openings along outer boundary wall so Mataf is open & visible
    f"fill {min_x+1} {cy+2} {min_z} {max_x-1} {cy+3} {min_z} air",
    f"fill {min_x+1} {cy+2} {max_z} {max_x-1} {cy+3} {max_z} air",
    f"fill {min_x} {cy+2} {min_z+1} {min_x} {cy+3} {max_z-1} air",
    f"fill {max_x} {cy+2} {min_z+1} {max_x} {cy+3} {max_z-1} air",

    # Corner Pillars on Boundary Wall
    f"setblock {min_x} {cy+5} {min_z} chiseled_quartz_block",
    f"setblock {max_x} {cy+5} {min_z} chiseled_quartz_block",
    f"setblock {min_x} {cy+5} {max_z} chiseled_quartz_block",
    f"setblock {max_x} {cy+5} {max_z} chiseled_quartz_block",

    f"setblock {min_x} {cy+6} {min_z} sea_lantern",
    f"setblock {max_x} {cy+6} {min_z} sea_lantern",
    f"setblock {min_x} {cy+6} {max_z} sea_lantern",
    f"setblock {max_x} {cy+6} {max_z} sea_lantern",

    # 4. Hajar al-Aswad (SE Corner of Kaaba)
    f"setblock {kx_max} {cy+2} {kz_max} lodestone",

    # 5. Hijr Ismail (Hateem semi-circular wall)
    f"fill {cx-5} {cy+2} {cz-2} {cx-5} {cy+2} {cz+2} smooth_quartz_slab",
    f"setblock {cx-4} {cy+2} {cz-3} smooth_quartz_slab",
    f"setblock {cx-4} {cy+2} {cz+3} smooth_quartz_slab",

    # 6. Maqam Ibrahim
    f"setblock {cx+4} {cy+2} {cz+1} gold_block",
    f"setblock {cx+4} {cy+3} {cz+1} glass"
]

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
