import os
import json
import urllib.request
import ssl

def load_env():
    token, server_id = None, None
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.startswith("EXAROTON_TOKEN="):
                    token = line.strip().split("=", 1)[1].strip("'\"")
                elif line.startswith("EXAROTON_SERVER_ID="):
                    server_id = line.strip().split("=", 1)[1].strip("'\"")
    return token, server_id

def send_command(cmd):
    token, server_id = load_env()
    url = f"https://api.exaroton.com/v1/servers/{server_id}/command/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = json.dumps({"command": cmd}).encode("utf-8")
    
    # Custom HTTPS context with DNS resolution fallback if needed
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Direct connection failed ({e}), attempting curl fallback...")
        import subprocess
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

if __name__ == "__main__":
    import sys
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "list"
    out = send_command(cmd)
    print("Response:", out)
