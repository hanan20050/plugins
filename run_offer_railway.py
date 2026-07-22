#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
import shutil

TOKEN = os.getenv("EXAROTON_TOKEN", "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ")
SERVER_ID = os.getenv("EXAROTON_SERVER_ID", "cEuS61sZvNEFS3aB")
URL = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"

def send_command(cmd):
    curl_cmd = [
        "curl", "-s", "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", URL,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    subprocess.run(curl_cmd, capture_output=True)

def run_offer():
    # 1. Update save.yml locally to 1:1 End Stone Buyback
    with open('Shopkeepers/data/save.yml', 'r') as f:
        content = f.read()

    shop4_old = '''    '74':
      resultItem:
        DataVersion: 4903
        id: minecraft:emerald
        count: 1
      item1:
        DataVersion: 4903
        id: minecraft:end_stone
        count: 64'''

    shop4_equal = '''    '74':
      resultItem:
        DataVersion: 4903
        id: minecraft:emerald
        count: 1
      item1:
        DataVersion: 4903
        id: minecraft:end_stone
        count: 32'''

    if shop4_old in content:
        content = content.replace(shop4_old, shop4_equal)
        with open('Shopkeepers/data/save.yml', 'w') as f:
            f.write(content)

    # 2. Push & Reload
    subprocess.run(["python3", "sync.py", "push", "Shopkeepers/data/save.yml"], capture_output=True)
    send_command('shopkeeper reload')

    # 3. Initial Announcement
    send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')
    send_command('tellraw @a ["",{"text":"  💎 RAILWAY AUTOMATED OFFER: 100% END STONE BUYBACK (3 MIN)! 💎","color":"gold","bold":true}]')
    send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')
    send_command('tellraw @a ["",{"text":"• Sell Rate: ","color":"yellow"},{"text":"32 End Stone = 1 Emerald (100% Full Value!)","color":"green","bold":true}]')

    total_seconds = 180
    interval = 10

    # 4. Countdown loop every 10 seconds
    for passed in range(10, total_seconds + 1, interval):
        time.sleep(interval)
        remaining = total_seconds - passed
        mins_p, secs_p = divmod(passed, 60)
        mins_r, secs_r = divmod(remaining, 60)
        
        passed_str = f"{mins_p}m {secs_p}s" if mins_p > 0 else f"{secs_p}s"
        rem_str = f"{mins_r}m {secs_r}s" if mins_r > 0 else f"{secs_r}s"
        
        if remaining > 0:
            send_command(f'tellraw @a ["",{{\"text\":\"⏳ END STONE OFFER: \",\"color\":\"yellow\",\"bold\":true}},{{\"text\":\"{passed_str} Passed\",\"color\":\"gray\"}},{{\"text\":\" | \",\"color\":\"dark_gray\"}},{{\"text\":\"{rem_str} Left\",\"color\":\"red\",\"bold\":true}}]')

    # 5. Restore original save.yml
    if os.path.exists("Shopkeepers/data/save_backup_endstone.yml"):
        shutil.copyfile("Shopkeepers/data/save_backup_endstone.yml", "Shopkeepers/data/save.yml")
    else:
        content = content.replace(shop4_equal, shop4_old)
        with open('Shopkeepers/data/save.yml', 'w') as f:
            f.write(content)

    # 6. Push & Reload
    subprocess.run(["python3", "sync.py", "push", "Shopkeepers/data/save.yml"], capture_output=True)
    send_command('shopkeeper reload')

    # 7. Final Expired Announcement
    send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')
    send_command('tellraw @a ["",{"text":"   🛑 END STONE 100% BUYBACK OFFER EXPIRED! 🛑","color":"gold","bold":true}]')
    send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')

    print("Railway End Stone Offer completed successfully!")

if __name__ == "__main__":
    run_offer()
