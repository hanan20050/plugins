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
    # Overall Plot: X=1241..1255, Z=-219..-191
    min_x, max_x = 1241, 1255
    y_floor = 62
    y_wall_min = 63
    y_wall_max = 67
    
    # House bounds (South Half): Z=-204..-191
    h_min_z, h_max_z = -204, -191
    
    print("--- 1. Clearing air above entire plot ---")
    run_command(f"fill {min_x} {y_wall_min} {-219} {max_x} {y_wall_max + 5} {h_max_z} air")
    
    print("--- 2. Setting 2-color floor ---")
    # North Half (Cyan) Z: -219 to -205
    run_command(f"fill {min_x} {y_floor} {-219} {max_x} {y_floor} {-205} cyan_concrete")
    # South Half (Red) Z: -204 to -191
    run_command(f"fill {min_x} {y_floor} {h_min_z} {max_x} {y_floor} {h_max_z} red_concrete")
    
    print("--- 3. Corner Pillars (South Half) ---")
    corners = [
        (min_x, h_min_z), (max_x, h_min_z),
        (min_x, h_max_z), (max_x, h_max_z)
    ]
    for cx, cz in corners:
        run_command(f"fill {cx} {y_wall_min} {cz} {cx} {y_wall_max} {cz} stripped_oak_log")
        
    print("--- 4. Exterior Walls (South Half) ---")
    # North Wall (faces yard)
    run_command(f"fill {min_x+1} {y_wall_min} {h_min_z} {max_x-1} {y_wall_max} {h_min_z} stone_bricks")
    # South Wall
    run_command(f"fill {min_x+1} {y_wall_min} {h_max_z} {max_x-1} {y_wall_max} {h_max_z} stone_bricks")
    # West Wall
    run_command(f"fill {min_x} {y_wall_min} {h_min_z+1} {min_x} {y_wall_max} {h_max_z-1} stone_bricks")
    # East Wall
    run_command(f"fill {max_x} {y_wall_min} {h_min_z+1} {max_x} {y_wall_max} {h_max_z-1} stone_bricks")
    
    print("--- 5. Roof ---")
    run_command(f"fill {min_x} {y_wall_max} {h_min_z} {max_x} {y_wall_max} {h_max_z} oak_planks")
    
    print("--- 6. Windows ---")
    # West Window
    run_command(f"fill {min_x} {y_wall_min+1} {-199} {min_x} {y_wall_min+2} {-198} glass_pane")
    # South Window
    run_command(f"fill {1247} {y_wall_min+1} {h_max_z} {1248} {y_wall_min+2} {h_max_z} glass_pane")

    print("--- 7. Doors ---")
    # North Door (facing yard)
    run_command(f"fill {1248} {y_wall_min} {h_min_z} {1248} {y_wall_min+1} {h_min_z} air")
    run_command(f"setblock {1248} {y_wall_min} {h_min_z} oak_door[half=lower,facing=north]")
    run_command(f"setblock {1248} {y_wall_min+1} {h_min_z} oak_door[half=upper,facing=north]")
    
    # East Door
    run_command(f"fill {max_x} {y_wall_min} {-197} {max_x} {y_wall_min+1} {-197} air")
    run_command(f"setblock {max_x} {y_wall_min} {-197} oak_door[half=lower,facing=east]")
    run_command(f"setblock {max_x} {y_wall_min+1} {-197} oak_door[half=upper,facing=east]")
    
    print("--- 8. Interiors ---")
    # Bed
    run_command(f"setblock 1242 63 -192 red_bed[part=foot,facing=south]")
    run_command(f"setblock 1242 63 -193 red_bed[part=head,facing=south]")
    
    # Crafting table and furnace
    run_command(f"setblock 1244 63 -192 crafting_table")
    run_command(f"setblock 1245 63 -192 furnace[facing=north]")
    
    # Chest
    run_command(f"setblock 1247 63 -192 chest[facing=north,type=left]")
    run_command(f"setblock 1248 63 -192 chest[facing=north,type=right]")
    
    # Lighting (Torches)
    run_command(f"setblock 1242 65 -203 torch")
    run_command(f"setblock 1254 65 -203 torch")
    run_command(f"setblock 1248 65 -192 torch")
    run_command(f"setblock 1248 65 -203 torch")
    
    print("Build complete.")

if __name__ == "__main__":
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val
    build_house()
