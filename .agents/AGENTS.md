# Project Rules

- Currency hierarchy for `save.yml`:
  - Emerald (`minecraft:emerald`) = Base Currency (1 Emerald)
  - Emerald Block (`minecraft:emerald_block`) = 9 Emeralds
  - Netherite Ingot (`minecraft:netherite_ingot`) = 64 Emeralds
  - Netherite Block (`minecraft:netherite_block`) = 576 Emeralds (9 Netherite Ingots)
- Always check Shopkeepers trade recipes and verify there are no infinite money glitches (e.g., selling price per unit > buying price per unit for any item).
- **Currency Exchange & Sales Rule (STRICT)**: NEVER apply sales or discounts to Money Exchange (Shopkeeper ID 5) or currency exchange trades (e.g. trading Emeralds <-> Emerald Blocks, Netherite Ingots, or Netherite Blocks) UNLESS explicitly asked by the user. Currency exchange rates are strictly fixed (1 Netherite Ingot = 64 Emeralds, 1 Emerald Block = 9 Emeralds, 1 Netherite Block = 576 Emeralds) and must never be altered during any sale or offer. All sales must exclude the Money Exchange shopkeeper (ID 5) entirely.
- **Shopkeeper Trade Cleanliness Rule (STRICT)**: Currency exchange trades must ONLY exist in the dedicated `Money Exchange` shopkeeper (Shopkeeper ID 5). Regular shops (e.g., General Store or Sell Drops shop) must NOT contain exchange trades. Duplicate trades within any shopkeeper must be removed.
- **Currency Exchange Confirmation Rule (STRICT)**: Only ask the user for explicit confirmation when creating, modifying, adding, or executing currency exchange trades (e.g. trading Emeralds <-> Emerald Blocks, Netherite Ingots, or Netherite Blocks). Regular item buy/sell trades do not require asking for confirmation each time.
- DO NOT send any chat messages, announcements, or notifications (via tellraw, say, title, or msg) unless the user explicitly requests to notify/broadcast to players.
- **Timer-Based Offer Rule**: Whenever creating or launching any timed offer/discount (e.g. 1-minute sale, 3-minute offer, etc.), ALWAYS run a background script that broadcasts `tellraw` chat updates every **10 seconds**, explicitly stating how much time has passed and how much time is remaining, before automatically ending the offer and restoring original prices.
- **New Property Upgrade Rule (STRICT)**: Protection upgrades and flags are strictly per-property. When creating a new property or region expansion for any player, NEVER automatically copy or apply existing protection upgrades/flags (e.g., TNT protection, Creeper protection) from their previous regions. New properties start with default flags (`pvp: allow`), and players must purchase upgrade certificates for each new property separately.
- **Adjacent Expansion Rule (STRICT)**: When creating an expanded region or adjacent plot for any player, the new region/plot must be placed **immediately adjacent** to the existing plot boundary (starting at `max_x + 1` for East expansion) with zero block gap, AND must ALWAYS be **centered** along the length/depth (Z-axis) of the original property boundary so it is balanced and not shifted too far left/north or right/south. The original house/property region bounds must be preserved intact so physical house structures are never cut off or misaligned. Crucially, "adjacent" also strictly implies that the new region/plot must match and share the **exact same floor level (Y-level)** as the original/neighboring plot so they align perfectly.
- **EconomyShopGUI File Editing Rule (STRICT)**: ALWAYS edit EconomyShopGUI configuration files (such as those in the `EconomyShopGUI` folder) locally only. NEVER push or sync EconomyShopGUI changes to the server unless explicitly requested by the user.







# Player Identity Reference (Real Names vs. Bedrock/Geyser Usernames)
- `.mustafahacker67` -> Real Name: `mustafa`
- `.HastyBag7675` -> Real Name: `muhammad saleh`
- `.WiryCircle3938` -> Real Name: `omer saleh`
- `hanansaleh` -> Real Name: `hanan saleh`
- `manansaleh2007` -> Real Name: `manan saleh`
- `NightmareDady` -> Real Name: `rayan saleh`
- `.AzanSaleh` / `azansalehhh` -> Real Name: `azan saleh` (Region: `azansalehhh`)


# Running Console Commands via Exaroton API
- When executing commands on the Exaroton server console via the API, the sandbox DNS may fail to resolve `api.exaroton.com`.
- Always use manual DNS resolution (e.g., `--resolve api.exaroton.com:443:104.26.12.211`) when calling the API via curl or Python subprocess.
- Endpoint: `POST https://api.exaroton.com/v1/servers/{server_id}/command/`
- Request Header: `Content-Type: application/json`
- Request Body (JSON object): `{"command": "<command_here>"}`
- Always use the server console to make edits/changes to plugin configurations (such as region flags) rather than modifying configuration files directly on disk.
- Authentication tokens and Server ID are located in the local `.env` file (`EXAROTON_TOKEN` and `EXAROTON_SERVER_ID`).
- Example command execution using `curl`:
  ```bash
  curl -s --resolve api.exaroton.com:443:104.26.12.211 \
    -X POST "https://api.exaroton.com/v1/servers/{server_id}/command/" \
    -H "Authorization: Bearer {token}" \
    -H "Content-Type: application/json" \
    -d '{"command": "<command_here>"}'

# Automatic Data Pulling Rule
- ALWAYS pull the latest configuration/region/trade log files from the Exaroton server via `sync.py pull <filepath>` whenever the user asks for updates, status checks, region queries, or server state verification before giving an answer.

# Region Size Categorization Formula & Rules
- Region Dimensions Calculation Formula:
  - Width (X): `(max_x - min_x) + 1`
  - Length (Z): `(max_z - min_z) + 1`
- Size Categories:
  - **Starter / Base Plot**: Under 15x15 blocks
  - **Small Plot**: Up to 25x25 blocks (e.g. 22x22 falls into Small Plot)
  - **Normal Plot**: Up to 50x50 blocks
  - **Big Plot**: Up to 100x100 blocks

# Automatic Sync & Plugin Reloading Rule
- Whenever any plugin configuration or data file (e.g. `Shopkeepers/data/save.yml`, `config.yml`, etc.) is created or modified, ALWAYS immediately upload/push the updated file to the Exaroton server via the API and execute the corresponding plugin reload command on the Exaroton server console (e.g., `shopkeeper reload`).

# Server Restart Permission Rule (STRICT)
- NEVER restart or stop the Exaroton server without obtaining explicit permission from the user first. Always ask the user and wait for their confirmation before issuing any server restart or stop command.


# Undo & Rollback Requirement (STRICT)
- ALWAYS implement and maintain a strictly operational undo/rollback mechanism for any scripts or commands that edit the Minecraft world (blocks/floors) or WorldGuard regions (redefining bounds, membership changes, flag changes).
- Region-modifying scripts must back up the region data before editing and support an `--undo` option.
- World/block modifying scripts must keep a history of the commands run and support a command to revert changes.
- Whenever executing an undo/rollback or clearing/removing blocks from the world, ALWAYS immediately execute a console command to clear any dropped item loot in the affected area to prevent clutter.

# WorldGuard Region Ownership & Player UUID Rule (STRICT)
- **Always Include UUIDs**: When defining or modifying WorldGuard regions (`regions.yml`) for any player (in any world), ALWAYS include their player UUID under `owners.unique-ids` (e.g. `95204d3f-ea6c-3dfa-929d-9180927184f8` for Manan). Plain text usernames alone in `owners.players` are NOT recognized by WorldGuard on online-mode/Geyser servers.

# Player Region Markings & Registry Rule (STRICT)
- **Persistent Floor Markings Registry**: ALWAYS reference and update `player_regions_registry.json` whenever creating, modifying, or querying player regions, floor boundaries, or concrete floor color markings (e.g. Azan Saleh's Cyan North half, Black West 3-block border, and Red South remaining base). New regions created for any player must be registered in `player_regions_registry.json` with exact coordinates, dimensions, size categories, UUIDs, and floor material markings.
- **EconomyShopGUI Slot Configuration Rule (STRICT)**: When configuring items in EconomyShopGUI (such as in `shops/` or `sections/`), ensure that `slot:` is set to a valid slot index (between 0 and 53) or omitted entirely for automatic layout. Setting `slot:` to an out-of-bounds value (e.g., `88`) will cause the item to fail to load in the shop database, preventing it from being sold via `/sellall` or appearing in the GUI.
- **Region Structure & Sub-zone Logging Rule (STRICT)**: Whenever creating, modifying, or detailing a region that contains multiple structures or sub-zones (e.g., a house and a farm), ALWAYS create a log/registry entry documenting exactly which structure/sub-zone is located where (its coordinates, purpose, and key coordinates) within the workspace registry or region notes.
- **Additive & Surgical Modification Rule (STRICT)**: Whenever asked to "add" something to an area or build, do NOT clear or reset the existing structure/area; only place the new elements. If asked to "repair", "tweak", or modify an existing build, do NOT clear/fill the entire area with air first; calculate and target only the specific coordinates of the blocks that require changes.

# Low Token Use Policy (STRICT)
- **Minimal Token Usage**: Keep all responses as short, concise, and direct as possible. Never summarize, recap, or repeat details of completed files, diffs, or commands in your final responses unless explicitly requested by the user.
- **Targeted Reading**: Specifying StartLine and EndLine values is mandatory when reading/inspecting files. Avoid displaying full logs or large code snippets.
- **Filtered Command Outputs**: Always pipe terminal commands to `grep`, `tail -n`, or similar utilities to return only relevant output. Use silent flags (`-s`, `-q`) for all fetch/download commands.
- **Surgical Code Edits**: Edit code only using precise replacements targeting the exact lines to modify.
- **Short Final Statuses**: Minimize summary details in final responses to a maximum of 1-3 lines.




