#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import urllib.request
import urllib.error

# Load environment variables from .env
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, val = line.split("=", 1)
                CONFIG[key.strip()] = val.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")

if not TOKEN or not SERVER_ID:
    print("Error: EXAROTON_TOKEN or EXAROTON_SERVER_ID not found in .env")
    sys.exit(1)

STATUS_MAP = {
    0: "OFFLINE",
    1: "ONLINE",
    2: "STARTING",
    3: "STOPPING",
    4: "RESTARTING",
    5: "PREPARING",
    6: "LOADING",
    7: "CREATING",
    8: "SAVING",
}

def api_request(endpoint, method="GET", data=None, is_binary=False):
    url = f"https://api.exaroton.com/v1{endpoint}"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", method, url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ]

    temp_file = None
    if data is not None:
        if is_binary:
            import tempfile
            tf = tempfile.NamedTemporaryFile(delete=False)
            tf.write(data)
            tf.close()
            temp_file = tf.name
            curl_cmd.extend(["-H", "Content-Type: application/octet-stream", "--data-binary", f"@{temp_file}"])
        else:
            curl_cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])

    try:
        if is_binary and method == "GET":
            res = subprocess.run(curl_cmd, capture_output=True)
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            return res.stdout

        res = subprocess.run(curl_cmd, capture_output=True, text=True)
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

        body = res.stdout.strip()
        if not body:
            return {"success": True}
        return json.loads(body)
    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}

def get_server_status():
    res = api_request(f"/servers/{SERVER_ID}")
    if res.get("success"):
        server_data = res.get("data", {})
        status_code = server_data.get("status")
        return STATUS_MAP.get(status_code, f"UNKNOWN ({status_code})")
    return "UNKNOWN"

def clean_path(path):
    path = path.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    if path == ".":
        return ""
    return path.strip("/")

def pull_item(remote_rel_path):
    remote_path = f"plugins/{remote_rel_path}".strip("/")
    
    # Get info
    info_res = api_request(f"/servers/{SERVER_ID}/files/info/{remote_path}")
    if not info_res.get("success") or not info_res.get("data"):
        print(f"Error: File or directory '{remote_path}' not found on server.")
        return

    data = info_res.get("data", {})
    if data.get("isDirectory"):
        # Create local directory if not exists
        if remote_rel_path:
            os.makedirs(remote_rel_path, exist_ok=True)
        children = data.get("children", [])
        if children is None:
            # Re-fetch directory children if not loaded
            # Note: info endpoint with children is returned for directory
            pass
        
        # If children list is present, pull each child
        for child in (children or []):
            child_name = child.get("name")
            child_rel = os.path.join(remote_rel_path, child_name)
            pull_item(child_rel)
    else:
        # It's a file
        print(f"Pulling {remote_path} -> {remote_rel_path}...")
        content = api_request(f"/servers/{SERVER_ID}/files/data/{remote_path}", is_binary=True)
        
        # Ensure parent directories exist locally
        parent_dir = os.path.dirname(remote_rel_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(remote_rel_path, "wb") as f:
            f.write(content)
        print(f"Pulled {remote_rel_path}")

def push_item(local_rel_path):
    remote_path = f"plugins/{local_rel_path}".strip("/")
    
    if not os.path.exists(local_rel_path):
        print(f"Error: Local path '{local_rel_path}' does not exist.")
        return
        
    if os.path.isdir(local_rel_path):
        # Recursively push files in directory
        for item in os.listdir(local_rel_path):
            # Ignore hidden files, git, recipes, and sync/env/cheat-sheet scripts
            if item.startswith(".") or item in ("sync.py", "__pycache__", "recipes_26.2", "worldguard_worldedit_commands.md"):
                continue
            child_rel = os.path.join(local_rel_path, item)
            push_item(child_rel)
    else:
        print(f"Pushing {local_rel_path} -> {remote_path}...")
        with open(local_rel_path, "rb") as f:
            file_bytes = f.read()
            
        res = api_request(f"/servers/{SERVER_ID}/files/data/{remote_path}", method="PUT", data=file_bytes, is_binary=True)
        if res.get("success"):
            print(f"Pushed {local_rel_path}")
        else:
            print(f"Failed to push {local_rel_path}: {res.get('error')}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 sync.py status")
        print("  python3 sync.py pull <path_relative_to_plugins>")
        print("  python3 sync.py push <path_relative_to_plugins>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    
    if cmd == "status":
        status = get_server_status()
        print(f"Server Status: {status}")
        return

    if len(sys.argv) < 3:
        print(f"Error: Missing path argument for '{cmd}' command.")
        sys.exit(1)

    target_path = clean_path(sys.argv[2])

    if cmd == "pull":
        pull_item(target_path)
    elif cmd == "push":
        status = get_server_status()
        print(f"Current server status: {status}")
        if status != "OFFLINE":
            print("\nWARNING: The Minecraft server is currently running/changing state.")
            print("Modifying files while the server is active can result in lost progress or corruption.")
            confirm = input("Are you sure you want to push files anyway? (y/N): ")
            if confirm.lower() != "y":
                print("Push cancelled.")
                return
        push_item(target_path)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
