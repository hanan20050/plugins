#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib.request
import urllib.error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables from .env
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    CONFIG[parts[0].strip()] = parts[1].strip()

TOKEN = CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = CONFIG.get("EXAROTON_SERVER_ID")

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

def api_request(endpoint, method="GET", data=None):
    url = f"https://api.exaroton.com/v1{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode("utf-8")

    try:
        with urllib.request.urlopen(req) as res:
            body = res.read().decode("utf-8")
            if not body:
                return {"success": True}
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            print(f"API Error ({e.code}): {err_json.get('error', 'Unknown error')}")
        except Exception:
            print(f"HTTP Error ({e.code}): {e.reason}")
        return None
    except Exception as e:
        print(f"Error making API request: {e}")
        return None

def get_server_status():
    res = api_request(f"/servers/{SERVER_ID}")
    if res and res.get("success"):
        server_data = res.get("data", {})
        status_code = server_data.get("status")
        return status_code, STATUS_MAP.get(status_code, f"UNKNOWN ({status_code})")
    return None, "UNKNOWN"

def send_email(subject, body):
    smtp_server = CONFIG.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port_str = CONFIG.get("SMTP_PORT", "587")
    username = CONFIG.get("SMTP_USERNAME")
    password = CONFIG.get("SMTP_PASSWORD")
    recipient = CONFIG.get("NOTIFICATION_EMAIL")
    
    if not all([username, password, recipient]):
        print("Error: SMTP_USERNAME, SMTP_PASSWORD, and NOTIFICATION_EMAIL must be set in .env")
        return False

    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        print(f"Invalid SMTP_PORT: {smtp_port_str}")
        return False

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print(f"Connecting to SMTP server {smtp_server}:{smtp_port}...")
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(username, password)
        server.sendmail(username, recipient, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient}!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def main():
    if not TOKEN or not SERVER_ID:
        print("Error: EXAROTON_TOKEN or EXAROTON_SERVER_ID not found in .env")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--test-email":
        print("Testing email notification configuration...")
        test_subject = "Exaroton Server Notification Test"
        test_body = "This is a test email from your Exaroton Server Monitor script."
        success = send_email(test_subject, test_body)
        if success:
            print("Test email sent successfully! Your settings are correct.")
        else:
            print("Test email failed. Please check your SMTP settings in .env.")
        sys.exit(0 if success else 1)

    print("Starting Exaroton Server Monitor...")
    print(f"Monitoring Server ID: {SERVER_ID}")
    
    # Get initial status
    last_code, last_status = get_server_status()
    print(f"Initial server status: {last_status}")

    poll_interval = 30  # seconds
    
    while True:
        try:
            time.sleep(poll_interval)
            current_code, current_status = get_server_status()
            
            if current_code is None:
                continue  # Skip if API request failed

            if current_code != last_code:
                print(f"Server status changed: {last_status} -> {current_status}")
                
                # Check transition to ONLINE (status code 1)
                if current_code == 1:
                    subject = "Minecraft Server is ONLINE!"
                    body = f"Your Minecraft server (ID: {SERVER_ID}) is now ONLINE and ready for players!"
                    send_email(subject, body)
                
                last_code = current_code
                last_status = current_status
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"Unexpected error in monitor loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
