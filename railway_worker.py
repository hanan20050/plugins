#!/usr/bin/env python3
import os
import sys
import time
import traceback
import subprocess
from datetime import datetime

# Environment / Credentials Fallback (MUST BE BEFORE IMPORTS)
EXAROTON_TOKEN = os.getenv("EXAROTON_TOKEN", "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ")
EXAROTON_SERVER_ID = os.getenv("EXAROTON_SERVER_ID", "cEuS61sZvNEFS3aB")
os.environ["EXAROTON_TOKEN"] = EXAROTON_TOKEN
os.environ["EXAROTON_SERVER_ID"] = EXAROTON_SERVER_ID

# Import existing scripts safely
import save_player_messages
import apply_house_upgrades
import notify_server_start

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

    while True:
        try:
            # 1. Save player messages continuously
            run_task("Save Player Messages", save_player_messages.main)

            # 2. Process house trade upgrades
            run_task("Apply House Upgrades", apply_house_upgrades.main)

            # 3. Check server startup & notify
            run_task("Notify Server Start", notify_server_start.check_and_notify)

            # 4. Check single-run Railway offer trigger
            if os.path.exists("trigger_offer.flag"):
                try:
                    os.remove("trigger_offer.flag")
                except Exception:
                    pass
                import run_offer_railway
                run_task("Railway End Stone Offer", run_offer_railway.run_offer)


        except Exception as e:
            print(f"Error in main loop iteration: {e}")
            traceback.print_exc()

        sys.stdout.flush()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
