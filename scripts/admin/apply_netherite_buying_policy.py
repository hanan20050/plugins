#!/usr/bin/env python3
import os
import sys
import re

SAVE_PATH = 'Shopkeepers/data/save.yml'
BACKUP_PATH = 'Shopkeepers/data/save_backup_prediscount.yml'

def main():
    if not os.path.exists(BACKUP_PATH):
        print(f"Error: {BACKUP_PATH} not found.")
        sys.exit(1)

    with open(BACKUP_PATH, 'r') as f:
        content = f.read()

    # Split top-level shopkeeper blocks
    # Note: top level keys in save_backup_prediscount.yml are '1':, '5':, '6':, '2':, '4':, etc.
    sk_blocks = re.split(r'\n(?=\'\d+\':)', content)

    cleaned_blocks = []

    for block in sk_blocks:
        if not block.strip():
            continue

        m_id = re.match(r'^\s*\'(\d+)\':', block)
        if not m_id:
            continue

        sk_id = m_id.group(1)
        m_name = re.search(r'name:\s*([^\n]+)', block)
        sk_name = m_name.group(1) if m_name else 'Unknown'

        # Extract header (up to recipes:)
        rec_start_match = re.search(r'(\n\s+recipes:\s*\n)', block)
        if not rec_start_match:
            cleaned_blocks.append(block.strip())
            continue

        header_part = block[:rec_start_match.end()]
        remainder = block[rec_start_match.end():]

        snap_match = re.search(r'(\n\s+snapshots:.*|\Z)', remainder, re.DOTALL)
        if snap_match and snap_match.group(1):
            recipes_part = remainder[:snap_match.start()]
        else:
            recipes_part = remainder

        # Extract recipe chunks (4 spaces indent, e.g. "    '1':\n")
        recipe_chunks = re.findall(r'(\s{4}\'\d+\':\s*\n(?:(?!\s{4}\'\d+\':).)*)', recipes_part, re.DOTALL)

        kept_chunks = []
        for r_chunk in recipe_chunks:
            res_id_match = re.search(r'resultItem:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*([^\n]+)', r_chunk)
            res_id = res_id_match.group(1).strip() if res_id_match else None

            # Policy: If sk_id != '5' and resultItem is netherite_ingot (shop is selling netherite ingot to player) -> REMOVE
            if sk_id != '5' and res_id == 'minecraft:netherite_ingot':
                print(f"[Shopkeeper {sk_id} ({sk_name})] Removing trade selling netherite_ingot.")
                continue

            kept_chunks.append(r_chunk)

        # Re-index kept recipe chunks sequentially '1', '2', '3'...
        reindexed_chunks = []
        for idx, r_chunk in enumerate(kept_chunks, start=1):
            reindexed = re.sub(r'^\s{4}\'\d+\':', f'    \'{idx}\':', r_chunk, count=1)
            reindexed_chunks.append(reindexed)

        new_block = header_part + ''.join(reindexed_chunks)
        cleaned_blocks.append(new_block.rstrip())

    final_content = '\n'.join(cleaned_blocks) + '\nsnapshots: []\n'

    with open(SAVE_PATH, 'w') as f:
        f.write(final_content)

    print("save.yml successfully updated with Netherite buying policy.")

if __name__ == '__main__':
    main()
