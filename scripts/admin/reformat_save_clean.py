#!/usr/bin/env python3
import os
import re

SAVE_PATH = 'Shopkeepers/data/save.yml'
BACKUP_PATH = 'Shopkeepers/data/save_backup_prediscount.yml'

def main():
    with open(SAVE_PATH, 'r') as f:
        save_content = f.read()

    with open(BACKUP_PATH, 'r') as f:
        backup_content = f.read()

    # Extract Shopkeeper 6 block from backup if not present
    m6 = re.search(r'(\n\'6\':\s*\n(?:(?!\n\'\d+\':|\nsnapshots:).)*)', backup_content, re.DOTALL)
    if not m6:
        print("Error: Could not extract Shopkeeper 6 from backup.")
        return

    sk6_block = m6.group(1)

    # Convert any netherite_ingot trades in SK6 to Emeralds / Emerald Blocks
    sk6_block = re.sub(
        r'\'27\':\s*\n\s*resultItem:((?:(?!\'28\':).)*)item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*minecraft:netherite_ingot\s*\n\s*count:\s*2',
        '\'27\':\n      resultItem:\\1item1:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 64\n      item2:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 64',
        sk6_block,
        flags=re.DOTALL
    )

    sk6_block = re.sub(
        r'\'28\':\s*\n\s*resultItem:((?:(?!\'29\':).)*)item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*minecraft:netherite_ingot\s*\n\s*count:\s*2',
        '\'28\':\n      resultItem:\\1item1:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 64\n      item2:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 64',
        sk6_block,
        flags=re.DOTALL
    )

    sk6_block = re.sub(
        r'\'29\':\s*\n\s*resultItem:((?:(?!\n\s*snapshots:|\Z).)*)item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*minecraft:netherite_ingot\s*\n\s*count:\s*3',
        '\'29\':\n      resultItem:\\1item1:\n        DataVersion: 4903\n        id: minecraft:emerald_block\n        count: 21\n      item2:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 3',
        sk6_block,
        flags=re.DOTALL
    )

    # Remove any existing 'snapshots: []' or trailing text from save_content
    cleaned_save = re.sub(r'\nsnapshots:.*', '', save_content, flags=re.DOTALL)
    cleaned_save = re.sub(r'\n\'6\':.*', '', cleaned_save, flags=re.DOTALL)

    # Append Shopkeeper 6 before snapshots
    final_content = cleaned_save.rstrip() + sk6_block.rstrip() + '\nsnapshots: []\n'

    with open(SAVE_PATH, 'w') as f:
        f.write(final_content)

    print("save.yml successfully updated with Shopkeeper 6 before snapshots.")

if __name__ == '__main__':
    main()
