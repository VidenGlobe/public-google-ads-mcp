"""Reporting and segmentation tools."""

from mcp.server.fastmcp import FastMCP

from google_ads_mcp.google_ads.client import search_rows
from google_ads_mcp.google_ads.utils import (
    build_date_clause,
    build_where,
    cost_from_micros,
    enum_name,
    error_response,
    fmt,
    id_filter,
    normalize_numeric_id,
    safe_divide,
    safe_percentage,
)


def register(mcp: FastMCP) -> None:
    """Register core reporting tools."""

    @mcp.tool()
    def get_campaigns(
        customer_id: str,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """List campaigns with status, type, budget, and performance metrics for the requested date range."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            query = f"""
                SELECT
                    campaign.id, campaign.name, campaign.status,
                    campaign.advertising_channel_type,
                    campaign_budget.amount_micros,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.conversions_value
                FROM campaign
                WHERE {date_range.clause}
                ORDER BY metrics.cost_micros DESC
            """
            campaigns = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                campaigns.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "status": enum_name(row.campaign.status),
                        "type": enum_name(row.campaign.advertising_channel_type),
                        "daily_budget": cost_from_micros(row.campaign_budget.amount_micros),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt({"date_range": date_range.as_dict(), "campaigns": campaigns})
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_ad_groups(
        customer_id: str,
        campaign_id: str,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """List ad groups for a campaign with status, bid settings, and performance metrics."""
        try:
            normalized_campaign_id = normalize_numeric_id("campaign_id", campaign_id)
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(f"campaign.id = {normalized_campaign_id}", date_range.clause)
            query = f"""
                SELECT
                    ad_group.id, ad_group.name, ad_group.status,
                    ad_group.cpc_bid_micros,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions
                FROM ad_group
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            ad_groups = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                ad_groups.append(
                    {
                        "ad_group_id": str(row.ad_group.id),
                        "ad_group_name": row.ad_group.name,
                        "status": enum_name(row.ad_group.status),
                        "cpc_bid": cost_from_micros(row.ad_group.cpc_bid_micros),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": normalized_campaign_id},
                    "date_range": date_range.as_dict(),
                    "ad_groups": ad_groups,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_keywords(
        customer_id: str,
        campaign_id: str | None = None,
        ad_group_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """List positive keywords with match types, quality scores, bids, and performance metrics."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(
                "ad_group_criterion.type = 'KEYWORD'",
                "ad_group_criterion.negative = FALSE",
                date_range.clause,
                id_filter("campaign.id", "campaign_id", campaign_id),
                id_filter("ad_group.id", "ad_group_id", ad_group_id),
            )
            query = f"""
                SELECT
                    campaign.id, campaign.name,
                    ad_group.id, ad_group.name,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    ad_group_criterion.quality_info.quality_score,
                    ad_group_criterion.effective_cpc_bid_micros,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions
                FROM keyword_view
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            keywords = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                keywords.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "ad_group_id": str(row.ad_group.id),
                        "ad_group_name": row.ad_group.name,
                        "keyword_text": row.ad_group_criterion.keyword.text,
                        "match_type": enum_name(row.ad_group_criterion.keyword.match_type),
                        "status": enum_name(row.ad_group_criterion.status),
                        "quality_score": row.ad_group_criterion.quality_info.quality_score,
                        "cpc_bid": cost_from_micros(row.ad_group_criterion.effective_cpc_bid_micros),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id, "ad_group_id": ad_group_id},
                    "date_range": date_range.as_dict(),
                    "keywords": keywords,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_performance_report(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get daily performance metrics over a resolved date range for trend analysis."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
            query = f"""
                SELECT
                    segments.date,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.conversions_value
                FROM campaign
                WHERE {where_clause}
                ORDER BY segments.date ASC
            """
            daily_metrics = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                daily_metrics.append(
                    {
                        "date": str(row.segments.date),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "daily_metrics": daily_metrics,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_search_terms(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get search term performance to identify wasted spend and negative keyword opportunities."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
            query = f"""
                SELECT
                    search_term_view.search_term,
                    search_term_view.status,
                    campaign.id, campaign.name,
                    ad_group.id, ad_group.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions
                FROM search_term_view
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
                LIMIT 100
            """
            search_terms = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                search_terms.append(
                    {
                        "search_term": row.search_term_view.search_term,
                        "status": enum_name(row.search_term_view.status),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "ad_group_id": str(row.ad_group.id),
                        "ad_group_name": row.ad_group.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "search_terms": search_terms,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_geo_performance(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get geographic performance breakdown by location."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
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
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
                LIMIT 200
            """
            geo_performance = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                geo_performance.append(
                    {
                        "geo_name": row.geo_target_constant.name,
                        "canonical_name": row.geo_target_constant.canonical_name,
                        "geo_type": row.geo_target_constant.target_type,
                        "location_type": enum_name(row.geographic_view.location_type),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "geo_performance": geo_performance,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_device_performance(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get performance breakdown by device type."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
            query = f"""
                SELECT
                    segments.device,
                    campaign.id, campaign.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.conversions_value
                FROM campaign
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            device_performance = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                device_performance.append(
                    {
                        "device": enum_name(row.segments.device),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "device_performance": device_performance,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_ad_performance(
        customer_id: str,
        campaign_id: str | None = None,
        ad_group_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get ad-level creative performance including headlines, descriptions, and metrics."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(
                "ad_group_ad.status != 'REMOVED'",
                date_range.clause,
                id_filter("campaign.id", "campaign_id", campaign_id),
                id_filter("ad_group.id", "ad_group_id", ad_group_id),
            )
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
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
                LIMIT 100
            """
            ad_performance = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                ad_performance.append(
                    {
                        "ad_id": str(row.ad_group_ad.ad.id),
                        "ad_type": enum_name(row.ad_group_ad.ad.type_),
                        "status": enum_name(row.ad_group_ad.status),
                        "headlines": [headline.text for headline in row.ad_group_ad.ad.responsive_search_ad.headlines],
                        "descriptions": [
                            description.text for description in row.ad_group_ad.ad.responsive_search_ad.descriptions
                        ],
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
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id, "ad_group_id": ad_group_id},
                    "date_range": date_range.as_dict(),
                    "ad_performance": ad_performance,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_age_gender_performance(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get age range and gender performance breakdowns."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
            age_query = f"""
                SELECT
                    ad_group_criterion.age_range.type,
                    campaign.id, campaign.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.conversions_value
                FROM age_range_view
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            age_performance = []
            for row in search_rows(customer_id, age_query):
                cost = cost_from_micros(row.metrics.cost_micros)
                age_performance.append(
                    {
                        "age_range": enum_name(row.ad_group_criterion.age_range.type_),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            gender_query = f"""
                SELECT
                    ad_group_criterion.gender.type,
                    campaign.id, campaign.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.conversions_value
                FROM gender_view
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            gender_performance = []
            for row in search_rows(customer_id, gender_query):
                cost = cost_from_micros(row.metrics.cost_micros)
                gender_performance.append(
                    {
                        "gender": enum_name(row.ad_group_criterion.gender.type_),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "age_performance": age_performance,
                    "gender_performance": gender_performance,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_audience_performance(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get audience segment performance for campaign audiences."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
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
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
                LIMIT 100
            """
            audience_performance = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                audience_performance.append(
                    {
                        "resource_name": row.campaign_audience_view.resource_name,
                        "audience_name": row.campaign_criterion.display_name,
                        "audience_type": enum_name(row.campaign_criterion.type_),
                        "audience_status": enum_name(row.campaign_criterion.status),
                        "criterion_id": str(row.campaign_criterion.criterion_id),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "audience_performance": audience_performance,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_hourly_performance(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get performance by hour of day and day of week."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
            query = f"""
                SELECT
                    segments.day_of_week,
                    segments.hour,
                    campaign.id, campaign.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.conversions_value
                FROM campaign
                WHERE {where_clause}
                ORDER BY segments.day_of_week, segments.hour
            """
            hourly_performance = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                hourly_performance.append(
                    {
                        "day_of_week": enum_name(row.segments.day_of_week),
                        "hour": row.segments.hour,
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "hourly_performance": hourly_performance,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_search_term_keyword_mapping(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Map search terms to the keywords that triggered them."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
            query = f"""
                SELECT
                    search_term_view.search_term,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    campaign.id, campaign.name,
                    ad_group.id, ad_group.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions
                FROM search_term_view
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
                LIMIT 500
            """
            mapping = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                mapping.append(
                    {
                        "search_term": row.search_term_view.search_term,
                        "keyword_text": row.ad_group_criterion.keyword.text,
                        "match_type": enum_name(row.ad_group_criterion.keyword.match_type),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "ad_group_id": str(row.ad_group.id),
                        "ad_group_name": row.ad_group.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "search_term_keyword_mapping": mapping,
                }
            )
        except Exception as exc:
            return error_response(exc)
