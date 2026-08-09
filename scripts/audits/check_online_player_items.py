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

print("Querying inventory count for online players:")
for p in ["azansalehhh", "hanansaleh"]:
    for item in ["minecraft:diamond", "minecraft:diamond_block", "minecraft:netherite_ingot", "minecraft:netherite_block", "minecraft:emerald_block"]:
        cmd = f"execute as {p} run clear {p} {item} 0"
        run_cmd(cmd)

run_cmd("say Inventory check finished.")
