import re, subprocess, json, time, sys

with open('.env') as f:
    env_content = f.read()

token = re.search(r'EXAROTON_TOKEN=(.*)', env_content).group(1).strip()
server_id = re.search(r'EXAROTON_SERVER_ID=(.*)', env_content).group(1).strip()

headers = [
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json'
]

biomes = [
    "badlands", "bamboo_jungle", "beach", "birch_forest", "cherry_grove",
    "cold_ocean", "dark_forest", "deep_cold_ocean", "deep_dark", "deep_frozen_ocean",
    "deep_lukewarm_ocean", "deep_ocean", "desert", "dripstone_caves", "eroded_badlands",
    "flower_forest", "forest", "frozen_ocean", "frozen_peaks", "frozen_river",
    "grove", "ice_spikes", "jagged_peaks", "jungle", "lukewarm_ocean",
    "lush_caves", "mangrove_swamp", "meadow", "mushroom_fields", "ocean",
    "old_growth_birch_forest", "old_growth_pine_taiga", "old_growth_spruce_taiga", "plains", "river",
    "savanna", "savanna_plateau", "snowy_beach", "snowy_plains", "snowy_slopes",
    "snowy_taiga", "sparse_jungle", "stony_peaks", "stony_shore", "sunflower_plains",
    "swamp", "taiga", "warm_ocean", "windswept_forest", "windswept_gravelly_hills",
    "windswept_hills", "windswept_savanna", "wooded_badlands"
]

print(f"=== OVERWORLD BIOME SEARCH FOR PLAYER 'hanansaleh' (1299, 79, -219) ===", flush=True)
print(f"Total biomes to query: {len(biomes)}\n", flush=True)

results = {}

for idx, b in enumerate(biomes, 1):
    print(f"[{idx}/{len(biomes)}] Locating {b}...", end=" ", flush=True)
    cmd_str = f"minecraft:execute at hanansaleh run minecraft:locate biome minecraft:{b}"
    cmd = [
        'curl', '-s', '--resolve', 'api.exaroton.com:443:104.26.12.211',
        '-X', 'POST', f'https://api.exaroton.com/v1/servers/{server_id}/command/'
    ] + headers + ['-d', json.dumps({'command': cmd_str})]
    
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(1.2)

    # Fetch latest log
    log_cmd = [
        'curl', '-s', '--resolve', 'api.exaroton.com:443:104.26.12.211',
        '-X', 'GET', f'https://api.exaroton.com/v1/servers/{server_id}/logs/'
    ] + headers[0:2]

    res = subprocess.run(log_cmd, capture_output=True, text=True)
    found = False
    try:
        data = json.loads(res.stdout)
        content = data.get('data', {}).get('content', '')
        for line in reversed(content.splitlines()[-30:]):
            m = re.search(rf'The nearest minecraft:{b} is at \[(-?\d+),\s*(-?\d+|\~|\?),?\s*(-?\d+)\] \((.*?)\)', line)
            if m:
                x, y, z, dist = m.group(1), m.group(2), m.group(3), m.group(4)
                results[b] = {'x': x, 'y': y, 'z': z, 'dist': dist}
                print(f"-> Found at ({x}, {y}, {z}) [{dist}]", flush=True)
                found = True
                break
            m_nf = re.search(rf'Could not find a biome of type minecraft:{b}', line)
            if m_nf:
                results[b] = {'x': 'N/A', 'y': 'N/A', 'z': 'N/A', 'dist': 'Not within range'}
                print(f"-> Not within search range", flush=True)
                found = True
                break
    except Exception as e:
        pass
    
    if not found:
        results[b] = {'x': 'N/A', 'y': 'N/A', 'z': 'N/A', 'dist': 'Pending'}
        print(f"-> Query sent", flush=True)

# Save to file
file_content = """# Overworld Biome Coordinates List
**Player:** `hanansaleh`
**Origin Location:** X: `1299`, Y: `79`, Z: `-219`

| Biome Name | Biome ID | Coordinates (X, Y, Z) | Distance |
| :--- | :--- | :--- | :--- |
"""

for b in sorted(biomes):
    info = results.get(b, {'x': 'N/A', 'y': 'N/A', 'z': 'N/A', 'dist': 'N/A'})
    formatted_name = b.replace('_', ' ').title()
    coords = f"({info['x']}, {info['y']}, {info['z']})" if info['x'] != 'N/A' else "Not in range"
    file_content += f"| {formatted_name} | `minecraft:{b}` | {coords} | {info['dist']} |\n"

with open("overworld_biomes_locations.md", "w") as out:
    out.write(file_content)

txt_content = f"OVERWORLD BIOME COORDINATES LIST FOR PLAYER hanansaleh (1299, 79, -219)\n"
txt_content += "=" * 70 + "\n\n"

for b in sorted(biomes):
    info = results.get(b, {'x': 'N/A', 'y': 'N/A', 'z': 'N/A', 'dist': 'N/A'})
    formatted_name = b.replace('_', ' ').title()
    coords = f"X: {info['x']}, Y: {info['y']}, Z: {info['z']}" if info['x'] != 'N/A' else "Not in range"
    txt_content += f"- {formatted_name} (minecraft:{b}): {coords} | Distance: {info['dist']}\n"

with open("overworld_biomes_locations.txt", "w") as out_txt:
    out_txt.write(txt_content)

print("\n=== SCAN COMPLETE ===", flush=True)
print("Saved complete report to overworld_biomes_locations.txt and overworld_biomes_locations.md!", flush=True)
