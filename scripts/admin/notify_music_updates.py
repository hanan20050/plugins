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
        {"text": "🎵 MUSIC CATALOG UPDATE 🎵\n", "color": "light_purple", "bold": True},
        {"text": "All Minecraft Music Discs are now available in the shop!\n\n", "color": "green"},
        {"text": "• Common Music Discs (1 for 8 Emeralds):\n", "color": "gray"},
        {"text": "  Cat, Blocks, Chirp, Far, Mall, Mellohi, Stal, Strad, Ward, 13, 11, Wait\n", "color": "white"},
        {"text": "• Rare Music Discs (1 for 16 Emeralds):\n", "color": "gray"},
        {"text": "  Otherside, relic, 5, Creator Music Box, Precipice\n", "color": "white"},
        {"text": "• Epic Music Discs (1 for 32 Emeralds):\n", "color": "gray"},
        {"text": "  Pigstep, Creator (Disc)\n\n", "color": "white"},
        {"text": "📻 Visit General Store & Build Shop (Shopkeeper 1) to buy!\n", "color": "aqua", "bold": True},
        {"text": "========================================\n", "color": "gold"}
    ]
    
    tellraw_cmd = f"tellraw @a {json.dumps(message_json)}"
    print("Broadcasting music disc catalog to players...")
    res = send_command(tellraw_cmd)
    if res.get("success"):
        print("✔ Broadcast sent successfully!")
    else:
        print(f"❌ Failed to send broadcast: {res.get('error')}")

if __name__ == '__main__':
    main()
