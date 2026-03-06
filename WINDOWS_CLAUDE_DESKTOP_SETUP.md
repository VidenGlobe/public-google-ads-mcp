# Google Ads MCP for Claude Desktop on Windows

This guide is written for a non-technical user.

Goal: install the MCP server, connect it to Claude Desktop on Windows, and make the Google Ads tools appear inside Claude.

## Fastest option

If the repo is already on the computer, you can run one script instead of doing most steps manually.

Open `PowerShell` in the repo folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows-claude-desktop.ps1
```

What the script does:

- installs `git` if missing
- installs `uv` if missing
- creates `.env` from `.env.example` if needed
- opens `.env` in Notepad if it still has placeholder values
- runs `uv sync`
- updates `claude_desktop_config.json` automatically

What you still need to do yourself:

- make sure Claude Desktop is installed
- fill in your real Google Ads credentials in `.env`
- restart Claude Desktop after the script finishes

If the repo is not on the computer yet, use this script instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-public-google-ads-mcp.ps1
```

It clones or pulls:

```text
https://github.com/VidenGlobe/public-google-ads-mcp
```

Then it runs the main Windows setup script automatically.

## What you need before you start

- A Windows computer
- Claude Desktop installed
- A Google Ads API setup already created, or someone who can give you these 5 values:
  - `GOOGLE_ADS_DEVELOPER_TOKEN`
  - `GOOGLE_ADS_CLIENT_ID`
  - `GOOGLE_ADS_CLIENT_SECRET`
  - `GOOGLE_ADS_REFRESH_TOKEN`
  - `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

If you do not have the 5 Google Ads values yet, do the install first and ask your admin for them later.

## Step 1. Open PowerShell

Click `Start`, type `PowerShell`, then open it.

You will do the whole setup in PowerShell.

## Step 2. Install Git

Copy and paste:

```powershell
winget install --id Git.Git -e
```

Wait until it finishes.

If Windows asks for permission, click `Yes`.

If you get an error that `winget` does not exist, install Git from `https://git-scm.com/download/win` instead.

## Step 3. Install uv

Copy and paste:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

OR

```powershell
winget install --id astral-sh.uv -e
```

Wait until it finishes.

**Then close PowerShell and open it again.**

If you get an error that `winget` does not exist, install uv from `https://docs.astral.sh/uv/getting-started/installation/` instead.

To confirm `uv` is installed, run:

```powershell
uv --version
```

## Step 4. Download the MCP server

In PowerShell, run:

```powershell
cd $HOME
git clone https://github.com/VidenGlobe/public-google-ads-mcp google-ads-mcp
cd $HOME\google-ads-mcp
```

If you already have this repo on your computer, open that folder instead.

## Step 5. Create the `.env` file

In PowerShell, run:

```powershell
cd $HOME\google-ads-mcp
Copy-Item .env.example .env
notepad .env
```

Notepad will open.

Replace the sample values with your real values for:

- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

Save the file and close Notepad.

## Step 6. Install the project dependencies

In PowerShell, run:

```powershell
cd $HOME\google-ads-mcp
uv sync
```

Wait until it finishes.

## Step 7. Test that the server starts

In PowerShell, run:

```powershell
cd $HOME\google-ads-mcp
uv run google-ads-mcp
```

If the command just sits there quietly, that is usually fine. It means the server started and is waiting for Claude Desktop.

Press `Ctrl+C` to stop it after the test.

If you see an error, fix that first before connecting Claude Desktop.

## Step 8. Find your `uv` path

Claude Desktop works best when you give it the full path to `uv.exe`.

In PowerShell, run:

```powershell
where.exe uv
```

Copy the first result.

It will usually look like this:

```text
C:\Users\<YourName>\AppData\Local\Microsoft\WinGet\Links\uv.exe
```

## Step 9. Add the server to Claude Desktop

On Windows:

1. Press `Win + R`
2. Paste this:

```text
%APPDATA%\Claude
```

3. Press `Enter`
4. Create a file named `claude_desktop_config.json` if it does not exist
5. Open that file in Notepad

Paste this config:

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

Now replace:

- `C:/Users/<YourName>/AppData/Local/Microsoft/WinGet/Links/uv.exe` with the exact result from `where.exe uv`
- `C:/Users/<YourName>/google-ads-mcp` with the real folder where you cloned this repo

Save the file.

## Step 10. Restart Claude Desktop

This part matters.

1. Fully close Claude Desktop
2. Also close it from the system tray if it is still running
3. Open Claude Desktop again

## Step 11. Check that it worked

Open Claude Desktop and look for the tools icon in the chat box.

If the MCP server is connected, Claude should show Google Ads tools.

You can test with a prompt like:

```text
Show me all campaigns for customer 1234567890
```

Replace `1234567890` with a real Google Ads customer ID.

## If something does not work

### Claude does not show any tools

- Fully quit Claude Desktop and open it again
- Re-check `claude_desktop_config.json`
- Make sure the JSON has no extra commas or missing brackets

### `uv` is not found

Run this in PowerShell:

```powershell
where.exe uv
```

Then put that exact path into `claude_desktop_config.json`.

### The server fails to start

Run this in PowerShell:

```powershell
cd $HOME\google-ads-mcp
uv run google-ads-mcp
```

If you see an error, that is the problem Claude Desktop is also hitting.

### The repo is private and `git clone` fails

- Make sure you have access to the repo
- Use the correct Git URL
- If your company uses GitHub login, you may need a GitHub token instead of a password

### Google Ads tools appear, but data does not load

Usually this means one of the Google Ads values in `.env` is wrong or missing.

Check:

- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

## Short version

1. Open `PowerShell`
2. Install `git`
3. Install `uv`
4. Clone the repo
5. Create `.env`
6. Paste Google Ads credentials into `.env`
7. Run `uv sync`
8. Add the server to `claude_desktop_config.json`
9. Restart Claude Desktop
