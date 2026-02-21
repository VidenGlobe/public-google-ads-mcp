# Google Ads MCP Server

An MCP (Model Context Protocol) server that gives Claude read-only access to Google Ads account data. Ships with realistic mock data for immediate testing — no API credentials required.

## What it does

Exposes 6 tools to Claude:

| Tool | Description |
|------|-------------|
| `get_account_info` | Account ID and name |
| `get_campaigns` | All campaigns with 30-day performance metrics |
| `get_ad_groups` | Ad groups for a campaign |
| `get_keywords` | Keywords with quality scores and match types |
| `get_performance_report` | Daily metrics over N days (trend analysis) |
| `get_search_terms` | Search term report with wasted spend flagging |

## Quick Start (Mock Data)

```bash
# Install dependencies
cd google-ads-mcp
uv sync

# Test it works
uv run google-ads-mcp
```

## Connect to Claude Desktop

Add to `~/.config/Claude/claude_desktop_config.json` (Linux) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/google-ads-mcp", "run", "google-ads-mcp"]
    }
  }
}
```

Restart Claude Desktop. You'll see the tools icon (🔧) appear.

## Connect to VS Code (GitHub Copilot)

Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "google-ads": {
        "command": "uv",
        "args": ["--directory", "/absolute/path/to/google-ads-mcp", "run", "google-ads-mcp"]
      }
    }
  }
}
```

## Use with Live Google Ads Data

1. Copy `.env.example` to `.env`
2. Fill in your Google Ads API credentials ([setup guide](https://developers.google.com/google-ads/api/docs/first-call/overview))
3. Set `GOOGLE_ADS_USE_MOCK=false`

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Example Prompts

Once connected, try these in Claude:

- *"Show me all my campaigns and their performance"*
- *"Run a CPA diagnostic on my Google Ads data for the last 14 days vs. the 14 days before that"*
- *"Find wasted spend in my search terms"*
- *"Which keywords have quality scores below 5?"*
- *"Show me daily performance trends for campaign 1002"*

## Project Structure

```
google-ads-mcp/
├── pyproject.toml
├── .env.example
├── README.md
└── src/google_ads_mcp/
    ├── __init__.py
    ├── server.py          # MCP server with 6 tools
    └── mock_data.py       # Realistic test data
```
