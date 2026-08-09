#!/usr/bin/env python3
"""
sync_master_prices.py

Syncs master prices from shop_prices_master.yml into EconomyShopGUI section files,
pushes updated section files to the Exaroton server via sync.py, and reloads EconomyShopGUI (sreload).
"""

import os
import sys
import re
import subprocess

def parse_simple_yaml(filepath):
    data = {"categories": {}}
    current_cat = None
    current_items = None
    
    with open(filepath, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        if indent == 2 and line.endswith(":") and not line.strip().startswith("#"):
            current_cat = stripped.rstrip(":")
            data["categories"][current_cat] = {"items": []}
            i += 1
            continue

        if current_cat:
            if stripped.startswith("section_file:"):
                sec_file = stripped.split("section_file:", 1)[1].strip().strip("'\"")
                data["categories"][current_cat]["section_file"] = sec_file
            elif stripped.startswith("- material:"):
                mat = stripped.split("- material:", 1)[1].strip()
                item_obj = {"material": mat, "buy": 0.0, "sell": 0.0}
                data["categories"][current_cat]["items"].append(item_obj)
                
                # Check next lines for buy and sell
                j = i + 1
                while j < len(lines):
                    next_l = lines[j].strip()
                    if next_l.startswith("buy:"):
                        item_obj["buy"] = float(next_l.split("buy:", 1)[1].strip())
                    elif next_l.startswith("sell:"):
                        item_obj["sell"] = float(next_l.split("sell:", 1)[1].strip())
                    elif next_l.startswith("- material:") or (len(lines[j]) - len(lines[j].lstrip(" ")) == 2 and lines[j].rstrip("\n").endswith(":")):
                        break
                    j += 1
        i += 1

    return data

def sync_master_to_sections():
    master_file = "shop_prices_master.yml"
    if not os.path.exists(master_file):
        print(f"❌ {master_file} not found!")
        return

    data = parse_simple_yaml(master_file)

    categories = data.get("categories", {})
    updated_files = set()

    for cat_key, cat_info in categories.items():
        sec_file = cat_info.get("section_file")
        items = cat_info.get("items", [])
        
        if not sec_file or not os.path.exists(sec_file):
            print(f"⚠️ Section file not found: {sec_file}")
            continue

        # Read existing section file template (header, title, slot, etc.)
        with open(sec_file, "r") as sf:
            sec_text = sf.read()

        # Extract header lines before 'items:'
        if "items:" in sec_text:
            header = sec_text.split("items:")[0].rstrip() + "\nitems:\n"
        else:
            header = sec_text.rstrip() + "\nitems:\n"

        # Format items section
        items_yaml = header
        for idx, item in enumerate(items, 1):
            buy_val = item["buy"]
            sell_val = item["sell"]
            mat_val = item["material"]
            items_yaml += f"  {idx}:\n"
            items_yaml += f"    material: {mat_val}\n"
            if buy_val > 0:
                items_yaml += f"    buy: {buy_val}\n"
            items_yaml += f"    sell: {sell_val}\n"

        with open(sec_file, "w") as sf:
            sf.write(items_yaml)

        print(f"✅ Updated {sec_file} ({len(items)} items)")
        updated_files.add(sec_file)

    # Push to server
    for uf in sorted(updated_files):
        res = subprocess.run(["python3", "sync.py", "push", uf], capture_output=True, text=True)
        print(res.stdout.strip())

    # Reload plugin
    token = open(".env").read().split("EXAROTON_TOKEN=")[1].split("\n")[0].strip()
    server_id = open(".env").read().split("EXAROTON_SERVER_ID=")[1].split("\n")[0].strip()
    
    cmd = f'curl -s --resolve api.exaroton.com:443:104.26.12.211 -X POST "https://api.exaroton.com/v1/servers/{server_id}/command/" -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d \x27{{"command": "sreload"}}\x27'
    subprocess.run(cmd, shell=True)
    print("🚀 Reloaded EconomyShopGUI (sreload) on server!")

if __name__ == "__main__":
    sync_master_to_sections()
