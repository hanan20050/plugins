# Project Rules

- Emerald is the base currency for this file (`save.yml`).
- Netherite Ingot is the bigger currency (1 Netherite Ingot = 64 Emeralds).
- Always check Shopkeepers trade recipes and verify there are no infinite money glitches (e.g., selling price per unit > buying price per unit for any item).
- For broadcasting announcements to all players, use title/subtitle commands so they fit nicely on the screen (e.g., `/title @a title {"text":"New Features","color":"gold"}` followed by `/title @a subtitle {"text":"Coming Soon!","color":"yellow"}`).


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

# Automatic Sync & Plugin Reloading Rule
- Whenever any plugin configuration or data file (e.g. `Shopkeepers/data/save.yml`, `config.yml`, etc.) is created or modified, ALWAYS immediately upload/push the updated file to the Exaroton server via the API and execute the corresponding plugin reload command on the Exaroton server console (e.g., `shopkeeper reload`).

# Server Restart Permission Rule (STRICT)
- NEVER restart or stop the Exaroton server without obtaining explicit permission from the user first. Always ask the user and wait for their confirmation before issuing any server restart or stop command.


