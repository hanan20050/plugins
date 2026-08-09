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

def undo_house():
    # Coordinates for azansalehhh
    min_x, max_x = 1241, 1255
    min_z, max_z = -219, -191
    y_floor = 62
    
    print("--- 1. Clearing all structures above floor ---")
    run_command(f"fill {min_x} {y_floor + 1} {min_z} {max_x} {y_floor + 10} {max_z} air")
    
    print("--- 2. Resetting floor to dirt ---")
    run_command(f"fill {min_x} {y_floor} {min_z} {max_x} {y_floor} {max_z} dirt")
    
    print("Undo complete.")

if __name__ == "__main__":
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val
    undo_house()
