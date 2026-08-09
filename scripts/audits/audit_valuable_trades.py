import re
import sqlite3

print("=== DEEP AUDIT OF ALL SHOPKEEPERS TRADES (save.yml) ===")
with open("Shopkeepers/data/save.yml", "r") as f:
    content = f.read()

shops = re.split(r'\n(\'?\d+\'?):\n', content)

trades_summary = []

for i in range(1, len(shops), 2):
    shop_id = shops[i].strip("'")
    shop_body = shops[i+1]
    
    name_m = re.search(r'name:\s*[\'\"]?(.*?)[\'\"]?\n', shop_body)
    shop_name = name_m.group(1) if name_m else "Unknown"
    
    recipes = re.split(r'\n\s{4}(\'\d+\'|\d+):\n', shop_body)
    for r_idx in range(1, len(recipes), 2):
        rec_id = recipes[r_idx].strip("'")
        rec_body = recipes[r_idx+1]
        
        res_m = re.search(r'resultItem:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)
        i1_m = re.search(r'item1:.*?\n\s+DataVersion:.*?\n\s+id:\s*(minecraft:\w+)\n\s+count:\s*(\d+)', rec_body, re.DOTALL)
        
        res_id = res_m.group(1) if res_m else ""
        res_cnt = int(res_m.group(2)) if res_m else 0
        
        i1_id = i1_m.group(1) if i1_m else ""
        i1_cnt = int(i1_m.group(2)) if i1_m else 0
        
        trades_summary.append((shop_id, shop_name, rec_id, i1_cnt, i1_id, res_cnt, res_id))

print(f"Total trades parsed: {len(trades_summary)}")

# Check for diamond trades
print("\n--- ALL DIAMOND RELATED TRADES ---")
for t in trades_summary:
    if "diamond" in t[4] or "diamond" in t[6]:
        print(f"Shop #{t[0]} ({t[1]}) Trade #{t[2]}: {t[3]}x {t[4]}  -->  {t[5]}x {t[6]}")

# Check for netherite trades
print("\n--- ALL NETHERITE RELATED TRADES ---")
for t in trades_summary:
    if "netherite" in t[4] or "netherite" in t[6]:
        print(f"Shop #{t[0]} ({t[1]}) Trade #{t[2]}: {t[3]}x {t[4]}  -->  {t[5]}x {t[6]}")

# Check for emerald / emerald block trades
print("\n--- ALL EMERALD BLOCK RELATED TRADES ---")
for t in trades_summary:
    if "emerald_block" in t[4] or "emerald_block" in t[6]:
        print(f"Shop #{t[0]} ({t[1]}) Trade #{t[2]}: {t[3]}x {t[4]}  -->  {t[5]}x {t[6]}")

print("\n=== TRADE DATABASE LOG ANALYSIS (trades.db) ===")
try:
    conn = sqlite3.connect("Shopkeepers/trade-logs/trades.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(trade);")
    columns = [col[1] for col in cursor.fetchall()]
    print("Table columns:", columns)
    
    cursor.execute("SELECT * FROM trade WHERE item1_id LIKE '%diamond%' OR item1_id LIKE '%netherite%' OR result_id LIKE '%diamond%' OR result_id LIKE '%netherite%' ORDER BY timestamp DESC LIMIT 50;")
    rows = cursor.fetchall()
    print(f"\nRecent 50 diamond/netherite transactions from database:")
    for row in rows:
        print(row)
    conn.close()
except Exception as e:
    print("Database error:", e)
