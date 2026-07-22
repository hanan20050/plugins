# Project Rules

- Currency hierarchy for `save.yml`:
  - Emerald (`minecraft:emerald`) = Base Currency (1 Emerald)
  - Emerald Block (`minecraft:emerald_block`) = 9 Emeralds
  - Netherite Ingot (`minecraft:netherite_ingot`) = 64 Emeralds
  - Netherite Block (`minecraft:netherite_block`) = 576 Emeralds (9 Netherite Ingots)
- Always check Shopkeepers trade recipes and verify there are no infinite money glitches (e.g., selling price per unit > buying price per unit for any item).
- DO NOT send any chat messages, announcements, or notifications (via tellraw, say, title, or msg) unless the user explicitly requests to notify/broadcast to players.
- **Timer-Based Offer Rule**: Whenever creating or launching any timed offer/discount (e.g. 1-minute sale, 3-minute offer, etc.), ALWAYS run a background script that broadcasts `tellraw` chat updates every **10 seconds**, explicitly stating how much time has passed and how much time is remaining, before automatically ending the offer and restoring original prices.



# Player Identity Reference (Real Names vs. Bedrock/Geyser Usernames)
- `.mustafahacker67` -> Real Name: `mustafa`
- `.HastyBag7675` -> Real Name: `muhammad saleh`
- `.WiryCircle3938` -> Real Name: `omer saleh`
- `hanansaleh` -> Real Name: `hanan saleh`
- `manansaleh2007` -> Real Name: `manan saleh`
- `NightmareDady` -> Real Name: `rayan saleh`
- `.AzanSaleh` / `azansalehhh` -> Real Name: `azan saleh` (Region: `azansalehhh`)

# GitHub 24/7 Automated Upgrade Tracker
- Public Repository: `https://github.com/hanan20050/plugins`
- GitHub Actions Cron Workflow: `.github/workflows/upgrade_tracker.yml` (runs every 5 mins 24/7 for free).
- Secrets: `EXAROTON_TOKEN` and `EXAROTON_SERVER_ID` configured in GitHub Secrets.
- Upgrade Script: `apply_house_upgrades.py` (checks trade log, applies WG region flags, and broadcasts updates).


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

# Railway Worker & Cloud Container Execution Rules
- **Environment Setup Order**: Environment variable overrides (`os.environ.get("EXAROTON_TOKEN")`) MUST be initialized at the top of worker scripts BEFORE importing submodules.
- **Credential Fallbacks**: Ensure fallback `EXAROTON_TOKEN` and `EXAROTON_SERVER_ID` are present so cloud containers (Railway/Docker) without local `.env` files don't evaluate `TOKEN` to `None`.
- **Private In-Game Messaging**: Upgrade activations and notifications MUST use private `/msg <player_name>` messages instead of public `/say` or title announcements.
- **Mandatory Certificate Return**: Upgrades cannot be refunded until the physical Certificate book item (`written_book`) is retrieved/cleared from the player's inventory (`clear <player> minecraft:written_book 1`).


