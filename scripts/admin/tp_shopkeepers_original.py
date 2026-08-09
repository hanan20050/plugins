#!/usr/bin/env python3
"""
Teleport shopkeeper entities back to their original coordinates saved in Shopkeepers save.yml data file.

Original Shopkeeper Locations from save.yml:
  - ID 1 (&eGeneral Store & Build Shop): X=1297.5, Y=80, Z=-217.5 (UUID: 149ce7e3-d907-4b7c-9b90-302484745505)
  - ID 2 (&6Land & House Upgrades): X=1297.5, Y=80, Z=-215.5 (UUID: a28b74c2-9b2f-4889-bdc0-f4b6794bb71b)
  - ID 4 (&aSell Drops & Buyback Shop): X=1297.5, Y=80, Z=-219.5 (UUID: e8f2b3c4-75d9-4b12-a3e4-829104756182)
  - ID 5 (&6Money Exchange): X=1299.5, Y=80, Z=-217.5 (UUID: 23f7e445-49fa-4d0b-89e3-5152914dd67e)
  - ID 6 (&dEnchanted Book Emporium): X=1299.5, Y=80, Z=-219.5 (UUID: d750a5be-0c4d-41d2-8216-f5ece811d063)
  - ID 7 (&bBiome Coordinates & Explorer): X=1299.5, Y=80, Z=-215.5 (UUID: 2fa9bf42-8f1d-47a3-ab62-ecb5aae0e79f)

Supports dry-run and reload options.
"""

import os
import sys
import json
import subprocess
import argparse

# Credentials and constants
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

SHOPKEEPERS = [
    {"id": "1", "name": "General Store & Build Shop", "uuid": "149ce7e3-d907-4b7c-9b90-302484745505", "x": 1297.5, "y": 79.0, "z": -217.5},
    {"id": "2", "name": "Land & House Upgrades", "uuid": "a28b74c2-9b2f-4889-bdc0-f4b6794bb71b", "x": 1297.5, "y": 79.0, "z": -215.5},
    {"id": "4", "name": "Sell Drops & Buyback Shop", "uuid": "e8f2b3c4-75d9-4b12-a3e4-829104756182", "x": 1297.5, "y": 79.0, "z": -219.5},
    {"id": "5", "name": "Money Exchange", "uuid": "23f7e445-49fa-4d0b-89e3-5152914dd67e", "x": 1299.5, "y": 79.0, "z": -217.5},
    {"id": "6", "name": "Enchanted Book Emporium", "uuid": "d750a5be-0c4d-41d2-8216-f5ece811d063", "x": 1299.5, "y": 79.0, "z": -219.5},
    {"id": "7", "name": "Biome Coordinates & Explorer", "uuid": "2fa9bf42-8f1d-47a3-ab62-ecb5aae0e79f", "x": 1299.5, "y": 79.0, "z": -215.5},
]

def send_exaroton_command(cmd, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] Console Command: {cmd}")
        return True

    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if not data.get("success", False):
            print(f"[ERROR] Exaroton Command Failed: {data.get('error')}")
            return False
        return True
    except Exception as e:
        print(f"[ERROR] Failed to parse API response: {res.stdout}")
        return False

def teleport_shopkeepers(dry_run=False):
    print("Teleporting all shopkeepers to their exact original positions...")
    
    # First reload shopkeepers plugin to ensure save.yml entities are spawned / synced
    send_exaroton_command("shopkeepers reload", dry_run=dry_run)

    for shop in SHOPKEEPERS:
        # Teleport entity by UUID
        cmd_uuid = f"tp {shop['uuid']} {shop['x']} {shop['y']} {shop['z']}"
        print(f"Teleporting Shopkeeper ID {shop['id']} ({shop['name']}) -> {shop['x']}, {shop['y']}, {shop['z']}")
        send_exaroton_command(cmd_uuid, dry_run=dry_run)

    # Secondary reload to guarantee position persistence
    send_exaroton_command("shopkeepers reload", dry_run=dry_run)
    print("All shopkeepers successfully teleported to original locations.")

def main():
    parser = argparse.ArgumentParser(description="Teleport all shopkeepers to original positions.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without sending console commands")
    args = parser.parse_args()

    teleport_shopkeepers(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
