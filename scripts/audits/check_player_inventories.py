import subprocess
import json
import time

players = [
    ".mustafahacker67",
    ".HastyBag7675",
    ".WiryCircle3938",
    "hanansaleh",
    "manansaleh2007",
    "NightmareDady",
    "azansalehhh",
    ".AzanSaleh"
]

valuable_items = [
    "minecraft:diamond",
    "minecraft:diamond_block",
    "minecraft:netherite_ingot",
    "minecraft:netherite_block",
    "minecraft:emerald_block"
]

def run_cmd(cmd):
    import urllib.request
    from run_console_command import load_env
    token, server_id = load_env()
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
    return res.stdout

print("=== CHECKING ONLINE PLAYERS & INVENTORIES FOR VALUABLE BLOCKS/ITEMS ===")
for p in players:
    for item in valuable_items:
        # Execute clear test command (count 0) to check how many items player holds
        cmd = f"clear {p} {item} 0"
        res = run_cmd(cmd)
        print(f"Player {p} -> Query {item}: {res}")
