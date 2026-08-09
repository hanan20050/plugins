#!/usr/bin/env python3
import os
import sys
import time
import json
import yaml
import urllib.request
import urllib.error

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
BACKUP_PATH = os.path.join(PLUGINS_DIR, "Shopkeepers/data/save.yml.sale_bak")

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
        # standard urllib context
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
    except Exception as e:
        # Fallback using curl with explicit DNS resolution if DNS fails
        curl_cmd = [
            "curl", "-s",
            "--resolve", "api.exaroton.com:443:104.26.12.211",
            "-X", "POST", url,
            "-H", f"Authorization: Bearer {EXAROTON_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"command": cmd})
        ]
        import subprocess
        subprocess.run(curl_cmd, capture_output=True)

def broadcast(message_text):
    raw_json = json.dumps([
        {"text": "[SALE ANNOUNCEMENT] ", "color": "gold", "bold": True},
        {"text": message_text, "color": "yellow"}
    ])
    send_exaroton_command(f"tellraw @a {raw_json}")

def apply_discount(data, discount_factor=0.5):
    # Target shopkeeper 1 ONLY
    sk = data.get("1")
    if not sk:
        return data, 0
    recipes = sk.get("recipes", {})
    count = 0
    for r_id, trade in recipes.items():
        item1 = trade.get("item1", {})
        cnt = item1.get("count", 1)
        new_cnt = max(1, int(cnt * discount_factor))
        item1["count"] = new_cnt
        count += 1
    return data, count

def push_and_reload():
    import subprocess
    sync_script = os.path.join(PLUGINS_DIR, "sync.py")
    subprocess.run([sys.executable, sync_script, "push", "Shopkeepers/data/save.yml"], check=True)
    send_exaroton_command("shopkeeper reload")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run building shop flash sale")
    parser.add_argument("--duration", type=int, default=180, help="Duration in seconds (default: 180)")
    parser.add_argument("--discount", type=float, default=0.8, help="Discount ratio off (e.g. 0.8 for 80%% off)")
    args = parser.parse_args()

    duration = args.duration # seconds
    interval = 10 # seconds
    discount_off_percent = int(args.discount * 100)
    pay_factor = max(0.01, 1.0 - args.discount)
    
    print("Reading original save.yml...")
    with open(SAVE_PATH, "r") as f:
        original_data = yaml.safe_load(f)
        
    # Create local backup
    with open(BACKUP_PATH, "w") as f:
        yaml.dump(original_data, f, default_flow_style=False)
        
    print(f"Applying {discount_off_percent}% discount (pay factor {pay_factor}) to Building Shop (Shopkeeper 1)...")
    sale_data = yaml.safe_load(open(BACKUP_PATH, "r"))
    sale_data, modified_count = apply_discount(sale_data, discount_factor=pay_factor)
    
    with open(SAVE_PATH, "w") as f:
        yaml.dump(sale_data, f, default_flow_style=False)
        
    print(f"Updated {modified_count} trades in Building Shop. Syncing to server...")
    push_and_reload()
    
    broadcast(f"🔥 {discount_off_percent}% OFF FLASH SALE in the Building Shop (&eGeneral Store & Build Shop&r) is NOW LIVE for {duration // 60} minutes ({duration} seconds)!")
    print("Sale started. Running countdown notifications every 10 seconds...")
    
    elapsed = 0
    start_time = time.time()
    
    while elapsed < duration:
        time.sleep(interval)
        elapsed += interval
        remaining = duration - elapsed
        if remaining > 0:
            broadcast(f"⏳ Flash Sale Update: {elapsed}s elapsed, {remaining}s remaining! {discount_off_percent}% OFF in Building Shop!")
            print(f"Broadcasted: {elapsed}s elapsed, {remaining}s remaining.")
            
    # Sale ended, restore original
    print("Sale duration ended. Restoring original prices...")
    with open(BACKUP_PATH, "r") as f:
        restored_data = yaml.safe_load(f)
        
    with open(SAVE_PATH, "w") as f:
        yaml.dump(restored_data, f, default_flow_style=False)
        
    push_and_reload()
    broadcast(f"⌛ {discount_off_percent}% OFF FLASH SALE in the Building Shop has ENDED! Standard prices restored.")
    print("Original prices restored and synced successfully.")
    
    if os.path.exists(BACKUP_PATH):
        os.remove(BACKUP_PATH)

if __name__ == "__main__":
    main()
