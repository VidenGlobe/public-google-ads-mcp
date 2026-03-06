# Google Ads MCP Server

An MCP (Model Context Protocol) server that gives Claude/Copilot read-only access to Google Ads account data. Supports querying any customer account by passing the customer ID per request.

## What it does

Exposes 10 tools — every tool takes a `customer_id` parameter so you can query any account:

| Tool | Description |
|------|-------------|
| `get_campaigns` | All campaigns with 30-day performance metrics |
| `get_ad_groups` | Ad groups for a campaign |
| `get_keywords` | Keywords with quality scores and match types |
| `get_performance_report` | Daily metrics over N days (trend analysis) |
| `get_search_terms` | Search term report (wasted spend, negative keyword opportunities) |
| `get_geo_performance` | Geographic breakdown (country, region, city) |
| `get_device_performance` | Device split (mobile, desktop, tablet) |
| `get_ad_performance` | Ad creative performance (headlines, descriptions, CTR) |
| `get_age_gender_performance` | Demographic breakdown (age range + gender) |
| `get_audience_performance` | Audience segment performance (in-market, affinity, custom) |

---

## Quick Start — Install Dependencies

```bash
cd /home/rustam/projecs/videnglobe/google-ads-mcp
uv sync
```

---

## Setup — Google Ads API Credentials

1. Copy `.env.example` to `.env`
2. Fill in your Google Ads API credentials ([setup guide](https://developers.google.com/google-ads/api/docs/first-call/overview))

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `GOOGLE_ADS_DEVELOPER_TOKEN` — your API developer token
- `GOOGLE_ADS_CLIENT_ID` — OAuth2 client ID
- `GOOGLE_ADS_CLIENT_SECRET` — OAuth2 client secret
- `GOOGLE_ADS_REFRESH_TOKEN` — OAuth2 refresh token (use `auth/generate_refresh_token.py` to generate)
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` — your MCC/manager account ID (no dashes)

The target `customer_id` is **not** in `.env` — it's passed per request by the agent.

### Generate a refresh token

In the intended setup flow, an admin gives the user all credentials except `GOOGLE_ADS_REFRESH_TOKEN`.

If you do not have `GOOGLE_ADS_REFRESH_TOKEN` yet, run one command:

```bash
uv run scripts/get_refresh_token.py
```

Or on Windows via PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate-refresh-token-windows.ps1
```

The script reads `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET` from `.env`, opens the Google login page in your browser, and **automatically saves** the refresh token back into `.env`. No manual copying needed.

---

## VS Code + GitHub Copilot (Step-by-Step)

### Step 1: Verify the MCP config file exists

The file `.vscode/mcp.json` in this project already contains the server config:

```json
{
  "servers": {
    "google-ads": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/home/rustam/projecs/videnglobe/google-ads-mcp",
        "run",
        "google-ads-mcp"
      ]
    }
  },
  "inputs": []
}
```

### Step 2: Enable MCP support in VS Code settings

Open VS Code Settings (`Ctrl+,`) and make sure this setting is enabled:

```
Chat > MCP: Enabled  →  ✅ checked
```

Or add to your `settings.json`:
```json
{
  "chat.mcp.enabled": true
}
```

### Step 3: Start the MCP server in VS Code

1. Open the **Command Palette** (`Ctrl+Shift+P`)
2. Type **`MCP: List Servers`** and press Enter
3. You should see **`google-ads`** in the list
4. If it shows as **stopped**, click on it and select **"Start Server"**

Alternatively:
1. Open the **Command Palette** (`Ctrl+Shift+P`)
2. Type **`MCP: Start Server`** and press Enter
3. Select **`google-ads`** from the dropdown

### Step 4: Verify it's running

1. Open **Copilot Chat** (`Ctrl+Alt+I` or click the Copilot icon in the sidebar)
2. Switch to **Agent mode** (click the dropdown at the top of the chat panel — switch from "Ask" or "Edit" to **"Agent"**)
3. You should see a **🔧 tools icon** in the chat input area — click it to see the 10 Google Ads tools listed
4. If you don't see the tools icon, the server may not be started — go back to Step 3

### Step 5: Test it

In Copilot Chat (Agent mode), type:

> **Show me all campaigns for customer 1234567890**

Copilot will ask for permission to call the `get_campaigns` tool. Click **"Allow"** and you'll see live data from the Google Ads API.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Server not listed in `MCP: List Servers` | Make sure you have `.vscode/mcp.json` in the workspace root and the workspace is open in VS Code |
| Server fails to start | Run `cd /home/rustam/projecs/videnglobe/google-ads-mcp && uv run google-ads-mcp` in terminal to check for errors |
| No tools icon in Copilot Chat | Make sure you're in **Agent mode** (not "Ask" or "Edit" mode) |
| `uv` not found | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` then restart VS Code |
| Tools listed but not working | Click "Allow" when Copilot asks for permission to use the tool |

---

## Claude Desktop on Windows (native)

You do not need WSL for this project. Claude Desktop can run the server directly on Windows.

Fastest option if the repo is already on the machine:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows-claude-desktop.ps1
```

The script installs missing tools, creates `.env`, runs `uv sync`, and updates `claude_desktop_config.json` automatically.

If the repo is not on the machine yet, use this instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-public-google-ads-mcp.ps1
```

That script clones or pulls `https://github.com/VidenGlobe/public-google-ads-mcp` into `$HOME\google-ads-mcp`, then runs the Windows Claude Desktop setup.

### Step 1: Install Git and uv

Open `PowerShell` and run:

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
```

Then restart your terminal.

If `winget` is not available on the machine, install Git from `https://git-scm.com/download/win` and install uv from `https://docs.astral.sh/uv/getting-started/installation/`.

### Step 2: Clone the repo and install dependencies

```powershell
cd $HOME
git clone https://github.com/VidenGlobe/public-google-ads-mcp google-ads-mcp
cd $HOME\google-ads-mcp
Copy-Item .env.example .env
uv sync
```

Edit `.env` and fill in your Google Ads API credentials.

### Step 3: Find the full path to `uv`

Run:

```powershell
where.exe uv
```

Copy the first result. It will usually look like:

```text
C:\Users\<YourName>\AppData\Local\Microsoft\WinGet\Links\uv.exe
```

### Step 4: Open the Claude Desktop config file

Press `Win+R`, paste this path, and press Enter:

```
%APPDATA%\Claude\claude_desktop_config.json
```

If the file doesn't exist, create it. If the `Claude` folder doesn't exist, create it at `C:\Users\<YourName>\AppData\Roaming\Claude\`.

### Step 5: Add the MCP server config

Paste this into `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "C:/Users/<YourName>/AppData/Local/Microsoft/WinGet/Links/uv.exe",
      "args": [
        "--directory",
        "C:/Users/<YourName>/google-ads-mcp",
        "run",
        "google-ads-mcp"
      ]
    }
  }
}
```

Replace:

- `C:/Users/<YourName>/AppData/Local/Microsoft/WinGet/Links/uv.exe` with the exact result from `where.exe uv`
- `C:/Users/<YourName>/google-ads-mcp` with the folder where you cloned this repo

### Step 6: Restart Claude Desktop

Fully quit Claude Desktop (system tray → right-click → Quit), then reopen it.

### Step 7: Verify

You should see a tools icon in the chat input area. Click it to see the Google Ads tools. Try:

> **Show me all campaigns for customer 1234567890**

### Troubleshooting (Windows)

| Problem | Solution |
|---------|----------|
| `winget` not found | Install Git from `https://git-scm.com/download/win` and uv from `https://docs.astral.sh/uv/getting-started/installation/` |
| Tools icon doesn't appear | Fully quit and reopen Claude Desktop (not just close the window) |
| `uv` not found | Run `where.exe uv` and use the exact full path in `claude_desktop_config.json` |
| Server errors | Test manually: open PowerShell and run `cd $HOME\google-ads-mcp` then `uv run google-ads-mcp` |
| Config file location | Windows: `%APPDATA%\Claude\claude_desktop_config.json` → typically `C:\Users\<YourName>\AppData\Roaming\Claude\` |

---

## Claude Desktop on Linux / macOS (native)

Add to `~/.config/Claude/claude_desktop_config.json` (Linux) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "uv",
      "args": ["--directory", "/home/rustam/projecs/videnglobe/google-ads-mcp", "run", "google-ads-mcp"]
    }
  }
}
```

Restart Claude Desktop. You'll see the tools icon (🔧) appear.

---

## Example Prompts

Once connected, try these in Copilot Chat (Agent mode) or Claude:

- *"Show me all campaigns for customer 1234567890"*
- *"Run a CPA diagnostic on customer 1234567890 for the last 30 days"*
- *"Find wasted spend in search terms for customer 1234567890"*
- *"Which keywords have quality scores below 5 for customer 1234567890?"*
- *"Show me geographic performance for customer 1234567890"*
- *"Compare device performance across campaigns for customer 1234567890"*
- *"Show me demographic breakdown (age + gender) for customer 1234567890"*
- *"What audiences are performing best for customer 1234567890?"*

---

## Project Structure

```
google-ads-mcp/
├── .vscode/
│   └── mcp.json           # VS Code MCP server config (auto-detected)
├── auth/
│   └── generate_refresh_token.py  # OAuth2 token generation utility
├── pyproject.toml
├── .env.example
├── README.md
└── src/google_ads_mcp/
    ├── __init__.py
    └── server.py          # MCP server with 10 tools
```
