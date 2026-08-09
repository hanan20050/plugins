#!/usr/bin/env python3
"""
check_all_chests_report.py
--------------------------
Scans all chest block locations across WorldGuard player regions and world coordinates,
queries live block data via Exaroton API console commands, parses SNBT item NBT,
and formats a clean, human-readable report.

Outputs report to console and saves to `chest_contents_report.txt` and `chest_contents_report.json`.
"""

import os
import sys
import json
import re
import time
import subprocess
from datetime import datetime

# Load environment credentials
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

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN")
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID")

if not TOKEN or not SERVER_ID:
    print("Error: EXAROTON_TOKEN or EXAROTON_SERVER_ID missing.")
    sys.exit(1)

# SNBT Parser for Minecraft item NBT data
def parse_snbt(s):
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c in "{}[],:":
            tokens.append((c, c))
            i += 1
            continue
        if c == '"':
            i += 1
            start = i
            val = []
            while i < len(s):
                if s[i] == '\\' and i + 1 < len(s):
                    val.append(s[i+1])
                    i += 2
                elif s[i] == '"':
                    break
                else:
                    val.append(s[i])
                    i += 1
            tokens.append(("STRING", "".join(val)))
            i += 1
            continue

        start = i
        while i < len(s) and s[i] not in " \t\r\n{}[],:\"":
            i += 1
        raw = s[start:i]
        if re.match(r"^-?\d+b$", raw, re.I):
            tokens.append(("INT", int(raw[:-1])))
        elif re.match(r"^-?\d+s$", raw, re.I):
            tokens.append(("INT", int(raw[:-1])))
        elif re.match(r"^-?\d+l$", raw, re.I):
            tokens.append(("INT", int(raw[:-1])))
        elif re.match(r"^-?\d+f$", raw, re.I):
            tokens.append(("FLOAT", float(raw[:-1])))
        elif re.match(r"^-?\d+d$", raw, re.I):
            tokens.append(("FLOAT", float(raw[:-1])))
        elif re.match(r"^-?\d+\.\d+$", raw):
            tokens.append(("FLOAT", float(raw)))
        elif re.match(r"^-?\d+$", raw):
            tokens.append(("INT", int(raw)))
        elif raw in ("true", "1b"):
            tokens.append(("BOOL", True))
        elif raw in ("false", "0b"):
            tokens.append(("BOOL", False))
        else:
            tokens.append(("IDENT", raw))

    idx = 0
    def peek():
        return tokens[idx] if idx < len(tokens) else (None, None)
    def consume(expected=None):
        nonlocal idx
        t = peek()
        if expected and t[0] != expected and t[1] != expected:
            raise ValueError(f"Expected {expected} but got {t}")
        idx += 1
        return t[1]

    def parse_value():
        t, val = peek()
        if t == "{":
            return parse_compound()
        elif t == "[":
            return parse_list()
        else:
            consume()
            return val

    def parse_compound():
        consume("{")
        res = {}
        while True:
            t, val = peek()
            if t == "}":
                consume("}")
                break
            key = consume()
            consume(":")
            val = parse_value()
            res[key] = val
            t, val = peek()
            if t == ",":
                consume(",")
            elif t == "}":
                pass
            else:
                raise ValueError(f"Expected , or }} but got {t}")
        return res

    def parse_list():
        consume("[")
        t, val = peek()
        if t == "IDENT" and idx + 1 < len(tokens) and tokens[idx+1][0] == ";":
            consume()
            consume(";")
        res = []
        while True:
            t, val = peek()
            if t == "]":
                consume("]")
                break
            val = parse_value()
            res.append(val)
            t, val = peek()
            if t == ",":
                consume(",")
            elif t == "]":
                pass
            else:
                raise ValueError(f"Expected , or ] but got {t}")
        return res

    return parse_value()

def send_command(cmd):
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/command/"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-X", "POST", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"command": cmd})
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    return res.stdout

def get_logs():
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/logs"
    curl_cmd = [
        "curl", "-s",
        "--resolve", "api.exaroton.com:443:104.26.12.211",
        "-H", f"Authorization: Bearer {TOKEN}",
        url
    ]
    res = subprocess.run(curl_cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
        if data.get("success"):
            return data.get("data", {}).get("content", "")
    except Exception as e:
        pass
    return ""

def get_block_data(x, y, z):
    send_command(f"data get block {x} {y} {z}")
    pattern = rf"{x},\s*{y},\s*{z}\s+has\s+the\s+following\s+block\s+data:\s*(\{{.*\}})"
    for _ in range(4):
        time.sleep(1.5)
        logs = get_logs()
        for line in reversed(logs.splitlines()):
            m = re.search(pattern, line)
            if m:
                return m.group(1)
    return None

def load_chest_coordinates():
    # Primary candidate coordinates from prior scans and region mapping
    coords = [
        (1270, 67, -219), (1270, 66, -219), (1270, 65, -219),
        (1270, 67, -218), (1270, 66, -218), (1270, 65, -218),
        (1270, 67, -216), (1270, 66, -216), (1270, 65, -216),
        (1270, 67, -214), (1270, 66, -214), (1270, 65, -214),
        (1245, 63, -198), (1245, 64, -200), (1245, 63, -199),
        (1247, 67, -198), (1245, 63, -200), (1244, 67, -199),
        (1116, 65, -156), (1270, 65, -217)
    ]
    
    # Load additional populated chests from `all_world_chests.json` if available
    json_path = os.path.join(os.path.dirname(__file__), "all_world_chests.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                all_chests = json.load(f)
                for c in all_chests:
                    if c.get("items_count", 0) > 0:
                        pt = (c["x"], c["y"], c["z"])
                        if pt not in coords:
                            coords.append(pt)
        except Exception:
            pass
    return coords

def main():
    coords = load_chest_coordinates()
    print(f"Scanning {len(coords)} chest locations on Exaroton server...")
    
    report_lines = []
    report_lines.append("=== LIVE CHEST INVENTORY CONTENTS REPORT ===")
    report_lines.append(f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total Locations Checked: {len(coords)}\n")
    
    json_output = []

    for x, y, z in coords:
        raw_snbt = get_block_data(x, y, z)
        chest_entry = {
            "location": {"x": x, "y": y, "z": z},
            "items": []
        }
        
        report_lines.append(f"CHEST AT POSITION ({x}, {y}, {z}):")
        if not raw_snbt:
            report_lines.append("  [Block data unavailable or non-chest block]\n")
            json_output.append(chest_entry)
            continue

        try:
            parsed = parse_snbt(raw_snbt)
            items = parsed.get("Items", [])
            if not items:
                report_lines.append("  [Empty Chest / No items]\n")
            else:
                for item in items:
                    slot = item.get("Slot", 0)
                    item_id = item.get("id", "unknown")
                    count = item.get("count", 1)
                    comp = item.get("components")
                    
                    item_data = {
                        "slot": slot,
                        "id": item_id,
                        "count": count
                    }
                    if comp:
                        item_data["components"] = comp
                    chest_entry["items"].append(item_data)

                    comp_str = f" (Components: {json.dumps(comp)})" if comp else ""
                    report_lines.append(f"  Slot {slot:2d}: {count}x {item_id}{comp_str}")
                report_lines.append("")
        except Exception as e:
            report_lines.append(f"  [Error parsing NBT: {e}]\n")
            
        json_output.append(chest_entry)

    report_text = "\n".join(report_lines)
    print("\n" + report_text)

    # Save report files
    txt_path = os.path.join(os.path.dirname(__file__), "chest_contents_report.txt")
    json_path = os.path.join(os.path.dirname(__file__), "chest_contents_report.json")
    
    with open(txt_path, "w") as f:
        f.write(report_text)
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=4)

    print(f"\n✅ Report successfully saved to:")
    print(f" - Text report: {txt_path}")
    print(f" - JSON report: {json_path}")

if __name__ == "__main__":
    main()
