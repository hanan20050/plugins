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

def build_roof():
    print("--- Building Pitched Roof ---")
    min_z, max_z = -204, -191
    
    # Roof base is at Y=68
    for i in range(8):
        y = 68 + i
        x_left = 1241 + i
        x_right = 1255 - i
        
        if x_left < x_right:
            # Place stairs on the edges
            run_command(f"fill {x_left} {y} {min_z} {x_left} {y} {max_z} oak_stairs[facing=east]")
            run_command(f"fill {x_right} {y} {min_z} {x_right} {y} {max_z} oak_stairs[facing=west]")
            
            # Fill the inner gap with planks
            if x_right - x_left > 1:
                run_command(f"fill {x_left+1} {y} {min_z} {x_right-1} {y} {max_z} oak_planks")
        elif x_left == x_right:
            # Peak of the roof (X=1248)
            run_command(f"fill {x_left} {y} {min_z} {x_left} {y} {max_z} oak_slab[type=bottom]")

    print("Roof build complete.")

if __name__ == "__main__":
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val
    build_roof()
