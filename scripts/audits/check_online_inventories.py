import subprocess
import json

online_players = ["azansalehhh", "hanansaleh"]
valuable_items = [
    "minecraft:diamond",
    "minecraft:diamond_block",
    "minecraft:netherite_ingot",
    "minecraft:netherite_block",
    "minecraft:emerald_block"
]

def run_cmd(cmd):
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

print("=== CHECKING INVENTORIES FOR ONLINE PLAYERS ===")
for p in online_players:
    for item in valuable_items:
        res = run_cmd(f"clear {p} {item} 0")
        print(f"Player {p} -> Query {item}")

print("=== EXECUTING OPENINV INVENTORY & ENDER CHEST AUDIT COMMANDS ===")
for p in online_players:
    run_cmd(f"openinv {p}")
