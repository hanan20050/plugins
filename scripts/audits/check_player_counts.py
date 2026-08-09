import subprocess, json

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

players = ["azansalehhh", "hanansaleh"]
items = [
    "minecraft:diamond",
    "minecraft:diamond_block",
    "minecraft:netherite_ingot",
    "minecraft:netherite_block",
    "minecraft:emerald_block"
]

print("Scanning online player inventories with tellraw log output:")
for p in players:
    for item in items:
        run_cmd(f"execute as {p} run clear {p} {item} 0")
