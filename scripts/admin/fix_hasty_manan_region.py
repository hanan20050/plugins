#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import shutil

REGIONS_FILE = "WorldGuard/worlds/world/regions.yml"
BACKUP_DIR = "WorldGuard/backups"
BACKUP_FILE = os.path.join(BACKUP_DIR, "hasty_manan_region_fix_backup.json")

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists(REGIONS_FILE):
        with open(REGIONS_FILE, "r") as f:
            content = f.read()
        with open(BACKUP_FILE, "w") as f:
            json.dump({"raw_regions_yml": content}, f, indent=2)
        print(f"Backed up {REGIONS_FILE} to {BACKUP_FILE}")

def undo():
    if not os.path.exists(BACKUP_FILE):
        print(f"No backup file found at {BACKUP_FILE}")
        sys.exit(1)
    with open(BACKUP_FILE, "r") as f:
        data = json.load(f)
    with open(REGIONS_FILE, "w") as f:
        f.write(data["raw_regions_yml"])
    print(f"Restored {REGIONS_FILE} from {BACKUP_FILE}")
    
    # Sync and reload
    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)
    send_console_command("rg reload")
    print("Undo completed and synced to server.")

def send_console_command(cmd):
    ENV_FILE = ".env"
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    token = os.environ.get("EXAROTON_TOKEN") or config.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
    server_id = os.environ.get("EXAROTON_SERVER_ID") or config.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"
    
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    print(f"Console Command '{cmd}' output: {res.stdout}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        undo()
        return

    backup()

    # Read current regions file
    with open(REGIONS_FILE, "r") as f:
        lines = f.readlines()

    # Build new regions yml block for hasty & manan
    hasty_manan_yaml = """    hastybag7675_manansaleh2007:
        min: {x: 1256, y: 64, z: -229}
        max: {x: 1272, y: 319, z: -208}
        members: {}
        flags: {other-explosion: deny, pvp: deny, tnt: deny, pvp-group: NON_OWNERS}
        owners:
            unique-ids: [00000000-0000-0000-0009-01f4482c7d17, 95204d3f-ea6c-3dfa-929d-9180927184f8]
        type: cuboid
        priority: 0
    manansaleh2007:
        min: {x: 1256, y: 64, z: -229}
        max: {x: 1272, y: 319, z: -208}
        members: {}
        flags: {other-explosion: deny, pvp: deny, tnt: deny, pvp-group: NON_OWNERS}
        owners:
            unique-ids: [00000000-0000-0000-0009-01f4482c7d17, 95204d3f-ea6c-3dfa-929d-9180927184f8]
        type: cuboid
        priority: 0
"""

    # We need to replace manansaleh2007 section or insert hastybag7675_manansaleh2007
    # Let's inspect where `manansaleh2007:` is in lines and replace it cleanly.
    new_lines = []
    skip = False
    for line in lines:
        if line.startswith("    manansaleh2007:"):
            skip = True
            new_lines.append(hasty_manan_yaml)
            continue
        if skip:
            if line.startswith("    ") and not line.startswith("        ") and ":" in line:
                skip = False
            else:
                continue
        new_lines.append(line)

    with open(REGIONS_FILE, "w") as f:
        f.writelines(new_lines)

    print("Updated WorldGuard regions file with restored Hasty and Manan regions.")

    # Push to Exaroton
    subprocess.run(["python3", "sync.py", "push", REGIONS_FILE], check=True)

    # Reload WorldGuard on server
    send_console_command("rg reload")
    print("Region file pushed to Exaroton server and WorldGuard reloaded.")

if __name__ == "__main__":
    main()
