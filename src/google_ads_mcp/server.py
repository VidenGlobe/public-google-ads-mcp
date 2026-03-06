"""Google Ads MCP Server - Gives Claude access to Google Ads account data."""

import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    "google-ads",
    instructions="Google Ads MCP server. Provides read-only access to Google Ads data: campaigns, ad groups, keywords, search terms, performance trends, geographic splits, device splits, ad creative performance, demographics, and audience segments. Every tool requires a customer_id parameter to specify which account to query.",
)


def _get_google_ads_client():
    """Initialize Google Ads API client."""
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
        return GoogleAdsClient.load_from_dict(credentials)
    except Exception as e:
        print(f"Failed to initialize Google Ads client: {e}", file=sys.stderr)
        return None


def _fmt(data: Any) -> str:
    """Format data as readable JSON."""
    return json.dumps(data, indent=2, default=str)


class _ClientError(Exception):
    """Raised when the Google Ads client cannot be initialized."""


def _require_client():
    """Get Google Ads client or raise _ClientError."""
    client = _get_google_ads_client()
    if not client:
        raise _ClientError("Google Ads client not configured. Set API credentials in environment variables.")
    return client


# ---------------------------------------------------------------------------
# Existing tools (with customer_id as required parameter)
# ---------------------------------------------------------------------------


@mcp.tool()
def get_campaigns(customer_id: str) -> str:
    """List all campaigns with their status, type, budget, and last 30 days performance metrics (impressions, clicks, cost, conversions, CPA, ROAS).

    Args:
        customer_id: The Google Ads customer ID to query (e.g. "1234567890", no dashes)
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

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
            cost = row.metrics.cost_micros / 1_000_000
            campaigns.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "status": row.campaign.status.name,
                "type": row.campaign.advertising_channel_type.name,
                "daily_budget": row.campaign_budget.amount_micros / 1_000_000,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "ctr": round(row.metrics.clicks / row.metrics.impressions * 100, 2) if row.metrics.impressions else 0,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
                "roas": round(row.metrics.conversions_value / cost, 2) if cost else None,
            })
    return _fmt({"campaigns": campaigns})


@mcp.tool()
def get_ad_groups(customer_id: str, campaign_id: str) -> str:
    """List ad groups for a specific campaign with their status, bid settings, and last 30 days metrics.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: The campaign ID to get ad groups for
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

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
def get_keywords(customer_id: str, campaign_id: str | None = None, ad_group_id: str | None = None) -> str:
    """List keywords with quality scores, match types, and bid settings. Filter by campaign or ad group.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter keywords
        ad_group_id: Optional ad group ID to filter keywords
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

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
def get_performance_report(customer_id: str, campaign_id: str | None = None, days: int = 30) -> str:
    """Get daily performance metrics over a date range. Useful for trend analysis and CPA diagnostics.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter (omit for account-level)
        days: Number of days to look back (default 30, valid: 7, 14, 30, 90)
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

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
def get_search_terms(customer_id: str, campaign_id: str | None = None) -> str:
    """Get search term report showing actual queries that triggered ads. Essential for finding wasted spend and negative keyword opportunities.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

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


# ---------------------------------------------------------------------------
# New tools: geo, device, ad creative, demographics, audience
# ---------------------------------------------------------------------------


@mcp.tool()
def get_geo_performance(customer_id: str, campaign_id: str | None = None) -> str:
    """Get geographic performance breakdown by country, region, and city. Useful for identifying high/low performing locations and optimizing geo targeting.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter results
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

    ga_service = client.get_service("GoogleAdsService")
    where = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            geographic_view.country_criterion_id,
            geographic_view.location_type,
            campaign.id, campaign.name,
            geo_target_constant.name,
            geo_target_constant.canonical_name,
            geo_target_constant.target_type,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM geographic_view
        WHERE segments.date DURING LAST_30_DAYS
          {where}
        ORDER BY metrics.cost_micros DESC
        LIMIT 200
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    geos = []
    for batch in response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            geos.append({
                "geo_name": row.geo_target_constant.name,
                "canonical_name": row.geo_target_constant.canonical_name,
                "geo_type": row.geo_target_constant.target_type,
                "location_type": row.geographic_view.location_type.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "ctr": round(row.metrics.clicks / row.metrics.impressions * 100, 2) if row.metrics.impressions else 0,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
                "roas": round(row.metrics.conversions_value / cost, 2) if cost else None,
            })
    return _fmt({"filters": {"campaign_id": campaign_id}, "geo_performance": geos})


@mcp.tool()
def get_device_performance(customer_id: str, campaign_id: str | None = None) -> str:
    """Get performance breakdown by device type (mobile, desktop, tablet). Useful for identifying device-specific gaps and optimizing bid adjustments.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter results
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

    ga_service = client.get_service("GoogleAdsService")
    where = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            segments.device,
            campaign.id, campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
          {where}
        ORDER BY metrics.cost_micros DESC
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    devices = []
    for batch in response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            devices.append({
                "device": row.segments.device.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "ctr": round(row.metrics.clicks / row.metrics.impressions * 100, 2) if row.metrics.impressions else 0,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
                "roas": round(row.metrics.conversions_value / cost, 2) if cost else None,
            })
    return _fmt({"filters": {"campaign_id": campaign_id}, "device_performance": devices})


@mcp.tool()
def get_ad_performance(customer_id: str, campaign_id: str | None = None, ad_group_id: str | None = None) -> str:
    """Get ad-level creative performance including headlines, descriptions, and key metrics. Useful for identifying top/bottom performing creatives.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter results
        ad_group_id: Optional ad group ID to filter results
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

    ga_service = client.get_service("GoogleAdsService")
    where_clauses = ["ad_group_ad.status != 'REMOVED'"]
    if campaign_id:
        where_clauses.append(f"campaign.id = {campaign_id}")
    if ad_group_id:
        where_clauses.append(f"ad_group.id = {ad_group_id}")

    query = f"""
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.type,
            ad_group_ad.ad.final_urls,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.status,
            campaign.id, campaign.name,
            ad_group.id, ad_group.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM ad_group_ad
        WHERE {' AND '.join(where_clauses)}
          AND segments.date DURING LAST_30_DAYS
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    ads = []
    for batch in response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            headlines = []
            descriptions = []
            try:
                headlines = [h.text for h in row.ad_group_ad.ad.responsive_search_ad.headlines]
                descriptions = [d.text for d in row.ad_group_ad.ad.responsive_search_ad.descriptions]
            except AttributeError:
                pass
            ads.append({
                "ad_id": str(row.ad_group_ad.ad.id),
                "ad_type": row.ad_group_ad.ad.type_.name,
                "status": row.ad_group_ad.status.name,
                "headlines": headlines,
                "descriptions": descriptions,
                "final_urls": list(row.ad_group_ad.ad.final_urls),
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "ctr": round(row.metrics.clicks / row.metrics.impressions * 100, 2) if row.metrics.impressions else 0,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
                "roas": round(row.metrics.conversions_value / cost, 2) if cost else None,
            })
    return _fmt({"filters": {"campaign_id": campaign_id, "ad_group_id": ad_group_id}, "ad_performance": ads})


@mcp.tool()
def get_age_gender_performance(customer_id: str, campaign_id: str | None = None) -> str:
    """Get demographic performance breakdown by age range and gender. Useful for identifying which demographics convert best and optimizing targeting.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter results
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

    ga_service = client.get_service("GoogleAdsService")
    where = f"AND campaign.id = {campaign_id}" if campaign_id else ""

    # Age breakdown
    age_query = f"""
        SELECT
            ad_group_criterion.age_range.type,
            campaign.id, campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM age_range_view
        WHERE segments.date DURING LAST_30_DAYS
          {where}
        ORDER BY metrics.cost_micros DESC
    """
    age_response = ga_service.search_stream(customer_id=customer_id, query=age_query)
    age_data = []
    for batch in age_response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            age_data.append({
                "age_range": row.ad_group_criterion.age_range.type_.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "ctr": round(row.metrics.clicks / row.metrics.impressions * 100, 2) if row.metrics.impressions else 0,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
                "roas": round(row.metrics.conversions_value / cost, 2) if cost else None,
            })

    # Gender breakdown
    gender_query = f"""
        SELECT
            ad_group_criterion.gender.type,
            campaign.id, campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM gender_view
        WHERE segments.date DURING LAST_30_DAYS
          {where}
        ORDER BY metrics.cost_micros DESC
    """
    gender_response = ga_service.search_stream(customer_id=customer_id, query=gender_query)
    gender_data = []
    for batch in gender_response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            gender_data.append({
                "gender": row.ad_group_criterion.gender.type_.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "ctr": round(row.metrics.clicks / row.metrics.impressions * 100, 2) if row.metrics.impressions else 0,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
                "roas": round(row.metrics.conversions_value / cost, 2) if cost else None,
            })

    return _fmt({"filters": {"campaign_id": campaign_id}, "age_performance": age_data, "gender_performance": gender_data})


@mcp.tool()
def get_audience_performance(customer_id: str, campaign_id: str | None = None) -> str:
    """Get audience segment performance showing how different audiences (in-market, affinity, custom) perform. Useful for identifying high-value audiences.

    Args:
        customer_id: The Google Ads customer ID (e.g. "1234567890", no dashes)
        campaign_id: Optional campaign ID to filter results
    """
    try:
        client = _require_client()
    except _ClientError as e:
        return _fmt({"error": str(e)})

    ga_service = client.get_service("GoogleAdsService")
    where = f"AND campaign.id = {campaign_id}" if campaign_id else ""
    query = f"""
        SELECT
            campaign_audience_view.resource_name,
            campaign_criterion.criterion_id,
            campaign_criterion.display_name,
            campaign_criterion.type,
            campaign_criterion.status,
            campaign.id, campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM campaign_audience_view
        WHERE segments.date DURING LAST_30_DAYS
          {where}
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    audiences = []
    for batch in response:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1_000_000
            audiences.append({
                "audience_name": row.campaign_criterion.display_name,
                "audience_type": row.campaign_criterion.type_.name,
                "audience_status": row.campaign_criterion.status.name,
                "criterion_id": str(row.campaign_criterion.criterion_id),
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": cost,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "ctr": round(row.metrics.clicks / row.metrics.impressions * 100, 2) if row.metrics.impressions else 0,
                "cpa": round(cost / row.metrics.conversions, 2) if row.metrics.conversions else None,
                "roas": round(row.metrics.conversions_value / cost, 2) if cost else None,
            })
    return _fmt({"filters": {"campaign_id": campaign_id}, "audience_performance": audiences})


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
