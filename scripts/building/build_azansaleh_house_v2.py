import os
import subprocess
import json
import time

def run_command(command_str):
    print(f"Executing: {command_str}")
    token = os.environ.get("EXAROTON_TOKEN")
    server_id = os.environ.get("EXAROTON_SERVER_ID")
    if not token or not server_id:
        print("Error: Missing EXAROTON_TOKEN or EXAROTON_SERVER_ID")
        return
    
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = json.dumps({"command": command_str})
    
    curl_cmd = [
        "curl", "-s", "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", data
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Success: {result.stdout}")
    else:
        print(f"Failed: {result.stderr}")
    time.sleep(0.5)

def build_house():
    # Coordinates
    min_x, max_x = 1241, 1255
    min_z, max_z = -219, -191
    y_floor = 62
    y_wall_min = 63
    y_wall_max = 67
    
    print("--- 1. Clearing air above floor ---")
    run_command(f"fill {min_x} {y_wall_min} {min_z} {max_x} {y_wall_max + 5} {max_z} air")
    
    print("--- 2. Setting 2-color floor ---")
    # North Half (Cyan) Z: -219 to -205
    run_command(f"fill {min_x} {y_floor} {-219} {max_x} {y_floor} {-205} cyan_concrete")
    # South Half (Red) Z: -204 to -191
    run_command(f"fill {min_x} {y_floor} {-204} {max_x} {y_floor} {-191} red_concrete")
    
    print("--- 3. Corner Pillars ---")
    corners = [
        (min_x, min_z), (max_x, min_z),
        (min_x, max_z), (max_x, max_z)
    ]
    for cx, cz in corners:
        run_command(f"fill {cx} {y_wall_min} {cz} {cx} {y_wall_max} {cz} stripped_oak_log")
        
    print("--- 4. Exterior Walls ---")
    # North Wall
    run_command(f"fill {min_x+1} {y_wall_min} {min_z} {max_x-1} {y_wall_max} {min_z} stone_bricks")
    # South Wall
    run_command(f"fill {min_x+1} {y_wall_min} {max_z} {max_x-1} {y_wall_max} {max_z} stone_bricks")
    # West Wall
    run_command(f"fill {min_x} {y_wall_min} {min_z+1} {min_x} {y_wall_max} {max_z-1} stone_bricks")
    # East Wall
    run_command(f"fill {max_x} {y_wall_min} {min_z+1} {max_x} {y_wall_max} {max_z-1} stone_bricks")
    
    print("--- 5. Roof ---")
    run_command(f"fill {min_x} {y_wall_max} {min_z} {max_x} {y_wall_max} {max_z} oak_planks")
    
    print("--- 6. Windows ---")
    # West Window
    run_command(f"fill {min_x} {y_wall_min+1} {-206} {min_x} {y_wall_min+2} {-205} glass_pane")
    # South Window
    run_command(f"fill {1247} {y_wall_min+1} {max_z} {1248} {y_wall_min+2} {max_z} glass_pane")

    print("--- 7. Doors ---")
    # North Door
    run_command(f"fill {1248} {y_wall_min} {min_z} {1248} {y_wall_min+1} {min_z} air")
    run_command(f"setblock {1248} {y_wall_min} {min_z} oak_door[half=lower,facing=north]")
    run_command(f"setblock {1248} {y_wall_min+1} {min_z} oak_door[half=upper,facing=north]")
    
    # East Door
    run_command(f"fill {max_x} {y_wall_min} {-205} {max_x} {y_wall_min+1} {-205} air")
    run_command(f"setblock {max_x} {y_wall_min} {-205} oak_door[half=lower,facing=east]")
    run_command(f"setblock {max_x} {y_wall_min+1} {-205} oak_door[half=upper,facing=east]")
    
    print("--- 8. Interiors ---")
    # Bed (needs two parts, but simplest is to place a single bed block or let the user place it. Actually, bed is 2 blocks. Let's just use simple blocks to avoid bed state issues, or we use a crafting table/furnace/chests instead).
    # We will just place a red_bed using setblock (head and foot).
    run_command(f"setblock 1242 63 -218 red_bed[part=foot,facing=east]")
    run_command(f"setblock 1243 63 -218 red_bed[part=head,facing=east]")
    
    # Crafting table and furnace
    run_command(f"setblock 1245 63 -218 crafting_table")
    run_command(f"setblock 1246 63 -218 furnace[facing=south]")
    
    # Chest
    run_command(f"setblock 1248 63 -218 chest[facing=south,type=left]")
    run_command(f"setblock 1249 63 -218 chest[facing=south,type=right]")
    
    # Lighting (Torches)
    run_command(f"setblock 1242 65 -210 torch")
    run_command(f"setblock 1254 65 -210 torch")
    run_command(f"setblock 1248 65 -218 torch")
    run_command(f"setblock 1248 65 -192 torch")
    
    print("Build complete.")

if __name__ == "__main__":
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val
    build_house()
