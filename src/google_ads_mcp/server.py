"""Google Ads MCP Server - Gives Claude access to Google Ads account data."""

from google_ads_mcp.app import create_mcp

mcp = create_mcp()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
