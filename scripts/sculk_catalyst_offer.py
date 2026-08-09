#!/usr/bin/env python3
import os
import sys
import time
import json
import yaml
import urllib.request
import subprocess

# Setup environment variables from .env
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                os.environ[key] = val

EXAROTON_TOKEN = os.environ.get("EXAROTON_TOKEN")
EXAROTON_SERVER_ID = os.environ.get("EXAROTON_SERVER_ID")

PLUGINS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.path.join(PLUGINS_DIR, "Shopkeepers/data/save.yml")
BACKUP_PATH = os.path.join(PLUGINS_DIR, "Shopkeepers/data/save.yml.sculk_offer_bak")

def send_exaroton_command(cmd):
    if not EXAROTON_TOKEN or not EXAROTON_SERVER_ID:
        print(f"[CONSOLE CMD SIMULATION] {cmd}")
        return
    url = f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/command/"
    req = urllib.request.Request(
        url,
        data=json.dumps({"command": cmd}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {EXAROTON_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
    except Exception:
        curl_cmd = [
            "curl", "-s",
            "--resolve", "api.exaroton.com:443:104.26.12.211",
            "-X", "POST", url,
            "-H", f"Authorization: Bearer {EXAROTON_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"command": cmd})
        ]
        subprocess.run(curl_cmd, capture_output=True)

def broadcast(prefix, text, color="light_purple"):
    raw_json = json.dumps([
        {"text": f"[{prefix}] ", "color": "dark_purple", "bold": True},
        {"text": text, "color": color}
    ])
    send_exaroton_command(f"tellraw @a {raw_json}")

def push_and_reload():
    sync_script = os.path.join(PLUGINS_DIR, "sync.py")
    subprocess.run([sys.executable, sync_script, "push", "Shopkeepers/data/save.yml"], check=True)
    send_exaroton_command("shopkeeper reload")

def main():
    duration = 600  # 10 minutes in seconds
    interval = 10   # broadcast every 10 seconds

    print("Backing up original save.yml...")
    with open(SAVE_PATH, "r") as f:
        original_content = f.read()

    with open(BACKUP_PATH, "w") as f:
        f.write(original_content)

    data = yaml.safe_load(original_content)
    
    # Locate trade 71 under shopkeeper 4
    if "4" in data and "recipes" in data["4"] and "71" in data["4"]["recipes"]:
        data["4"]["recipes"]["71"]["resultItem"]["count"] = 10
        print("Updated Sculk Catalyst trade to payout 10 Ancient Debris.")
    else:
        print("Error: Trade 71 under shopkeeper 4 not found!")
        sys.exit(1)

    # Validate YAML before writing
    yaml.safe_load(yaml.dump(data))

    with open(SAVE_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    push_and_reload()
    broadcast("SPECIAL OFFER", "ANCIENT CITY OFFER LAUNCHED! Sculk Catalyst now sells for 10 Ancient Debris for the next 10 minutes!", "gold")

    start_time = time.time()
    elapsed = 0

    try:
        while elapsed < duration:
            time.sleep(interval)
            elapsed = int(time.time() - start_time)
            if elapsed >= duration:
                break
            remaining = duration - elapsed
            
            el_m, el_s = divmod(elapsed, 60)
            rem_m, rem_s = divmod(remaining, 60)
            
            msg = f"Sculk Catalyst -> 10 Ancient Debris Offer: {el_m}m {el_s:02d}s elapsed | {rem_m}m {rem_s:02d}s remaining!"
            broadcast("OFFER TIMER", msg, "light_purple")
            sys.stdout.flush()

    finally:
        print("Restoring original save.yml...")
        with open(BACKUP_PATH, "r") as f:
            restored_content = f.read()
        
        with open(SAVE_PATH, "w") as f:
            f.write(restored_content)

        if os.path.exists(BACKUP_PATH):
            os.remove(BACKUP_PATH)

        push_and_reload()
        broadcast("OFFER ENDED", "The Sculk Catalyst 10 Ancient Debris offer has ended! Prices have been restored to normal.", "red")
        print("Offer ended and prices restored successfully.")

if __name__ == "__main__":
    main()
