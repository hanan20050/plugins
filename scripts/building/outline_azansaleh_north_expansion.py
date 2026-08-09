import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID")

if not TOKEN or not SERVER_ID:
    print("Error: EXAROTON_TOKEN or EXAROTON_SERVER_ID not set.")
    exit(1)

def run_command(cmd):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"command": cmd}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Command '{cmd}' -> Status {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        print(f"Error sending command '{cmd}': {e}")
        return False

def make_outline_and_floor():
    # 15x15 North Expansion bounds:
    # X: 1240 to 1254 (15 blocks)
    # Z: -219 to -205 (15 blocks, starting North of existing azansaleh_expanded at -204)
    # Floor Y level: y = 62
    
    min_x, max_x = 1240, 1254
    min_z, max_z = -219, -205
    y = 62
    
    print("=== Creating 15x15 North Expansion Outline with Dirt Path Blocks ===")
    
    # 1. Perimeter outline using dirt_path (minecraft:dirt_path)
    cmd1 = f"fill {min_x} {y} {min_z} {max_x} {y} {min_z} minecraft:dirt_path"
    cmd2 = f"fill {min_x} {y} {max_z} {max_x} {y} {max_z} minecraft:dirt_path"
    cmd3 = f"fill {min_x} {y} {min_z} {min_x} {y} {max_z} minecraft:dirt_path"
    cmd4 = f"fill {max_x} {y} {min_z} {max_x} {y} {max_z} minecraft:dirt_path"
    
    for cmd in [cmd1, cmd2, cmd3, cmd4]:
        run_command(cmd)
        time.sleep(0.5)
        
    print("Outline path blocks placed successfully!")

if __name__ == "__main__":
    make_outline_and_floor()
