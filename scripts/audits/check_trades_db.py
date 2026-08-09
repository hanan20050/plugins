import sqlite3

conn = sqlite3.connect("Shopkeepers/trade-logs/trades.db")
cursor = conn.cursor()

print("--- RECENT 50 TRADES IN TRADES.DB ---")
cursor.execute("SELECT timestamp, player_name, item_1_type, item_1_amount, item_2_type, item_2_amount, result_item_type, result_item_amount FROM trade ORDER BY timestamp DESC LIMIT 50;")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\n--- TRADES INVOLVING DIAMOND / NETHERITE / EMERALD BLOCK ---")
cursor.execute("""
SELECT timestamp, player_name, item_1_type, item_1_amount, item_2_type, item_2_amount, result_item_type, result_item_amount 
FROM trade 
WHERE item_1_type LIKE '%diamond%' OR item_2_type LIKE '%diamond%' OR result_item_type LIKE '%diamond%'
   OR item_1_type LIKE '%netherite%' OR item_2_type LIKE '%netherite%' OR result_item_type LIKE '%netherite%'
   OR item_1_type LIKE '%emerald_block%' OR item_2_type LIKE '%emerald_block%' OR result_item_type LIKE '%emerald_block%'
ORDER BY timestamp DESC;
""")
rows = cursor.fetchall()
print(f"Total trades found: {len(rows)}")
for row in rows:
    print(row)

conn.close()
