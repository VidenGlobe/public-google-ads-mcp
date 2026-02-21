# Generate Google Ads OAuth2 Refresh Token

Generates a refresh token for the Google Ads API using OAuth2.

## Setup

1. Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com):
   - APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Choose **Web application**
   - Add `http://127.0.0.1:8080` to Authorized redirect URIs
   - Download and save as `client_secret.json`

2. Enable the [Google Ads API](https://console.cloud.google.com/apis/library/googleads.googleapis.com)

## Usage

```bash
uv run auth/generate_refresh_token.py -c client_secret.json
```

### Important: VSCode Users

When the script displays the authorization URL:
- **Copy** the URL from the terminal
- **Paste** it into your browser manually
- Do NOT click the "Open in browser" suggestion in VSCode - this breaks the callback flow
- **Use your personal Google account** (not a shared account or account without proper access)

### What Happens

1. Script starts a local server on `127.0.0.1:8080`
2. You authorize the app in your browser
3. Google redirects back to the local server
4. Script displays your refresh token

## Using the Token

Add the refresh token to your `.env` file or configuration.

## Troubleshooting

- **Port in use**: `lsof -ti:8080 | xargs kill -9`
- **Auth fails**: Verify redirect URI is set in Google Cloud Console
- **Invalid client**: Check `client_secret.json` is valid