import os, random, requests
from urllib3.util import connection

_orig_create_connection = connection.create_connection
def patched_create_connection(address, *args, **kwargs):
    host, port = address
    if host == "api.exaroton.com":
        host = "104.26.12.211"
    return _orig_create_connection((host, port), *args, **kwargs)

connection.create_connection = patched_create_connection

token = None
server_id = None
with open('/Users/hanansaleh/Documents/GitHub/plugins/.env') as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            if k.strip() == 'EXAROTON_TOKEN': token = v.strip()
            elif k.strip() == 'EXAROTON_SERVER_ID': server_id = v.strip()

def send_cmd(cmd):
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json={"command": cmd})
    return r.status_code, r.text

cx, cy, cz = 1202, 63, -372
min_x, max_x = cx - 14, cx + 15  # 1188 to 1217
min_z, max_z = cz - 14, cz + 15  # -386 to -357

# Generate 20 random (X, Z) locations within 30x30 base to place short grass / tall grass at Y = cy + 1 (Y = 64)
grass_types = ["short_grass", "tall_grass[half=lower]", "poppy", "dandelion", "azure_bluet", "cornflower"]

cmds = []
random.seed(42)  # reproducible random scatter

for _ in range(20):
    rx = random.randint(min_x, max_x)
    rz = random.randint(min_z, max_z)
    g_type = random.choice(["short_grass", "short_grass", "short_grass", "poppy", "dandelion"])
    cmds.append(f"setblock {rx} {cy+1} {rz} {g_type}")

for cmd in cmds:
    status, text = send_cmd(cmd)
    print(f"Executed: {cmd} -> {status}")
