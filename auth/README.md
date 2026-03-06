# Generate Google Ads OAuth2 Refresh Token

Generates a refresh token for the Google Ads API using OAuth2.

## Quick start (recommended)

Make sure `.env` has `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET`, then run:

```bash
uv run scripts/get_refresh_token.py
```

The script will:
1. Read your client ID and secret from `.env`
2. Open the Google login page in your browser
3. Wait for you to sign in and click "Allow"
4. **Automatically save** the refresh token back into `.env`

On Windows via PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate-refresh-token-windows.ps1
```

On Linux/macOS:

```bash
./scripts/generate-refresh-token.sh
```

## Options

```
--env-file PATH   Use a specific .env file (default: auto-detect)
--no-save         Only print the token, do not update .env
--no-open         Do not auto-open the browser
```

## Low-level script

If you have a `client_secret.json` file from Google Cloud Console and want to use the raw helper:

```bash
uv run auth/generate_refresh_token.py -c client_secret.json
```

This prints the token but does not save it to `.env`.

## Prerequisites (admin setup)

1. Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com):
   - APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Choose **Web application**
   - Add `http://127.0.0.1:8080` to Authorized redirect URIs

2. Enable the [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com)

3. Give the user `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET`

## Troubleshooting

- **Port 8080 in use**: Close the app using that port, or check with `lsof -ti:8080` (Linux/Mac) / `netstat -ano | findstr :8080` (Windows)
- **Empty refresh token**: Go to https://myaccount.google.com/permissions, remove the app, and try again
- **Auth fails**: Verify `http://127.0.0.1:8080` is in the Authorized redirect URIs in Google Cloud Console
- **VSCode terminal**: If the browser doesn't open, copy the URL manually and paste it into your browser
