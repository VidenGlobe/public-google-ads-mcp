# Google Ads MCP Server

An MCP (Model Context Protocol) server that gives Claude/Copilot read-only access to Google Ads account data. Ships with realistic mock data for immediate testing — no API credentials required.

## What it does

Exposes 6 tools:

| Tool | Description |
|------|-------------|
| `get_account_info` | Account ID and name |
| `get_campaigns` | All campaigns with 30-day performance metrics |
| `get_ad_groups` | Ad groups for a campaign |
| `get_keywords` | Keywords with quality scores and match types |
| `get_performance_report` | Daily metrics over N days (trend analysis) |
| `get_search_terms` | Search term report with wasted spend flagging |

---

## Quick Start — Install Dependencies

```bash
cd /home/rustam/projecs/videnglobe/google-ads-mcp
uv sync
```

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
3. You should see a **🔧 tools icon** in the chat input area — click it to see the 6 Google Ads tools listed
4. If you don't see the tools icon, the server may not be started — go back to Step 3

### Step 5: Test it

In Copilot Chat (Agent mode), type:

> **Show me all my campaigns and their performance**

Copilot will ask for permission to call the `get_campaigns` tool. Click **"Allow"** and you'll see the mock data.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Server not listed in `MCP: List Servers` | Make sure you have `.vscode/mcp.json` in the workspace root and the workspace is open in VS Code |
| Server fails to start | Run `cd /home/rustam/projecs/videnglobe/google-ads-mcp && uv run google-ads-mcp` in terminal to check for errors |
| No tools icon in Copilot Chat | Make sure you're in **Agent mode** (not "Ask" or "Edit" mode) |
| `uv` not found | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` then restart VS Code |
| Tools listed but not working | Click "Allow" when Copilot asks for permission to use the tool |

---

## Claude Desktop on Windows (via WSL — Recommended)

Since this project lives in WSL, Claude Desktop on Windows needs to call into WSL to run the server.

### Step 1: Open the Claude Desktop config file

Press `Win+R`, paste this path, and press Enter:

```
%APPDATA%\Claude\claude_desktop_config.json
```

If the file doesn't exist, create it. If the `Claude` folder doesn't exist, create it at `C:\Users\<YourName>\AppData\Roaming\Claude\`.

### Step 2: Add the MCP server config

Paste this into `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "wsl.exe",
      "args": [
        "--distribution", "Ubuntu",
        "--exec",
        "/home/rustam/.local/bin/uv",
        "--directory", "/home/rustam/projecs/videnglobe/google-ads-mcp",
        "run", "google-ads-mcp"
      ]
    }
  }
}
```

> **Note:** Replace `Ubuntu` with your WSL distro name if different. Run `wsl -l -v` in PowerShell to check.

### Step 3: Restart Claude Desktop

Fully quit Claude Desktop (system tray → right-click → Quit), then reopen it.

### Step 4: Verify

You should see a 🔧 (hammer) icon in the chat input area. Click it to see the 6 Google Ads tools. Try:

> **Show me all my campaigns and their performance**

### Troubleshooting (Windows + WSL)

| Problem | Solution |
|---------|----------|
| Tools icon doesn't appear | Fully quit and reopen Claude Desktop (not just close the window) |
| `wsl.exe` not found | Make sure WSL is installed: run `wsl --status` in PowerShell |
| Wrong distro | Run `wsl -l -v` in PowerShell and use the correct name in `--distribution` |
| `uv` not found in WSL | Use full path `/home/rustam/.local/bin/uv` (already set in the config above) |
| Server errors | Test manually: open WSL terminal and run `cd /home/rustam/projecs/videnglobe/google-ads-mcp && uv run google-ads-mcp` |
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

## Use with Live Google Ads Data

1. Copy `.env.example` to `.env`
2. Fill in your Google Ads API credentials ([setup guide](https://developers.google.com/google-ads/api/docs/first-call/overview))
3. Set `GOOGLE_ADS_USE_MOCK=false`

```bash
cp .env.example .env
# Edit .env with your credentials
```

---

## Example Prompts

Once connected, try these in Copilot Chat (Agent mode) or Claude:

- *"Show me all my campaigns and their performance"*
- *"Run a CPA diagnostic on my Google Ads data for the last 14 days vs. the 14 days before that"*
- *"Find wasted spend in my search terms"*
- *"Which keywords have quality scores below 5?"*
- *"Show me daily performance trends for campaign 1002"*
- *"Get search terms for campaign 1002 and flag any with zero conversions"*

---

## Project Structure

```
google-ads-mcp/
├── .vscode/
│   └── mcp.json           # VS Code MCP server config (auto-detected)
├── pyproject.toml
├── .env.example
├── README.md
└── src/google_ads_mcp/
    ├── __init__.py
    ├── server.py          # MCP server with 6 tools
    └── mock_data.py       # Realistic test data
```
