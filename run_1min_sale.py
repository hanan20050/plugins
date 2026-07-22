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
send_command('tellraw @a ["",{"text":"   🚨 1-MINUTE FLASH SALE STARTED! 50% OFF ALL SHOPS! 🚨","color":"gold","bold":true}]')
send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')

# 2. Countdown loop every 10 seconds (60s down to 10s)
for remaining in range(60, 0, -10):
    if remaining == 60:
        send_command('tellraw @a ["",{"text":"⏳ FLASH SALE TIMER: ","color":"yellow","bold":true},{"text":"60 SECONDS REMAINING!","color":"red","bold":true}]')
    elif remaining == 50:
        send_command('tellraw @a ["",{"text":"⏳ FLASH SALE TIMER: ","color":"yellow","bold":true},{"text":"50 SECONDS REMAINING!","color":"gold","bold":true}]')
    elif remaining == 40:
        send_command('tellraw @a ["",{"text":"⏳ FLASH SALE TIMER: ","color":"yellow","bold":true},{"text":"40 SECONDS REMAINING!","color":"gold","bold":true}]')
    elif remaining == 30:
        send_command('tellraw @a ["",{"text":"⏳ FLASH SALE TIMER: ","color":"yellow","bold":true},{"text":"30 SECONDS REMAINING!","color":"gold","bold":true}]')
    elif remaining == 20:
        send_command('tellraw @a ["",{"text":"⏳ FLASH SALE TIMER: ","color":"yellow","bold":true},{"text":"20 SECONDS REMAINING!","color":"red","bold":true}]')
    elif remaining == 10:
        send_command('tellraw @a ["",{"text":"⏳ FLASH SALE TIMER: ","color":"yellow","bold":true},{"text":"10 SECONDS REMAINING! HURRY!","color":"red","bold":true}]')
    
    time.sleep(10)

# 3. Restore pre-discount prices
shutil.copyfile("Shopkeepers/data/save_backup_prediscount.yml", "Shopkeepers/data/save.yml")

# 4. Sync & Reload
subprocess.run(["python3", "sync.py", "push", "Shopkeepers/data/save.yml"], capture_output=True)
send_command('shopkeeper reload')

# 5. Final Expired Announcement
send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')
send_command('tellraw @a ["",{"text":"   🛑 1-MINUTE FLASH SALE EXPIRED! ALL PRICES RESTORED! 🛑","color":"gold","bold":true}]')
send_command('tellraw @a ["",{"text":"=======================================","color":"dark_purple","bold":true}]')

print("1-Minute Flash Sale completed and prices restored!")
