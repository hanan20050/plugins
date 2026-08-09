import json
import subprocess
import time
import sys

# Load env variables
env = {}
with open(".env", "r") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip('"').strip("'")

TOKEN = env.get("EXAROTON_TOKEN")
SERVER_ID = env.get("EXAROTON_SERVER_ID")

def run_cmd(cmd):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    curl_cmd = [
        "curl", "-s", "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    time.sleep(0.05)
    return res.stdout

# Shop region bounds:
# X: 1293 to 1300 (Width 8)
# Y: 78 to 81 (Height 4: Y=78 floor, Y=79 & Y=80 interior, Y=81 roof)
# Z: -221 to -215 (Length 7)

BACKUP_FILE = "shop_building_undo_log.json"

def build_shop():
    commands = []
    
    # 1. Solid floor base at Y=78
    commands.append("fill 1293 78 -221 1300 78 -215 polished_diorite")
    
    # 2. Outer Wall Frame at Y=79 and Y=80 (Stone Bricks with Oak Log Corners)
    commands.append("fill 1293 79 -221 1300 80 -215 stone_bricks outline")
    
    # Corner pillars:
    commands.append("fill 1293 79 -221 1293 80 -221 oak_log")
    commands.append("fill 1300 79 -221 1300 80 -221 oak_log")
    commands.append("fill 1293 79 -215 1293 80 -215 oak_log")
    commands.append("fill 1300 79 -215 1300 80 -215 oak_log")
    
    # Interior clear
    commands.append("fill 1294 79 -220 1299 80 -216 air")
    
    # 3. Glass Windows
    commands.append("fill 1295 80 -215 1298 80 -215 glass_pane")
    commands.append("fill 1295 80 -221 1298 80 -221 glass_pane")
    commands.append("fill 1300 80 -219 1300 80 -217 glass_pane")
    # West wall windows (around door)
    commands.append("setblock 1293 80 -220 glass_pane")
    commands.append("setblock 1293 80 -216 glass_pane")
    
    # 4. Double Door entrance on WEST side (X=1293, Z=-218..-217) facing WEST
    commands.append("fill 1293 79 -218 1293 80 -217 air")
    commands.append("setblock 1293 79 -218 oak_door[half=lower,hinge=right,facing=west]")
    commands.append("setblock 1293 80 -218 oak_door[half=upper,hinge=right,facing=west]")
    commands.append("setblock 1293 79 -217 oak_door[half=lower,hinge=left,facing=west]")
    commands.append("setblock 1293 80 -217 oak_door[half=upper,hinge=left,facing=west]")
    
    # 5. Roof ceiling strictly capped at Y=81
    commands.append("fill 1293 81 -221 1300 81 -215 smooth_stone_slab[type=bottom]")
    commands.append("fill 1294 81 -220 1299 81 -216 oak_slab[type=bottom]")
    
    # Lanterns in corners hanging at Y=80
    commands.append("setblock 1294 80 -220 lantern[hanging=true]")
    commands.append("setblock 1299 80 -220 lantern[hanging=true]")
    commands.append("setblock 1294 80 -216 lantern[hanging=true]")
    commands.append("setblock 1299 80 -216 lantern[hanging=true]")

    # 6. Clear all dropped items in region / world
    commands.append("kill @e[type=item]")
    
    # Backup log
    with open(BACKUP_FILE, "w") as f:
        json.dump({"commands": commands, "timestamp": time.time()}, f, indent=2)
        
    print(f"Executing {len(commands)} Minecraft commands to build shop...")
    for c in commands:
        out = run_cmd(c)
        print(f"> {c}: {out}")

def undo_shop():
    undo_commands = [
        "fill 1293 78 -221 1300 81 -215 air"
    ]
    print("Executing undo...")
    for c in undo_commands:
        out = run_cmd(c)
        print(f"> {c}: {out}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        undo_shop()
    else:
        build_shop()
