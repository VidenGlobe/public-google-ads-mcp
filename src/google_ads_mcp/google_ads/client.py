"""Google Ads client initialization and query execution helpers."""

from __future__ import annotations

import os
import sys
from typing import Any

from google_ads_mcp.google_ads.utils import normalize_customer_id


class ClientError(Exception):
    """Raised when the Google Ads client cannot be initialized."""


# Module-level singleton — initialized once, reused across all tool calls.
_client = None


def get_google_ads_client():
    """Return the cached Google Ads API client, initializing it on first call."""
    global _client
    if _client is not None:
        return _client
    try:
        from google.ads.googleads.client import GoogleAdsClient

        credentials = {
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "use_proto_plus": True,
        }
        _client = GoogleAdsClient.load_from_dict(credentials)
        return _client
    except Exception as exc:
        print(f"Failed to initialize Google Ads client: {exc}", file=sys.stderr)
        return None


def _reset_client() -> None:
    """Clear the cached client (useful for tests or credential rotation)."""
    global _client
    _client = None


def require_client():
    """Get the cached Google Ads client or raise ClientError."""
    client = get_google_ads_client()
    if not client:
        raise ClientError("Google Ads client not configured. Set API credentials in environment variables.")
    return client


def search_rows(customer_id: str, query: str) -> list[Any]:
    """Execute a streaming GAQL query and flatten the result rows."""
    client = require_client()
    ga_service = client.get_service("GoogleAdsService")
    normalized_customer_id = normalize_customer_id(customer_id)
    rows = []
    for batch in ga_service.search_stream(customer_id=normalized_customer_id, query=query):
        rows.extend(batch.results)
    return rows


def manager_customer_id() -> str:
    """Return the configured MCC/login customer ID."""
    login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if not login_customer_id:
        raise ClientError("GOOGLE_ADS_LOGIN_CUSTOMER_ID is not set.")
    return normalize_customer_id(login_customer_id)
