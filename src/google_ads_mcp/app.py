"""MCP application factory for the Google Ads server."""

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from google_ads_mcp.tools import register_tools

load_dotenv()

INSTRUCTIONS = (
    "Google Ads MCP server. Provides read-only access to Google Ads account data: "
    "accessible accounts, account metadata, campaigns, ad groups, keywords, search "
    "terms, segmented performance reports, bids, budgets, conversions, assets, "
    "labels, change history, and impression share. Metric tools require a "
    "customer_id parameter and accept optional date_range_days or date_from/date_to."
)


def create_mcp() -> FastMCP:
    """Create and configure the Google Ads FastMCP app."""
    mcp = FastMCP("google-ads", instructions=INSTRUCTIONS)
    register_tools(mcp)
    return mcp
