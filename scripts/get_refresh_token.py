"""Generate an OAuth2 refresh token and save it to .env automatically.

Reads GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET from .env,
runs the browser-based OAuth2 flow, and writes GOOGLE_ADS_REFRESH_TOKEN
back into .env.

Works on Windows, Linux, and macOS. No arguments needed.

Usage:
    uv run scripts/get_refresh_token.py
    uv run scripts/get_refresh_token.py --env-file /path/to/.env
"""

import hashlib
import json
import os
import re
import socket
import sys
import tempfile
import webbrowser
from functools import partial
from pathlib import Path
from urllib.parse import unquote

from google_auth_oauthlib.flow import Flow

# Force unbuffered output so messages appear immediately on Windows
print = partial(print, flush=True)  # noqa: A001

_SCOPE = "https://www.googleapis.com/auth/adwords"
_SERVER = "127.0.0.1"
_PORT = 8080
_REDIRECT_URI = f"http://{_SERVER}:{_PORT}"


def find_env_file(explicit_path: str | None = None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if not p.exists():
            print(f"ERROR: .env file not found: {p}")
            sys.exit(1)
        return p

    # Walk up from script location to find .env
    script_dir = Path(__file__).resolve().parent
    for d in [script_dir.parent, script_dir, Path.cwd()]:
        candidate = d / ".env"
        if candidate.exists():
            return candidate

    print("ERROR: .env file not found.")
    print("Create one from .env.example and fill in GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET.")
    sys.exit(1)


def read_env_value(env_path: Path, key: str) -> str | None:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*)\s*$")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("#"):
            continue
        m = pattern.match(line)
        if m:
            val = m.group(1).strip()
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            return val
    return None


def update_env_value(env_path: Path, key: str, value: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines()
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    found = False
    for i, line in enumerate(lines):
        if not line.strip().startswith("#") and pattern.match(line):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_authorization_code(passthrough_val: str) -> str:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((_SERVER, _PORT))
    except OSError:
        print(f"\nERROR: Port {_PORT} is already in use.")
        print("Close the application using that port and try again.")
        if sys.platform == "win32":
            print(f"  Check with: netstat -ano | findstr :{_PORT}")
        else:
            print(f"  Check with: lsof -ti:{_PORT}")
        sys.exit(1)

    sock.listen(1)
    connection, _ = sock.accept()
    data = connection.recv(1024)

    decoded = data.decode("utf-8")
    match = re.search(r"GET\s\/\?(.*) ", decoded)
    if not match:
        connection.close()
        sock.close()
        print("\nERROR: Did not receive a valid callback from Google.")
        sys.exit(1)

    raw_params = match.group(1)
    pairs = [pair.split("=") for pair in raw_params.split("&")]
    params = {k: v for k, v in pairs}

    try:
        if not params.get("code"):
            error = params.get("error", "unknown")
            msg = f"Authorization failed: {error}"
            response_body = f"<b>{msg}</b><p>Check the terminal for details.</p>"
            raise ValueError(msg)
        if params.get("state") != passthrough_val:
            msg = "State token mismatch — possible CSRF. Try again."
            response_body = f"<b>{msg}</b>"
            raise ValueError(msg)
        response_body = "<b>Authorization successful!</b><p>You can close this tab.</p>"
    except ValueError as e:
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{response_body}\r\n"
        connection.sendall(response.encode())
        connection.close()
        sock.close()
        print(f"\n{e}")
        sys.exit(1)

    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{response_body}\r\n"
    connection.sendall(response.encode())
    connection.close()
    sock.close()

    return unquote(params["code"])


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate Google Ads OAuth2 refresh token from .env")
    parser.add_argument("--env-file", default=None, help="Path to .env file (default: auto-detect)")
    parser.add_argument("--no-save", action="store_true", help="Only print the token, do not update .env")
    parser.add_argument("--no-open", action="store_true", help="Do not auto-open the browser")
    args = parser.parse_args()

    env_path = find_env_file(args.env_file)
    print(f"Using .env: {env_path}")

    client_id = read_env_value(env_path, "GOOGLE_ADS_CLIENT_ID")
    client_secret = read_env_value(env_path, "GOOGLE_ADS_CLIENT_SECRET")

    if not client_id or client_id.startswith("your-"):
        print("\nERROR: GOOGLE_ADS_CLIENT_ID is missing or has a placeholder value in .env")
        print("Ask your admin for the correct value.")
        sys.exit(1)

    if not client_secret or client_secret.startswith("your-"):
        print("\nERROR: GOOGLE_ADS_CLIENT_SECRET is missing or has a placeholder value in .env")
        print("Ask your admin for the correct value.")
        sys.exit(1)

    # Create temporary client secrets file
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [_REDIRECT_URI],
        }
    }

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="google-ads-oauth-", delete=False
    )
    try:
        json.dump(client_config, tmp)
        tmp.close()

        flow = Flow.from_client_secrets_file(tmp.name, scopes=[_SCOPE])
        flow.redirect_uri = _REDIRECT_URI

        passthrough_val = hashlib.sha256(os.urandom(1024)).hexdigest()
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            state=passthrough_val,
            prompt="consent",
            include_granted_scopes="true",
        )

        print()
        print("=" * 60)
        print("  STEP 1: Open this URL in your browser")
        print("=" * 60)
        print()
        print(authorization_url)
        print()
        print("  STEP 2: Sign in with the Google account that")
        print("          has access to Google Ads")
        print()
        print("  STEP 3: Click 'Allow'")
        print()
        print(f"Waiting for callback on {_REDIRECT_URI} ...")
        print()

        if not args.no_open:
            webbrowser.open(authorization_url)

        code = get_authorization_code(passthrough_val)
        flow.fetch_token(code=code)
        refresh_token = flow.credentials.refresh_token
    finally:
        os.unlink(tmp.name)

    if not refresh_token:
        print("\nERROR: Google returned an empty refresh token.")
        print("This can happen if you already authorized this app before.")
        print("Go to https://myaccount.google.com/permissions, remove the app, and try again.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  SUCCESS")
    print("=" * 60)
    print()
    print(f"  Refresh token: {refresh_token}")
    print()

    if not args.no_save:
        update_env_value(env_path, "GOOGLE_ADS_REFRESH_TOKEN", refresh_token)
        print(f"  Saved to: {env_path}")
        print()
        print("You are done! No need to copy anything manually.")
    else:
        print("  Add this to your .env file as:")
        print(f"  GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")

    print()


if __name__ == "__main__":
    main()
