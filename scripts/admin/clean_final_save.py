#!/usr/bin/env python3
import re

SAVE_PATH = 'Shopkeepers/data/save.yml'

def clean_final():
    with open(SAVE_PATH, 'r') as f:
        text = f.read()

    blocks = re.split(r'\n(?=\'\d+\':)', text)
    seen_ids = set()
    cleaned_blocks = []

    for b in blocks:
        if not b.strip():
            continue
        m_id = re.search(r'^\s*\'(\d+)\':', b)
        if not m_id:
            cleaned_blocks.append(b)
            continue
        
        sk_id = m_id.group(1)
        if sk_id in seen_ids:
            print(f"Removing duplicate top-level block SK ID {sk_id}")
            continue
        seen_ids.add(sk_id)
        
        # Ensure block ends with '  snapshots: []\n'
        b_clean = b.strip()
        if not b_clean.endswith('snapshots: []'):
            b_clean = b_clean + '\n  snapshots: []'
        cleaned_blocks.append(b_clean + '\n')

    final_text = "\n".join(cleaned_blocks)
    if not final_text.startswith('#'):
        final_text = "# This file is not intended to be manually modified!\n\ndata-version: 4|2|4903\n" + final_text

    with open(SAVE_PATH, 'w') as f:
        f.write(final_text)

    print("Cleaned final save.yml structure!")

if __name__ == '__main__':
    clean_final()
