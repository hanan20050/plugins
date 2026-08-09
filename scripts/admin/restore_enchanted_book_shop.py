#!/usr/bin/env python3
import os
import sys
import re

SAVE_PATH = 'Shopkeepers/data/save.yml'
BACKUP_PATH = 'Shopkeepers/data/save_backup_prediscount.yml'

def main():
    if not os.path.exists(SAVE_PATH) or not os.path.exists(BACKUP_PATH):
        print("Error: Required files missing.")
        sys.exit(1)

    with open(BACKUP_PATH, 'r') as f:
        backup_content = f.read()

    # Extract Shopkeeper ID 6 from backup
    m = re.search(r'(\n\'6\':\s*\n(?:(?!\n\'\d+\':).)*)', backup_content, re.DOTALL)
    if not m:
        print("Error: Shopkeeper 6 not found in backup.")
        sys.exit(1)

    sk6_block = m.group(1)

    # Convert any netherite_ingot payments in Shop 6 to Emeralds / Emerald Blocks
    # Trade 27: Swift Sneak 3 (2 netherite ingots = 128 emeralds -> item1: emerald 64, item2: emerald 64)
    # Trade 28: Soul Speed 3 (2 netherite ingots = 128 emeralds -> item1: emerald 64, item2: emerald 64)
    # Trade 29: Wind Burst 3 (3 netherite ingots = 192 emeralds -> item1: emerald_block 21, item2: emerald 3)

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
        r'\'29\':\s*\n\s*resultItem:((?:(?!\n\s*snapshots:).)*)item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*minecraft:netherite_ingot\s*\n\s*count:\s*3',
        '\'29\':\n      resultItem:\\1item1:\n        DataVersion: 4903\n        id: minecraft:emerald_block\n        count: 21\n      item2:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 3',
        sk6_block,
        flags=re.DOTALL
    )

    with open(SAVE_PATH, 'r') as f:
        save_content = f.read()

    # Check if top-level '6': already exists in save_content
    if re.search(r'^\'6\':', save_content, re.MULTILINE):
        print("Shopkeeper 6 already present in save.yml.")
        return

    # Insert sk6_block right before 'snapshots:' line or at end
    if 'snapshots:' in save_content:
        idx = save_content.rfind('snapshots:')
        new_save_content = save_content[:idx] + sk6_block.lstrip('\n') + '\n' + save_content[idx:]
    else:
        new_save_content = save_content + '\n' + sk6_block

    with open(SAVE_PATH, 'w') as f:
        f.write(new_save_content)

    print("Shopkeeper 6 ('Enchanted Book Emporium') successfully restored to save.yml.")

if __name__ == '__main__':
    main()
