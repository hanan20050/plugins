import time
import json
import subprocess
import shutil

TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
SERVER_ID = "cEuS61sZvNEFS3aB"
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

# 1. Initial Announcement
send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')
send_command('tellraw @a ["",{"text":"  💎 SPECIAL OFFER: 100% END STONE BUYBACK (3 MIN)! 💎","color":"gold","bold":true}]')
send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')
send_command('tellraw @a ["",{"text":"• Sell Rate: ","color":"yellow"},{"text":"32 End Stone = 1 Emerald (100% Full Value!)","color":"green","bold":true}]')

total_seconds = 180
interval = 10

# 2. Countdown loop every 10 seconds (180s down to 10s)
for passed in range(10, total_seconds + 1, interval):
    time.sleep(interval)
    remaining = total_seconds - passed
    mins_p, secs_p = divmod(passed, 60)
    mins_r, secs_r = divmod(remaining, 60)
    
    passed_str = f"{mins_p}m {secs_p}s" if mins_p > 0 else f"{secs_p}s"
    rem_str = f"{mins_r}m {secs_r}s" if mins_r > 0 else f"{secs_r}s"
    
    if remaining > 0:
        send_command(f'tellraw @a ["",{{\"text\":\"⏳ END STONE OFFER: \",\"color\":\"yellow\",\"bold\":true}},{{\"text\":\"{passed_str} Passed\",\"color\":\"gray\"}},{{\"text\":\" | \",\"color\":\"dark_gray\"}},{{\"text\":\"{rem_str} Left\",\"color\":\"red\",\"bold\":true}}]')

# 3. Restore pre-event save.yml
shutil.copyfile("Shopkeepers/data/save_backup_endstone.yml", "Shopkeepers/data/save.yml")

# 4. Sync & Reload
subprocess.run(["python3", "sync.py", "push", "Shopkeepers/data/save.yml"], capture_output=True)
send_command('shopkeeper reload')

# 5. Final Expired Announcement
send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')
send_command('tellraw @a ["",{"text":"   🛑 END STONE 100% BUYBACK OFFER EXPIRED! 🛑","color":"gold","bold":true}]')
send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')

print("3-Minute End Stone Buyback completed and normal rates restored!")
