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

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID

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

import hashlib

MANIFEST_FILE = os.path.join(os.path.dirname(__file__), ".sync_manifest.json")

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_manifest(manifest):
    try:
        with open(MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save manifest: {e}")

def get_file_hash(data_or_path):
    hasher = hashlib.sha256()
    if isinstance(data_or_path, bytes):
        hasher.update(data_or_path)
    elif os.path.exists(data_or_path):
        with open(data_or_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
    else:
        return None
    return hasher.hexdigest()

def clean_path(path):
    path = path.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    if path == ".":
        return ""
    return path.strip("/")

def ask_user_confirmation(title, message):
    """Asks user confirmation via CLI prompt."""
    if sys.stdin.isatty():
        try:
            ans = input(f"{title}: {message} [y/N]: ")
            return ans.lower() == "y"
        except Exception:
            return False
    return False

def check_and_handle_local_deletions(target_path, manifest):
    """Checks if any file previously synced was deleted locally on Mac, and prompts to delete on server."""
    to_delete = []
    target_clean = clean_path(target_path)
    
    for rel_path in list(manifest.keys()):
        if target_clean and not rel_path.startswith(target_clean):
            continue
        if not os.path.exists(rel_path):
            to_delete.append(rel_path)
            
    for rel_path in to_delete:
        should_delete = ask_user_confirmation(
            "⚠️ Local File Deleted",
            f"The file '{rel_path}' was deleted locally on your Mac.\n\nDo you want to delete it from the server too?"
        )
        if should_delete:
            remote_path = f"plugins/{rel_path}".strip("/")
            print(f"Deleting remote file: {remote_path}...")
            res = api_request(f"/servers/{SERVER_ID}/files/data/{remote_path}", method="DELETE")
            if res.get("success"):
                del manifest[rel_path]
                save_manifest(manifest)
                print(f"[DELETED ON SERVER] {rel_path}")
            else:
                print(f"Failed to delete {rel_path} on server: {res.get('error')}")
        else:
            print(f"[SKIPPED REMOTE DELETION] {rel_path}")

def check_and_handle_remote_deletions(target_path, remote_files_found, manifest):
    """Checks if any file previously synced was deleted on the server, and prompts to delete locally."""
    target_clean = clean_path(target_path)
    to_delete = []
    
    for rel_path, entry in list(manifest.items()):
        if target_clean and not rel_path.startswith(target_clean):
            continue
        if os.path.exists(rel_path) and rel_path not in remote_files_found:
            to_delete.append(rel_path)
            
    for rel_path in to_delete:
        should_delete = ask_user_confirmation(
            "⚠️ Server File Deleted",
            f"The file '{rel_path}' was deleted on the Minecraft server.\n\nDo you want to delete it locally on your Mac too?"
        )
        if should_delete:
            os.remove(rel_path)
            del manifest[rel_path]
            save_manifest(manifest)
            print(f"[DELETED LOCALLY] {rel_path}")
        else:
            print(f"[SKIPPED LOCAL DELETION] {rel_path}")

def pull_item(remote_rel_path, force=False, manifest=None, remote_files_found=None, status_callback=None):
    if manifest is None:
        manifest = load_manifest()
    if remote_files_found is None:
        remote_files_found = set()
    
    remote_path = f"plugins/{remote_rel_path}".strip("/")
    
    if status_callback:
        status_callback(remote_rel_path, "Scanning...")

    info_res = api_request(f"/servers/{SERVER_ID}/files/info/{remote_path}")
    if not info_res.get("success") or not info_res.get("data"):
        print(f"Warning: File or directory '{remote_path}' not found on server.")
        return remote_files_found

    data = info_res.get("data", {})
    if data.get("isDirectory"):
        if remote_rel_path:
            os.makedirs(remote_rel_path, exist_ok=True)
        children = data.get("children", [])
        for child in (children or []):
            child_name = child.get("name")
            child_rel = os.path.join(remote_rel_path, child_name)
            pull_item(child_rel, force=force, manifest=manifest, remote_files_found=remote_files_found, status_callback=status_callback)
    else:
        remote_files_found.add(remote_rel_path)
        remote_size = data.get("size", -1)
        
        if not force and os.path.exists(remote_rel_path):
            local_hash = get_file_hash(remote_rel_path)
            local_size = os.path.getsize(remote_rel_path)
            stored_entry = manifest.get(remote_rel_path, {})
            stored_hash = stored_entry.get("hash")
            
            if stored_hash and local_hash == stored_hash and local_size == remote_size:
                if status_callback:
                    status_callback(remote_rel_path, "Unchanged")
                print(f"[SKIP] {remote_rel_path} (Unchanged)")
                return remote_files_found
                
            if stored_hash and local_hash != stored_hash:
                if status_callback:
                    status_callback(remote_rel_path, "Has Local Edits (Skipped)")
                print(f"[SKIP PULL] {remote_rel_path} (Has local un-pushed edits)")
                return remote_files_found

        if status_callback:
            status_callback(remote_rel_path, "Downloading...")
        print(f"Pulling {remote_path} -> {remote_rel_path}...")
        content = api_request(f"/servers/{SERVER_ID}/files/data/{remote_path}", is_binary=True)
        
        parent_dir = os.path.dirname(remote_rel_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(remote_rel_path, "wb") as f:
            f.write(content)
            
        new_hash = get_file_hash(content)
        manifest[remote_rel_path] = {
            "hash": new_hash,
            "size": len(content),
            "mtime": os.path.getmtime(remote_rel_path)
        }
        save_manifest(manifest)
        if status_callback:
            status_callback(remote_rel_path, "Pulled")
        print(f"[PULLED] {remote_rel_path}")
        
    return remote_files_found

def push_item(local_rel_path, force=False, manifest=None, status_callback=None):
    if manifest is None:
        manifest = load_manifest()

    remote_path = f"plugins/{local_rel_path}".strip("/")
    
    if status_callback:
        status_callback(local_rel_path, "Scanning...")

    if not os.path.exists(local_rel_path):
        print(f"Warning: Local path '{local_rel_path}' does not exist.")
        return
        
    if os.path.isdir(local_rel_path):
        for item in os.listdir(local_rel_path):
            # Ignore hidden files, git, recipes, backup folders, and .bak files
            if (item.startswith(".") or 
                item in ("sync.py", "__pycache__", "recipes_26.2", "worldguard_worldedit_commands.md", "backups", "logs_and_backups") or 
                item.endswith(".bak") or 
                item.endswith(".db.bak")):
                continue
            child_rel = os.path.join(local_rel_path, item)
            push_item(child_rel, force=force, manifest=manifest, status_callback=status_callback)
    else:
        # Ignore individual .bak or backup files if targeted directly
        filename = os.path.basename(local_rel_path)
        if filename.endswith(".bak") or filename.endswith(".db.bak") or "history" in filename:
            print(f"[SKIP BACKUP] {local_rel_path}")
            return

        with open(local_rel_path, "rb") as f:
            file_bytes = f.read()
            
        local_hash = get_file_hash(file_bytes)
        stored_entry = manifest.get(local_rel_path, {})
        
        if not force and stored_entry.get("hash") == local_hash:
            if status_callback:
                status_callback(local_rel_path, "Unchanged")
            print(f"[SKIP] {local_rel_path} (Unchanged)")
            return

        if status_callback:
            status_callback(local_rel_path, "Uploading...")
        print(f"Pushing {local_rel_path} -> {remote_path}...")
        res = api_request(f"/servers/{SERVER_ID}/files/data/{remote_path}", method="PUT", data=file_bytes, is_binary=True)
        
        # If parent directory doesn't exist on server, create it and retry upload
        if not res.get("success") and "Parent directory does not exist" in str(res.get("error", "")):
            remote_parent = os.path.dirname(remote_path)
            if remote_parent:
                print(f"Creating missing remote server directory: {remote_parent}...")
                api_request(f"/servers/{SERVER_ID}/files/dir/{remote_parent}", method="POST")
                res = api_request(f"/servers/{SERVER_ID}/files/data/{remote_path}", method="PUT", data=file_bytes, is_binary=True)

        if res.get("success"):
            manifest[local_rel_path] = {
                "hash": local_hash,
                "size": len(file_bytes),
                "mtime": os.path.getmtime(local_rel_path)
            }
            save_manifest(manifest)
            if status_callback:
                status_callback(local_rel_path, "Pushed")
            print(f"[PUSHED] {local_rel_path}")
        else:
            print(f"Failed to push {local_rel_path}: {res.get('error')}")

def reload_plugin_for_path(path):
    status = get_server_status()
    if status != "ONLINE":
        print(f"(Server status is '{status}'; reload skipped)")
        return
    
    clean_p = clean_path(path).lower()
    if "shopkeepers" in clean_p:
        print("Sending server console command: shopkeeper reload ...")
        res = api_request(f"/servers/{SERVER_ID}/command", method="POST", data={"command": "shopkeeper reload"})
        if res.get("success"):
            print("✔ Executed 'shopkeeper reload' on server console!")
    elif "economyshopgui" in clean_p:
        print("Sending server console command: economyshopgui reload ...")
        res = api_request(f"/servers/{SERVER_ID}/command", method="POST", data={"command": "economyshopgui reload"})
        if res.get("success"):
            print("✔ Executed 'economyshopgui reload' on server console!")
    elif "worldguard" in clean_p:
        print("Sending server console command: wg reload ...")
        res = api_request(f"/servers/{SERVER_ID}/command", method="POST", data={"command": "wg reload"})
        if res.get("success"):
            print("✔ Executed 'wg reload' on server console!")

UNSAFE_SERVER_STATES = ["STARTING", "STOPPING", "RESTARTING", "SAVING", "PREPARING", "LOADING", "CREATING"]

def show_mac_alert(title, message):
    """Outputs alert message to console."""
    print(f"\n⚠️  ALERT: {title}\n{message}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 sync.py status")
        print("  python3 sync.py pull <path_relative_to_plugins> [--force]")
        print("  python3 sync.py push <path_relative_to_plugins> [--force]")
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
    force = "-f" in sys.argv or "--force" in sys.argv

    manifest = load_manifest()

    status = get_server_status()
    print(f"Current server status: {status}")

    # Safety check: Block sync operations during unsafe server state transitions
    if status in UNSAFE_SERVER_STATES and not force:
        reason = f"The Exaroton server is currently in '{status}' state.\n\nModifying or syncing files while the server is {status} could cause data corruption or lost progress. Please wait until the server is fully ONLINE or OFFLINE."
        print(f"\n⛔ SYNC ABORTED: Server is {status}")
        print(reason)
        show_mac_alert(f"⛔ Sync Cancelled (Server {status})", reason)
        sys.exit(1)

    if cmd == "pull":
        remote_files = pull_item(target_path, force=force, manifest=manifest)
        check_and_handle_remote_deletions(target_path, remote_files, manifest)
    elif cmd == "push":
        if status != "OFFLINE" and not force and sys.stdin.isatty():
            print("\nWARNING: The Minecraft server is currently running/changing state.")
            print("Modifying files while the server is active can result in lost progress or corruption.")
            try:
                confirm = input("Are you sure you want to push files anyway? (y/N): ")
                if confirm.lower() != "y":
                    print("Push cancelled.")
                    return
            except EOFError:
                pass
        # 1. Check if any local file was deleted and offer to delete on server
        check_and_handle_local_deletions(target_path, manifest)
        # 2. Push remaining local files
        push_item(target_path, force=force, manifest=manifest)
        # 3. Automatically reload plugin in-game if server is ONLINE
        reload_plugin_for_path(target_path)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
