"""Google Ads MCP Server - Gives Claude access to Google Ads account data."""

import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from google_ads_mcp.mock_data import (
    MOCK_ACCOUNT_NAME,
    MOCK_CUSTOMER_ID,
    get_mock_ad_groups,
    get_mock_campaigns,
    get_mock_keywords,
    get_mock_performance,
    get_mock_search_terms,
)

load_dotenv()

mcp = FastMCP(
    "google-ads",
    instructions="Google Ads MCP server. Provides read-only access to campaign, ad group, keyword, and performance data. Use these tools to analyze ad account performance, find wasted spend, diagnose CPA issues, and generate reports.",
)

USE_MOCK = os.getenv("GOOGLE_ADS_USE_MOCK", "true").lower() == "true"


def _get_google_ads_client():
    """Initialize Google Ads API client (when not using mock data)."""
    if USE_MOCK:
        return None
    try:
        from google.ads.googleads.client import GoogleAdsClient

        credentials = {
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
            "use_proto_plus": True,
        }
        return GoogleAdsClient.load_from_dict(credentials)
    except Exception as e:
        print(f"Failed to initialize Google Ads client: {e}", file=sys.stderr)
        return None


def _fmt(data: Any) -> str:
    """Format data as readable JSON."""
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def get_account_info() -> str:
    """Get basic account information including customer ID and account name."""
    if USE_MOCK:
        return _fmt({
            "customer_id": MOCK_CUSTOMER_ID,
            "account_name": MOCK_ACCOUNT_NAME,
            "mode": "mock_data",
            "note": "Using mock data for testing. Set GOOGLE_ADS_USE_MOCK=false and configure API credentials for live data.",
        })
    return _fmt({"customer_id": os.getenv("GOOGLE_ADS_CUSTOMER_ID"), "mode": "live"})


@mcp.tool()
def get_campaigns() -> str:
    """List all campaigns with their status, type, budget, bidding strategy, and last 30 days performance metrics (impressions, clicks, cost, conversions, CPA, ROAS)."""
    if USE_MOCK:
        campaigns = get_mock_campaigns()
        return _fmt({"account": MOCK_ACCOUNT_NAME, "campaigns": campaigns})

    client = _get_google_ads_client()
    if not client:
        return _fmt({"error": "Google Ads client not configured. Set credentials or use GOOGLE_ADS_USE_MOCK=true."})

    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
            campaign.id, campaign.name, campaign.status,
            campaign.advertising_channel_type,
            campaign_budget.amount_micros,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY metrics.cost_micros DESC
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    campaigns = []
    for batch in response:
        for row in batch.results:
            campaigns.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "status": row.campaign.status.name,
                "type": row.campaign.advertising_channel_type.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
            })
    return _fmt({"campaigns": campaigns})


@mcp.tool()
def get_ad_groups(campaign_id: str) -> str:
    """List ad groups for a specific campaign with their status and bid settings.

    Args:
        campaign_id: The campaign ID to get ad groups for (e.g. "1001")
    """
    if USE_MOCK:
        groups = get_mock_ad_groups(campaign_id)
        return _fmt({"campaign_id": campaign_id, "ad_groups": groups})

    client = _get_google_ads_client()
    if not client:
        return _fmt({"error": "Google Ads client not configured."})

    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            ad_group.id, ad_group.name, ad_group.status,
            ad_group.cpc_bid_micros,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions
        FROM ad_group
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING LAST_30_DAYS
        ORDER BY metrics.cost_micros DESC
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    groups = []
    for batch in response:
        for row in batch.results:
            groups.append({
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "status": row.ad_group.status.name,
                "cpc_bid": row.ad_group.cpc_bid_micros / 1_000_000,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions,
            })
    return _fmt({"campaign_id": campaign_id, "ad_groups": groups})


@mcp.tool()
def get_keywords(campaign_id: str | None = None, ad_group_id: str | None = None) -> str:
    """List keywords with quality scores, match types, and bid settings. Filter by campaign or ad group.

    Args:
        campaign_id: Optional campaign ID to filter keywords
        ad_group_id: Optional ad group ID to filter keywords
    """
    if USE_MOCK:
        keywords = get_mock_keywords(campaign_id, ad_group_id)
        return _fmt({"filters": {"campaign_id": campaign_id, "ad_group_id": ad_group_id}, "keywords": keywords})

    client = _get_google_ads_client()
    if not client:
        return _fmt({"error": "Google Ads client not configured."})

    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
    ga_service = client.get_service("GoogleAdsService")
    where_clauses = ["ad_group_criterion.type = 'KEYWORD'"]
    if campaign_id:
        where_clauses.append(f"campaign.id = {campaign_id}")
    if ad_group_id:
        where_clauses.append(f"ad_group.id = {ad_group_id}")

    query = f"""
        SELECT
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.effective_cpc_bid_micros,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions
        FROM keyword_view
        WHERE {' AND '.join(where_clauses)}
          AND segments.date DURING LAST_30_DAYS
        ORDER BY metrics.cost_micros DESC
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    keywords = []
    for batch in response:
        for row in batch.results:
            keywords.append({
                "keyword_text": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "status": row.ad_group_criterion.status.name,
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "cpc_bid": row.ad_group_criterion.effective_cpc_bid_micros / 1_000_000,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions,
            })
    return _fmt({"keywords": keywords})


@mcp.tool()
def get_performance_report(campaign_id: str | None = None, days: int = 30) -> str:
    """Get daily performance metrics (impressions, clicks, cost, conversions, CPA, ROAS) over a date range. Useful for trend analysis and CPA diagnostics.

    Args:
        campaign_id: Optional campaign ID to filter (omit for account-level)
        days: Number of days to look back (default 30)
    """
    if USE_MOCK:
        metrics = get_mock_performance(campaign_id, days)
        return _fmt({
            "filters": {"campaign_id": campaign_id, "days": days},
            "daily_metrics": metrics,
            "summary": {
                "total_cost": round(sum(d["cost"] for d in metrics), 2),
                "total_conversions": sum(d["conversions"] for d in metrics),
                "total_clicks": sum(d["clicks"] for d in metrics),
                "avg_cpa": round(sum(d["cost"] for d in metrics) / max(1, sum(d["conversions"] for d in metrics)), 2),
            },
        })

    client = _get_google_ads_client()
    if not client:
        return _fmt({"error": "Google Ads client not configured."})

    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
    ga_service = client.get_service("GoogleAdsService")
    where = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            segments.date,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
          {where}
        ORDER BY segments.date ASC
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    metrics = []
    for batch in response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            metrics.append({
                "date": str(row.segments.date),
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": conversions,
                "conversion_value": row.metrics.conversions_value,
                "cpa": round(cost / conversions, 2) if conversions else None,
            })
    return _fmt({"daily_metrics": metrics})


@mcp.tool()
def get_search_terms(campaign_id: str | None = None) -> str:
    """Get search term report showing actual queries that triggered ads. Essential for finding wasted spend and negative keyword opportunities.

    Args:
        campaign_id: Optional campaign ID to filter
    """
    if USE_MOCK:
        terms = get_mock_search_terms(campaign_id)
        zero_conv = [t for t in terms if t["conversions"] == 0]
        wasted = sum(t["cost"] for t in zero_conv)
        return _fmt({
            "filters": {"campaign_id": campaign_id},
            "search_terms": terms,
            "wasted_spend_summary": {
                "zero_conversion_terms": len(zero_conv),
                "wasted_spend": round(wasted, 2),
                "terms": [t["search_term"] for t in zero_conv],
            },
        })

    client = _get_google_ads_client()
    if not client:
        return _fmt({"error": "Google Ads client not configured."})

    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
    ga_service = client.get_service("GoogleAdsService")
    where = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            search_term_view.search_term,
            campaign.id, ad_group.id,
            search_term_view.status,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE segments.date DURING LAST_30_DAYS
          {where}
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    terms = []
    for batch in response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            terms.append({
                "search_term": row.search_term_view.search_term,
                "campaign_id": str(row.campaign.id),
                "ad_group_id": str(row.ad_group.id),
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
            })
    return _fmt({"search_terms": terms})


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
