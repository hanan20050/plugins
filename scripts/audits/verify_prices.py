import os
import re

buy_prices = {}
sell_prices = {}

sections_dir = "EconomyShopGUI/sections"
for root, dirs, files in os.walk(sections_dir):
    for f in files:
        if f.endswith(".yml"):
            p = os.path.join(root, f)
            with open(p) as fh:
                content = fh.read()
                
            items = re.findall(r"material:\s*([A-Z0-9_]+)[\s\S]*?buy:\s*([0-9.]+)[\s\S]*?sell:\s*([0-9.]+)", content)
            for mat, buy, sell in items:
                mat_id = "minecraft:" + mat.lower()
                b = float(buy)
                s = float(sell)
                buy_prices[mat_id] = b
                sell_prices[mat_id] = s

print("==========================================================================")
print(f"  ECONOMYSHOPGUI PRICE LIST AUDIT ({len(buy_prices)} Items Configured)  ")
print("==========================================================================")
print(f"{'Item Material':<30} | {'Buy Price ($)':<15} | {'Sell Price ($)':<15} | {'Margin'}")
print("-" * 80)

for mat in sorted(buy_prices.keys()):
    b = buy_prices[mat]
    s = sell_prices[mat]
    ratio = b / s if s > 0 else 0
    print(f"{mat:<30} | ${b:<14.2f} | ${s:<14.2f} | {ratio:.2f}x")
