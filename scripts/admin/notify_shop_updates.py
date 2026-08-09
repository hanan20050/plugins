import os
import sys
import json
import subprocess

TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = "cEuS61sZvNEFS3aB"

def send_command(command):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-H", "User-Agent: Mozilla/5.0",
        "-d", json.dumps({"command": command})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        return json.loads(res.stdout)
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    message_json = [
        "",
        {"text": "\n========================================\n", "color": "gold"},
        {"text": "✨ NEW BUILD SHOP CATALOG UPDATED ✨\n", "color": "yellow", "bold": True},
        {"text": "Added 47 new blocks required for the Big House:\n\n", "color": "green"},
        {"text": "• Common Blocks (16 for 2 Emeralds):\n", "color": "gray"},
        {"text": "  Grass Block, Acacia/Oak Stairs, Oak/Pale Oak Fences, Slab & Trapdoors\n", "color": "white"},
        {"text": "• Decors & Concrete (16 for 3 Emeralds):\n", "color": "gray"},
        {"text": "  White/Black/Light Gray Concrete, Carpets, Oak/Dark Oak Doors, Glass Panes\n", "color": "white"},
        {"text": "• Functional & Utility (Prices vary):\n", "color": "gray"},
        {"text": "  Chests, Barrels, Composters, Furnaces (8 for 4 Emeralds), Bookshelves (4 for 6 Emeralds)\n", "color": "white"},
        {"text": "• Rare & Lighting:\n", "color": "gray"},
        {"text": "  Quartz Stairs/Slabs, Light Gray Beds (4 for 6 Emeralds), Sea Lanterns & Lanterns (4 for 12 Emeralds)\n\n", "color": "white"},
        {"text": "🛒 Visit General Store & Build Shop (Shopkeeper 1) to buy!\n", "color": "aqua", "bold": True},
        {"text": "========================================\n", "color": "gold"}
    ]
    
    tellraw_cmd = f"tellraw @a {json.dumps(message_json)}"
    print("Broadcasting shop updates to players...")
    res = send_command(tellraw_cmd)
    if res.get("success"):
        print("✔ Broadcast sent successfully!")
    else:
        print(f"❌ Failed to send broadcast: {res.get('error')}")

if __name__ == '__main__':
    main()
