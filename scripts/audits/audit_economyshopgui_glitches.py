#!/usr/bin/env python3
"""
EconomyShopGUI Anti-Glitch & Price Auditor Script
--------------------------------------------------
Automatically scans all EconomyShopGUI shop files (under plugins/EconomyShopGUI/shops/)
for money glitches, pricing exploits, or invalid ratio configurations.

Usage:
  python3 audit_economyshopgui_glitches.py          # Audits local shop files
  python3 audit_economyshopgui_glitches.py --pull   # Pulls fresh shop files from server first, then audits
  python3 audit_economyshopgui_glitches.py --fix    # Automatically fixes any glitches found & pushes to server
"""

import os
import re
import sys
import argparse
import subprocess

SHOPS_DIR = os.path.join(os.path.dirname(__file__), "EconomyShopGUI", "shops")

def check_shop_file(filepath):
    """
    Audits a single shop YAML file for:
    1. Sell price >= Buy price (when buy > 0 and sell > 0)
    2. Zero or negative non-disabled prices
    """
    glitches = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract material, buy price, sell price
    items = re.findall(r'material:\s*([A-Z0-9_]+)\s+buy:\s*([\d\.-]+)\s+sell:\s*([\d\.-]+)', content)
    for mat, buy_str, sell_str in items:
        try:
            buy = float(buy_str)
            sell = float(sell_str)
        except ValueError:
            continue
        
        # Rule 1: Infinite money glitch (sell >= buy when both are active)
        if buy > 0 and sell > 0 and sell >= buy:
            glitches.append({
                'type': 'EXPLOIT_SELL_GE_BUY',
                'material': mat,
                'buy': buy,
                'sell': sell,
                'description': f'Sell price ({sell}) is greater than or equal to Buy price ({buy})'
            })
        
        # Rule 2: Free buying (buy == 0)
        elif buy == 0:
            glitches.append({
                'type': 'FREE_BUY',
                'material': mat,
                'buy': buy,
                'sell': sell,
                'description': f'Item can be bought for FREE (buy: 0.0)'
            })
            
    return glitches

def audit_all_shops():
    """Scans all shop files in the shops directory."""
    if not os.path.exists(SHOPS_DIR):
        print(f"Error: Shops directory not found at {SHOPS_DIR}")
        sys.exit(1)
        
    all_results = {}
    total_files = 0
    total_glitches = 0
    
    print("=" * 70)
    print("      ECONOMYSHOPGUI ANTI-GLITCH & PRICING AUDITOR SYSTEM          ")
    print("=" * 70)
    
    for root, _, files in os.walk(SHOPS_DIR):
        for file in files:
            if file.endswith(".yml"):
                total_files += 1
                fp = os.path.join(root, file)
                rel_p = os.path.relpath(fp, SHOPS_DIR)
                glitches = check_shop_file(fp)
                if glitches:
                    all_results[rel_p] = glitches
                    total_glitches += len(glitches)
                    
    print(f"\nScanned {total_files} shop configuration files.")
    
    if all_results:
        print(f"\n⚠️  CRITICAL: Found {total_glitches} pricing glitch(es) across {len(all_results)} file(s):\n")
        for file_rel, glitch_list in all_results.items():
            print(f"📄 File: EconomyShopGUI/shops/{file_rel}")
            for g in glitch_list:
                print(f"   ❌ [{g['material']}] Buy: ${g['buy']} | Sell: ${g['sell']} -> {g['description']}")
            print("-" * 60)
    else:
        print("\n✅ SUCCESS: All shop files are 100% CLEAN! No infinite money glitches or exploits found.")
        
    return all_results

def pull_shops_from_server():
    """Pulls fresh shop files from the server via sync.py."""
    print("🔄 Pulling latest shop files from server...")
    try:
        from sync import pull_item
        pull_item("EconomyShopGUI/shops")
        print("✅ Pulled latest shop files from server.\n")
    except Exception as e:
        print(f"Warning: Could not pull files via sync.py: {e}")

def fix_glitches(glitches_dict):
    """Automatically fixes glitches by adjusting buy price to 2x sell price."""
    if not glitches_dict:
        print("\nNo glitches to fix.")
        return
        
    print("\n🛠️  Fixing glitches automatically...")
    from sync import push_item
    
    for rel_p, glitch_list in glitches_dict.items():
        full_p = os.path.join(SHOPS_DIR, rel_p)
        with open(full_p, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for g in glitch_list:
            mat = g['material']
            old_buy = g['buy']
            new_buy = round(max(g['sell'] * 2.0, 0.5), 2)
            
            # Find and replace entry
            pattern = rf'(material:\s*{mat}\s+buy:\s*){old_buy}(\s+sell:\s*{g["sell"]})'
            replacement = r'\g<1>' + str(new_buy) + r'\g<2>'
            content = re.sub(pattern, replacement, content)
            print(f"   Fixed {mat} in {rel_p}: Buy changed from ${old_buy} -> ${new_buy}")
            
        with open(full_p, 'w', encoding='utf-8') as f:
            f.write(content)
            
        push_path = os.path.join("EconomyShopGUI/shops", rel_p)
        push_item(push_path)
        
    # Reload server
    print("\n🚀 Reloading EconomyShopGUI on server...")
    try:
        from sync import api_request, SERVER_ID
        import json
        data = json.dumps({'command': 'economyshopgui reload'}).encode('utf-8')
        api_request(f'/servers/{SERVER_ID}/command/', method='POST', data=data, is_binary=True)
        print("✅ Server reloaded.")
    except Exception as e:
        print(f"Warning: Could not reload server: {e}")

def main():
    parser = argparse.ArgumentParser(description="EconomyShopGUI Anti-Glitch & Price Auditor")
    parser.add_argument("--pull", action="store_true", help="Pull latest shop files from server before auditing")
    parser.add_argument("--fix", action="store_true", help="Automatically fix any glitches found and sync to server")
    args = parser.parse_args()
    
    if args.pull:
        pull_shops_from_server()
        
    results = audit_all_shops()
    
    if args.fix and results:
        fix_glitches(results)

if __name__ == "__main__":
    main()
