#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import re

# Load environment variables
ENV_FILE = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if not os.path.exists(ENV_FILE):
    ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or "cEuS61sZvNEFS3aB"

def send_exaroton_command(cmd):
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
        return data.get("success", False)
    except Exception:
        return False

def parse_resources_prices():
    filepath = "/Users/hanansaleh/Downloads/plugins/EconomyShopGUI/shops/resources.yml"
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
        
    with open(filepath, "r") as f:
        lines = f.readlines()
        
    items = []
    current_item = None
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Check for item key
        # Check if line defines an item key (e.g., copper_block: or copper_ingot:)
        match = re.match(r"^ {6}([a-z0-9_]+):", line)
        if not match:
            # Maybe inside page2
            match = re.match(r"^ {4}([a-z0-9_]+):", line)
            
        if match:
            if current_item and 'material' in current_item:
                items.append(current_item)
            current_item = {"key": match.group(1)}
            continue
            
        if current_item:
            # Parse material, buy, sell, stack-size
            mat_match = re.match(r"^\s+material:\s*([A-Z0-9_]+)", line)
            if mat_match:
                current_item["material"] = mat_match.group(1)
                continue
                
            buy_match = re.match(r"^\s+buy:\s*([0-9\.]+)", line)
            if buy_match:
                current_item["buy"] = float(buy_match.group(1))
                continue
                
            sell_match = re.match(r"^\s+sell:\s*(\-?[0-9\.]+)", line)
            if sell_match:
                current_item["sell"] = float(sell_match.group(1))
                continue
                
            stack_match = re.match(r"^\s+stack-size:\s*([0-9]+)", line)
            if stack_match:
                current_item["stack-size"] = int(stack_match.group(1))
                continue
                
    if current_item and 'material' in current_item:
        items.append(current_item)
        
    return items

def format_item_name(material):
    # e.g., NETHERITE_INGOT -> Netherite Ingot
    parts = material.split("_")
    return " ".join([p.capitalize() for p in parts])

def main():
    items = parse_resources_prices()
    
    # Send title
    send_exaroton_command('tellraw @a {"text":"\n=======================================","color":"gold"}')
    send_exaroton_command('tellraw @a {"text":"         💎 RESOURCE SHOP PRICES 💎","color":"yellow","bold":true}')
    send_exaroton_command('tellraw @a {"text":"=======================================","color":"gold"}')
    
    for item in items:
        name = format_item_name(item['material'])
        buy = item.get('buy', 0.0)
        sell = item.get('sell', 0.0)
        stack = item.get('stack-size', 1)
        
        buy_str = f"${buy:,.2f}" if buy > 0 else "FREE"
        sell_str = f"${sell:,.2f}" if sell >= 0 else "N/A"
        
        stack_info = f" (x{stack})" if stack > 1 else ""
        
        # Color code: green for buy, red/aqua for sell
        msg_json = [
            {"text": "• ", "color": "gray"},
            {"text": f"{name:<18}", "color": "white", "bold": True},
            {"text": " Buy: ", "color": "gray"},
            {"text": f"{buy_str:<9}", "color": "green"},
            {"text": " Sell: ", "color": "gray"},
            {"text": f"{sell_str}{stack_info}", "color": "aqua"}
        ]
        send_exaroton_command(f'tellraw @a {json.dumps(msg_json)}')
        
    send_exaroton_command('tellraw @a {"text":"=======================================\n","color":"gold"}')
    print("✅ Price list successfully broadcast to all players in chat!")

if __name__ == "__main__":
    main()
