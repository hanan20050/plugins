#!/usr/bin/env python3
import re
import os
import sys

SAVE_PATH = 'Shopkeepers/data/save.yml'

def main():
    if not os.path.exists(SAVE_PATH):
        print(f"Error: {SAVE_PATH} not found.")
        sys.exit(1)

    with open(SAVE_PATH, 'r') as f:
        content = f.read()

    # Split top-level blocks by shopkeeper keys (e.g. '1':, '2':, '3':, '4':, '5':)
    sk_blocks = re.split(r'\n(?=\'\d+\':)', content)

    cleaned_blocks = []

    for block in sk_blocks:
        if not block.strip():
            continue

        m_id = re.match(r'^\s*\'(\d+)\':', block)
        if not m_id:
            cleaned_blocks.append(block)
            continue

        sk_id = m_id.group(1)
        m_name = re.search(r'name:\s*([^\n]+)', block)
        sk_name = m_name.group(1) if m_name else 'Unknown'

        if sk_id == '5':
            # Money Exchange shopkeeper - keep netherite trades intact
            cleaned_blocks.append(block)
            continue

        # For shops other than 5:
        # 1. Check if any recipe uses netherite_ingot
        # If it's Shop 3 Trade 8 (Big Plot Expansion), convert item1: netherite_ingot (2) -> item1: emerald (64), item2: emerald (64)
        # If it's an exchange trade selling or buying netherite_ingot, remove it!

        rec_start_match = re.search(r'(\n\s+recipes:\s*\n)', block)
        if not rec_start_match:
            cleaned_blocks.append(block)
            continue

        header_part = block[:rec_start_match.end()]
        remainder = block[rec_start_match.end():]

        snap_match = re.search(r'(\n\s+snapshots:.*|\Z)', remainder, re.DOTALL)
        if snap_match and snap_match.group(1):
            tail_part = snap_match.group(1)
            recipes_part = remainder[:snap_match.start()]
        else:
            tail_part = ''
            recipes_part = remainder

        # Extract recipe chunks
        recipe_chunks = re.findall(r'(\s{4}\'\d+\':\s*\n(?:(?!\s{4}\'\d+\':).)*)', recipes_part, re.DOTALL)

        kept_chunks = []
        for r_chunk in recipe_chunks:
            if 'id: minecraft:netherite_ingot' in r_chunk:
                # Check if it's Big Plot Expansion certificate trade
                if 'Big Plot Expansion' in r_chunk:
                    print(f"[Shopkeeper {sk_id} ({sk_name})] Converting Netherite Ingot cost to 2x 64 Emeralds for Big Plot Expansion certificate.")
                    # Replace item1 netherite_ingot count 2 with item1 emerald 64 + item2 emerald 64
                    new_r_chunk = re.sub(
                        r'item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*minecraft:netherite_ingot\s*\n\s*count:\s*2',
                        'item1:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 64\n      item2:\n        DataVersion: 4903\n        id: minecraft:emerald\n        count: 64',
                        r_chunk
                    )
                    kept_chunks.append(new_r_chunk)
                else:
                    print(f"[Shopkeeper {sk_id} ({sk_name})] Removing netherite_ingot trade.")
            else:
                kept_chunks.append(r_chunk)

        # Re-index kept chunks
        reindexed_chunks = []
        for idx, r_chunk in enumerate(kept_chunks, start=1):
            # Replace top recipe key, e.g. "    '34':" -> "    '12':"
            reindexed = re.sub(r'^\s{4}\'\d+\':', f'    \'{idx}\':', r_chunk, count=1)
            reindexed_chunks.append(reindexed)

        new_block = header_part + ''.join(reindexed_chunks) + tail_part
        cleaned_blocks.append(new_block)

    final_content = '\n'.join(cleaned_blocks)

    with open(SAVE_PATH, 'w') as f:
        f.write(final_content)

    print("save.yml updated successfully.")

if __name__ == '__main__':
    main()
