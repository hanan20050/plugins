#!/usr/bin/env python3
"""
Exaroton Server Online Email Notifier
-------------------------------------
Monitors Exaroton server status via API.
When status changes from OFFLINE / STARTING -> ONLINE (1),
sends an email notification via SMTP (e.g. Gmail).
"""

import os
import sys
import json
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")
STATUS_FILE = os.path.join(os.path.dirname(__file__), "server_status.json")

# Status codes: 0=OFFLINE, 1=ONLINE, 2=STARTING, 3=STOPPING, 4=RESTARTING, 5=SAVING, 6=LOADING, 7=CRASHED
STATUS_NAMES = {
    0: "OFFLINE",
    1: "ONLINE",
    2: "STARTING",
    3: "STOPPING",
    4: "RESTARTING",
    5: "SAVING",
    6: "LOADING",
    7: "CRASHED",
    10: "PREPARING"
}

def get_server_status():
    if not TOKEN or not SERVER_ID:
        return None, "Missing Exaroton token or server ID"

    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "GET",
        url,
        "-H", f"Authorization: Bearer {TOKEN}"
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    if res.returncode == 0 and res.stdout:
        try:
            data = json.loads(res.stdout)
            if data.get("success"):
                server_data = data.get("data", {})
                status_code = server_data.get("status")
                server_name = server_data.get("name", "Minecraft Server")
                server_ip = server_data.get("address", "")
                return status_code, {"name": server_name, "address": server_ip}
        except Exception as e:
            print(f"Error parsing status JSON: {e}")
    return None, None

def send_startup_email(server_info):
    sender_email = os.environ.get("SENDER_EMAIL") or CONFIG.get("SENDER_EMAIL")
    sender_password = os.environ.get("EMAIL_APP_PASSWORD") or CONFIG.get("EMAIL_APP_PASSWORD")
    receiver_email = os.environ.get("RECEIVER_EMAIL") or CONFIG.get("RECEIVER_EMAIL") or sender_email
    smtp_host = os.environ.get("SMTP_HOST") or CONFIG.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT") or CONFIG.get("SMTP_PORT", "587"))

    if not sender_email or not sender_password:
        print("⚠️ SENDER_EMAIL or EMAIL_APP_PASSWORD not set. Skipping email send.")
        return False

    name = server_info.get("name", "Minecraft Server") if server_info else "Minecraft Server"
    address = server_info.get("address", "") if server_info else ""

    subject = f"🚀 Server is ONLINE: {name}"
    body = (
        f"Hello!\n\n"
        f"Your Minecraft server '{name}' is now ONLINE and ready to join!\n\n"
        f"Server Address: {address}\n\n"
        f"Happy playing!"
    )

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print(f"✅ Notification email successfully sent to {receiver_email}!")
        return True
    except Exception as e:
        print(f"❌ Failed to send notification email: {e}")
        return False

def check_and_notify():
    status_code, server_info = get_server_status()
    if status_code is None:
        return

    status_name = STATUS_NAMES.get(status_code, f"UNKNOWN({status_code})")
    
    last_status = None
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                saved = json.load(f)
                last_status = saved.get("status")
        except Exception:
            last_status = None

    print(f"Server Status Check: current={status_name} (code {status_code}), last={last_status}")

    # Trigger email ONLY when transitioning from not-online -> ONLINE (1)
    if status_code == 1 and last_status != 1:
        print(f"🎉 Server status changed to ONLINE! Sending email notification...")
        send_startup_email(server_info)

    # Save current status
    with open(STATUS_FILE, "w") as f:
        json.dump({"status": status_code, "name": status_name}, f)

if __name__ == "__main__":
    check_and_notify()
