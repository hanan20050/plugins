#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from datetime import datetime

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYNC_SCRIPT = os.path.join(BASE_DIR, "sync.py")

# Directories to monitor & sync
MONITORED_PATHS = ["Shopkeepers", "WorldGuard", "EconomyShopGUI"]
POLL_INTERVAL = 20  # seconds

def send_mac_notification(title, message):
    """Sends a native macOS desktop notification."""
    try:
        safe_title = title.replace('"', '\\"')
        safe_msg = message.replace('"', '\\"')
        cmd = f'display notification "{safe_msg}" with title "{safe_title}"'
        subprocess.run(["osascript", "-e", cmd], capture_output=True)
    except Exception as e:
        print(f"Failed to send notification: {e}")

def run_sync(command, path):
    """Runs sync.py pull or push and returns list of modified files."""
    try:
        res = subprocess.run(
            [sys.executable, SYNC_SCRIPT, command, path],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        output = res.stdout or ""
        pushed = []
        pulled = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("[PUSHED]"):
                pushed.append(line.replace("[PUSHED]", "").strip())
            elif line.startswith("[PULLED]"):
                pulled.append(line.replace("[PULLED]", "").strip())
        return pushed, pulled
    except Exception as e:
        print(f"Error executing sync {command} on {path}: {e}")
        return [], []

def is_online():
    """Checks if server API connection is reachable."""
    try:
        res = subprocess.run(
            [sys.executable, SYNC_SCRIPT, "status"],
            capture_output=True,
            text=True,
            timeout=8,
            cwd=BASE_DIR
        )
        return "Server Status:" in (res.stdout or "")
    except Exception:
        return False

def main():
    print("=" * 60)
    print("Minecraft Auto-Sync Background Daemon Started")
    print(f"Monitoring: {', '.join(MONITORED_PATHS)}")
    print(f"Poll Interval: {POLL_INTERVAL} seconds")
    print("=" * 60)
    sys.stdout.flush()

    was_offline = False

    while True:
        try:
            online = is_online()

            if not online:
                if not was_offline:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mac is offline. Pausing sync until connection is restored.")
                    was_offline = True
                time.sleep(POLL_INTERVAL)
                continue

            if was_offline:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mac back online! Syncing offline changes...")
                send_mac_notification("🌐 Internet Restored", "Mac is back online. Syncing offline edits...")
                was_offline = False

            total_pushed = []
            total_pulled = []

            for path in MONITORED_PATHS:
                # 1. Push local updates first so local edits are never overwritten by pull
                pushed_files, pulled_files = run_sync("push", path)
                total_pushed.extend(pushed_files)

                # 2. Pull remote updates second
                pushed_files, pulled_files = run_sync("pull", path)
                total_pulled.extend(pulled_files)

            # Notify user if any files synced
            if total_pulled:
                count = len(total_pulled)
                msg = f"Downloaded {count} file(s) from server:\n" + "\n".join(total_pulled[:3])
                if count > 3:
                    msg += f"\n...and {count - 3} more"
                send_mac_notification("📥 Server File Auto-Pulled", msg)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Notified pull: {total_pulled}")

            if total_pushed:
                count = len(total_pushed)
                msg = f"Uploaded {count} file(s) to server:\n" + "\n".join(total_pushed[:3])
                if count > 3:
                    msg += f"\n...and {count - 3} more"
                send_mac_notification("📤 Local File Auto-Pushed", msg)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Notified push: {total_pushed}")

        except Exception as e:
            print(f"Error in auto-sync iteration: {e}")

        sys.stdout.flush()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
