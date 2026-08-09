import re
import os
import sys

SAVE_PATH = "Shopkeepers/data/save.yml"

def double_prices():
    if not os.path.exists(SAVE_PATH):
        print(f"Error: {SAVE_PATH} not found.")
        sys.exit(1)

    with open(SAVE_PATH, "r") as f:
        content = f.read()

    # Make backup
    with open(SAVE_PATH + ".bak_books", "w") as f:
        f.write(content)

    # Locate Shopkeeper 6 block
    match = re.search(r"(\n'6':\s*\n(?:(?!\n'\d+':).)*)", content, re.DOTALL)
    if not match:
        print("Error: Shopkeeper 6 not found in save.yml")
        sys.exit(1)

    sk6_block = match.group(1)
    original_sk6 = sk6_block

    # Double item1 (and item2 if present) count in recipes inside SK6 block
    def update_item_block(m):
        item_prefix = m.group(1) # item1: or item2: header block up to count:
        count = int(m.group(2))
        return f"{item_prefix}{count * 2}"

    # Only double counts inside item1 and item2 blocks (not resultItem)
    updated_sk6 = re.sub(
        r"((?:item1|item2):\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*minecraft:[a-z_]+\s*\n\s*count:\s*)(\d+)",
        update_item_block,
        sk6_block
    )

    content = content.replace(original_sk6, updated_sk6)

    with open(SAVE_PATH, "w") as f:
        f.write(content)

    print("Successfully doubled all trade item costs in Shopkeeper 6 (Enchanted Book Emporium).")

if __name__ == "__main__":
    double_prices()
