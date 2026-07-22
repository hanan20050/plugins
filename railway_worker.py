#!/usr/bin/env python3
import os
import sys
import time
import traceback
import subprocess
from datetime import datetime

# Import existing scripts safely
import save_player_messages
import apply_house_upgrades
import notify_manan_farm
import demo_test_messaging

# Environment / Credentials Fallback
EXAROTON_TOKEN = os.getenv("EXAROTON_TOKEN", "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ")
EXAROTON_SERVER_ID = os.getenv("EXAROTON_SERVER_ID", "cEuS61sZvNEFS3aB")
os.environ["EXAROTON_TOKEN"] = EXAROTON_TOKEN
os.environ["EXAROTON_SERVER_ID"] = EXAROTON_SERVER_ID

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "1"))

def run_task(name, func):
    """Executes a function and logs exceptions without crashing the main loop."""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running task: {name}...")
        func()
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Exception in task {name}: {e}")
        traceback.print_exc()

def main():
    print("=" * 60)
    print("Railway Python Always-On Worker Started")
    print(f"Polling Interval: {POLL_INTERVAL} seconds")
    print("=" * 60)
    sys.stdout.flush()

    # Run demo test messaging on Railway start
    run_task("Railway Demo Messaging Test", demo_test_messaging.main)

    while True:
        try:
            # 1. Save player messages continuously
            run_task("Save Player Messages", save_player_messages.main)

            # 2. Process house trade upgrades
            run_task("Apply House Upgrades", apply_house_upgrades.main)

            # 3. Check player join notifications
            run_task("Notify Manan Farm", notify_manan_farm.main)

        except Exception as e:
            print(f"Error in main loop iteration: {e}")
            traceback.print_exc()

        sys.stdout.flush()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
