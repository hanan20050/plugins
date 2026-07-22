#!/usr/bin/env python3
import re
import os

SAVE_PATH = 'Shopkeepers/data/save.yml'

def get_base_save_content():
    """Returns save.yml from git commit c6915d0 as baseline."""
    import subprocess
    res = subprocess.run(["git", "show", "c6915d0:Shopkeepers/data/save.yml"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout:
        return res.stdout
    with open(SAVE_PATH, 'r') as f:
        return f.read()

def rebuild_save():
    content = get_base_save_content()
    currency_items = {'minecraft:emerald', 'minecraft:emerald_block', 'minecraft:netherite_ingot', 'minecraft:netherite_block'}

    # Split shopkeeper blocks cleanly by top-level shopkeeper keys ('1':, '2':, '4':, '5':)
    blocks = re.split(r'\n(?=\'\d+\':)', content)
    
    sk_data = {}
    sk_order = []

    for b in blocks:
        if not b.strip():
            continue
        m_id = re.search(r'^\s*\'(\d+)\':', b)
        if not m_id:
            continue
        sk_id = m_id.group(1)
        if sk_id in sk_data:
            continue  # Deduplicate shopkeeper IDs
        
        sk_order.append(sk_id)

        # Extract header lines up to recipes:
        rec_match = re.search(r'(\n\s+recipes:\s*\n)', b)
        if not rec_match:
            continue

        header = b[:rec_match.end()]
        body = b[rec_match.end():]

        # Extract recipes and snapshots
        rec_chunks = re.findall(r'(\s{4}\'\d+\':\s*\n(?:(?!\s{4}\'\d+\':|\s{2}snapshots:).)*)', body, re.DOTALL)

        parsed_recs = []
        for r_chunk in rec_chunks:
            i1_id_m = re.search(r'item1:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*([^\n]+)', r_chunk)
            i1_c_m = re.search(r'item1:\s*\n(?:\s*[^\n]+\n)*?\s*count:\s*(\d+)', r_chunk)

            res_id_m = re.search(r'resultItem:\s*\n\s*DataVersion:\s*\d+\s*\n\s*id:\s*([^\n]+)', r_chunk)
            res_c_m = re.search(r'resultItem:\s*\n(?:\s*[^\n]+\n)*?\s*count:\s*(\d+)', r_chunk)

            comp_m = re.search(r'components:\s*([^\n]+(?:\n\s+[^\n]+)*)', r_chunk)

            id1 = i1_id_m.group(1).strip() if i1_id_m else ''
            c1 = int(i1_c_m.group(1).strip()) if i1_c_m else 1
            id_res = res_id_m.group(1).strip() if res_id_m else ''
            c_res = int(res_c_m.group(1).strip()) if res_c_m else 1
            comp_str = comp_m.group(1).strip() if comp_m else ''

            parsed_recs.append({
                'id1': id1, 'c1': c1,
                'id_res': id_res, 'c_res': c_res,
                'comp': comp_str,
                'raw': r_chunk
            })

        sk_data[sk_id] = {
            'header': header,
            'recs': parsed_recs
        }

    # Process shopkeepers according to rules
    
    # 1. SK1: Remove dry leaves (leaf_litter), remove exchange trades, remove duplicates, sort by price
    sk1_recs = sk_data['1']['recs']
    seen1 = set()
    cleaned1 = []
    for r in sk1_recs:
        if r['id1'] == 'minecraft:leaf_litter' or r['id_res'] == 'minecraft:leaf_litter':
            continue
        if r['id1'] in currency_items and r['id_res'] in currency_items:
            continue  # exchange trade
        sig = (r['id1'], r['c1'], r['id_res'], r['c_res'], r['comp'])
        if sig in seen1:
            continue
        seen1.add(sig)
        cleaned1.append(r)

    # Sort SK1: emerald cost ascending (if item1 is emerald), then by result item id
    sk1_sorted = sorted(cleaned1, key=lambda r: (
        0 if r['id1'] != 'minecraft:emerald' else 1,
        r['c1'] if r['id1'] == 'minecraft:emerald' else 0,
        r['id_res']
    ))
    sk_data['1']['recs'] = sk1_sorted

    # 2. SK4: Remove exchange trades, remove duplicates, sort by emerald payout
    sk4_recs = sk_data['4']['recs']
    seen4 = set()
    cleaned4 = []
    for r in sk4_recs:
        if r['id1'] in currency_items and r['id_res'] in currency_items:
            continue
        sig = (r['id1'], r['c1'], r['id_res'], r['c_res'], r['comp'])
        if sig in seen4:
            continue
        seen4.add(sig)
        cleaned4.append(r)

    # Sort SK4: emerald payout ascending (if resultItem is emerald), then by item1 id
    sk4_sorted = sorted(cleaned4, key=lambda r: (
        0 if r['id_res'] != 'minecraft:emerald' else 1,
        r['c_res'] if r['id_res'] == 'minecraft:emerald' else 0,
        r['id1']
    ))
    sk_data['4']['recs'] = sk4_sorted

    # Re-assemble save.yml string strictly obeying Shopkeepers plugin format
    lines = ["# This file is not intended to be manually modified! If you want to manually edit this file anyway, ensure that the server is not running currently and that you have prepared a backup of this file.\n\ndata-version: 4|2|4903\n"]

    for sk_id in sk_order:
        header = sk_data[sk_id]['header'].strip('\n')
        lines.append(header + "\n")
        
        recs = sk_data[sk_id]['recs']
        for idx, r_data in enumerate(recs, start=1):
            r_chunk = r_data['raw'].strip('\n')
            reindexed_chunk = re.sub(r'^\s{4}\'\d+\':', f"    '{idx}':", r_chunk)
            lines.append(reindexed_chunk + "\n")
            
        lines.append("  snapshots: []\n")

    full_output = "".join(lines)

    with open(SAVE_PATH, 'w') as f:
        f.write(full_output)

    print("Rebuilt save.yml successfully!")
    return True

if __name__ == '__main__':
    rebuild_save()
