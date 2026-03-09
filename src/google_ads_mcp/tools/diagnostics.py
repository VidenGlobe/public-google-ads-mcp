"""Diagnostics, pacing, and audit-oriented tools."""

from __future__ import annotations

from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

from google_ads_mcp.google_ads.client import search_rows
from google_ads_mcp.google_ads.utils import (
    asset_payload,
    build_date_clause,
    build_where,
    cost_from_micros,
    enum_name,
    error_response,
    fmt,
    id_filter,
    message_to_string,
    normalize_numeric_id,
    normalize_positive_int,
    safe_divide,
    safe_percentage,
    today_month_context,
)


def register(mcp: FastMCP) -> None:
    """Register diagnostics, audit, and pacing tools."""

    @mcp.tool()
    def get_keyword_quality_details(
        customer_id: str,
        campaign_id: str | None = None,
        ad_group_id: str | None = None,
        min_impressions: int = 0,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get keyword quality score details including expected CTR, ad relevance, and landing page experience."""
        try:
            if min_impressions < 0:
                raise ValueError("min_impressions must be 0 or greater.")
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(
                "ad_group_criterion.status != 'REMOVED'",
                "ad_group_criterion.negative = FALSE",
                f"metrics.impressions >= {min_impressions}",
                date_range.clause,
                id_filter("campaign.id", "campaign_id", campaign_id),
                id_filter("ad_group.id", "ad_group_id", ad_group_id),
            )
            query = f"""
                SELECT
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    ad_group_criterion.quality_info.quality_score,
                    ad_group_criterion.quality_info.creative_quality_score,
                    ad_group_criterion.quality_info.post_click_quality_score,
                    ad_group_criterion.quality_info.search_predicted_ctr,
                    ad_group.id, ad_group.name,
                    campaign.id, campaign.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.average_cpc
                FROM keyword_view
                WHERE {where_clause}
                ORDER BY ad_group_criterion.quality_info.quality_score ASC
            """
            keyword_quality_details = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                keyword_quality_details.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "ad_group_id": str(row.ad_group.id),
                        "ad_group_name": row.ad_group.name,
                        "keyword_text": row.ad_group_criterion.keyword.text,
                        "match_type": enum_name(row.ad_group_criterion.keyword.match_type),
                        "status": enum_name(row.ad_group_criterion.status),
                        "quality_score": row.ad_group_criterion.quality_info.quality_score,
                        "expected_ctr": enum_name(row.ad_group_criterion.quality_info.search_predicted_ctr),
                        "ad_relevance": enum_name(row.ad_group_criterion.quality_info.creative_quality_score),
                        "landing_page_experience": enum_name(
                            row.ad_group_criterion.quality_info.post_click_quality_score
                        ),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "average_cpc": cost_from_micros(row.metrics.average_cpc),
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                    }
                )
            return fmt(
                {
                    "filters": {
                        "campaign_id": campaign_id,
                        "ad_group_id": ad_group_id,
                        "min_impressions": min_impressions,
                    },
                    "date_range": date_range.as_dict(),
                    "keyword_quality_details": keyword_quality_details,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_ad_extensions(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get campaign-level and account-level asset performance for extensions."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            campaign_asset_where = build_where(
                "campaign_asset.status != 'REMOVED'",
                date_range.clause,
                id_filter("campaign.id", "campaign_id", campaign_id),
            )
            campaign_asset_query = f"""
                SELECT
                    asset.id,
                    asset.name,
                    asset.type,
                    asset.sitelink_asset.description1,
                    asset.sitelink_asset.description2,
                    asset.sitelink_asset.link_text,
                    asset.callout_asset.callout_text,
                    asset.structured_snippet_asset.header,
                    asset.structured_snippet_asset.values,
                    campaign.id, campaign.name,
                    campaign_asset.field_type,
                    campaign_asset.status,
                    metrics.impressions, metrics.clicks, metrics.cost_micros
                FROM campaign_asset
                WHERE {campaign_asset_where}
                ORDER BY asset.type, metrics.impressions DESC
            """
            customer_asset_query = f"""
                SELECT
                    asset.id,
                    asset.name,
                    asset.type,
                    asset.sitelink_asset.description1,
                    asset.sitelink_asset.description2,
                    asset.sitelink_asset.link_text,
                    asset.callout_asset.callout_text,
                    asset.structured_snippet_asset.header,
                    asset.structured_snippet_asset.values,
                    customer_asset.field_type,
                    customer_asset.status,
                    metrics.impressions, metrics.clicks
                FROM customer_asset
                WHERE {build_where("customer_asset.status != 'REMOVED'", date_range.clause)}
                ORDER BY asset.type, metrics.impressions DESC
            """
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "campaign_assets": [asset_payload(row, "campaign") for row in search_rows(customer_id, campaign_asset_query)],
                    "account_assets": [asset_payload(row, "account") for row in search_rows(customer_id, customer_asset_query)],
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_bid_strategies(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get campaign bidding strategy details and relevant performance context."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(
                "campaign.status != 'REMOVED'",
                date_range.clause,
                id_filter("campaign.id", "campaign_id", campaign_id),
            )
            query = f"""
                SELECT
                    campaign.id, campaign.name, campaign.status,
                    campaign.bidding_strategy_type,
                    campaign.target_cpa.target_cpa_micros,
                    campaign.target_roas.target_roas,
                    campaign.maximize_conversions.target_cpa_micros,
                    campaign.maximize_conversion_value.target_roas,
                    campaign_budget.amount_micros,
                    metrics.conversions, metrics.conversions_value,
                    metrics.cost_micros, metrics.clicks, metrics.impressions,
                    metrics.search_impression_share,
                    metrics.search_budget_lost_impression_share,
                    metrics.search_rank_lost_impression_share
                FROM campaign
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            bid_strategies = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                bid_strategies.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "status": enum_name(row.campaign.status),
                        "bidding_strategy_type": enum_name(row.campaign.bidding_strategy_type),
                        "target_cpa": cost_from_micros(row.campaign.target_cpa.target_cpa_micros),
                        "maximize_conversions_target_cpa": cost_from_micros(
                            row.campaign.maximize_conversions.target_cpa_micros
                        ),
                        "target_roas": row.campaign.target_roas.target_roas,
                        "maximize_conversion_value_target_roas": row.campaign.maximize_conversion_value.target_roas,
                        "daily_budget": cost_from_micros(row.campaign_budget.amount_micros),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "search_impression_share": row.metrics.search_impression_share,
                        "search_budget_lost_impression_share": row.metrics.search_budget_lost_impression_share,
                        "search_rank_lost_impression_share": row.metrics.search_rank_lost_impression_share,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "bid_strategies": bid_strategies,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_budget_pacing(customer_id: str, campaign_id: str | None = None) -> str:
        """Get month-to-date spend versus budget with projected end-of-month pacing."""
        try:
            normalized_campaign_id = normalize_numeric_id("campaign_id", campaign_id)
            month_start, yesterday, days_in_month = today_month_context()
            if yesterday < month_start:
                return fmt(
                    {
                        "filters": {"campaign_id": normalized_campaign_id},
                        "month_start": month_start.isoformat(),
                        "through_date": None,
                        "days_elapsed": 0,
                        "days_remaining": days_in_month,
                        "summary": {
                            "total_daily_budget": 0.0,
                            "total_monthly_budget_target": 0.0,
                            "total_mtd_spend": 0.0,
                            "projected_eom_spend": 0.0,
                            "needed_daily_spend_to_hit_target": 0.0,
                        },
                        "campaign_pacing": [],
                    }
                )
            where_clause = build_where(
                "campaign.status = 'ENABLED'",
                f"segments.date BETWEEN '{month_start.isoformat()}' AND '{yesterday.isoformat()}'",
                id_filter("campaign.id", "campaign_id", normalized_campaign_id),
            )
            query = f"""
                SELECT
                    campaign.id, campaign.name, campaign.status,
                    campaign_budget.amount_micros,
                    metrics.cost_micros, metrics.conversions,
                    metrics.impressions, metrics.clicks
                FROM campaign
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            days_elapsed = (yesterday - month_start).days + 1
            days_remaining = max(days_in_month - yesterday.day, 0)
            campaign_pacing = []
            totals = {
                "total_daily_budget": 0.0,
                "total_monthly_budget_target": 0.0,
                "total_mtd_spend": 0.0,
                "projected_eom_spend": 0.0,
                "needed_daily_spend_to_hit_target": 0.0,
            }
            for row in search_rows(customer_id, query):
                daily_budget = cost_from_micros(row.campaign_budget.amount_micros)
                mtd_spend = cost_from_micros(row.metrics.cost_micros)
                monthly_budget_target = round(daily_budget * days_in_month, 2)
                avg_daily_spend = safe_divide(mtd_spend, days_elapsed) or 0.0
                projected_eom_spend = round(avg_daily_spend * days_in_month, 2)
                needed_daily_spend = 0.0
                if days_remaining:
                    needed_daily_spend = round(max(monthly_budget_target - mtd_spend, 0) / days_remaining, 2)
                if monthly_budget_target == 0:
                    pacing_status = "no_budget"
                else:
                    pacing_ratio = projected_eom_spend / monthly_budget_target
                    if pacing_ratio > 1.05:
                        pacing_status = "over"
                    elif pacing_ratio < 0.95:
                        pacing_status = "under"
                    else:
                        pacing_status = "on_track"
                campaign_pacing.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "status": enum_name(row.campaign.status),
                        "daily_budget": daily_budget,
                        "monthly_budget_target": monthly_budget_target,
                        "mtd_spend": mtd_spend,
                        "avg_daily_spend": avg_daily_spend,
                        "days_elapsed": days_elapsed,
                        "days_remaining": days_remaining,
                        "projected_eom_spend": projected_eom_spend,
                        "needed_daily_spend_to_hit_target": needed_daily_spend,
                        "pacing_status": pacing_status,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "conversions": row.metrics.conversions,
                    }
                )
                totals["total_daily_budget"] += daily_budget
                totals["total_monthly_budget_target"] += monthly_budget_target
                totals["total_mtd_spend"] += mtd_spend
                totals["projected_eom_spend"] += projected_eom_spend
                totals["needed_daily_spend_to_hit_target"] += needed_daily_spend
            return fmt(
                {
                    "filters": {"campaign_id": normalized_campaign_id},
                    "month_start": month_start.isoformat(),
                    "through_date": yesterday.isoformat(),
                    "days_elapsed": days_elapsed,
                    "days_remaining": days_remaining,
                    "summary": {key: round(value, 2) for key, value in totals.items()},
                    "campaign_pacing": campaign_pacing,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_landing_page_performance(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get landing page URL performance including speed and mobile friendliness metrics."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(date_range.clause, id_filter("campaign.id", "campaign_id", campaign_id))
            query = f"""
                SELECT
                    landing_page_view.unexpanded_final_url,
                    campaign.id, campaign.name,
                    metrics.impressions, metrics.clicks, metrics.cost_micros,
                    metrics.conversions, metrics.conversions_value,
                    metrics.speed_score,
                    metrics.mobile_friendly_clicks_percentage
                FROM landing_page_view
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
                LIMIT 100
            """
            landing_page_performance = []
            for row in search_rows(customer_id, query):
                cost = cost_from_micros(row.metrics.cost_micros)
                landing_page_performance.append(
                    {
                        "landing_page_url": row.landing_page_view.unexpanded_final_url,
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": cost,
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "speed_score": row.metrics.speed_score,
                        "mobile_friendly_clicks_percentage": row.metrics.mobile_friendly_clicks_percentage,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                        "cpa": safe_divide(cost, row.metrics.conversions),
                        "roas": safe_divide(row.metrics.conversions_value, cost),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "landing_page_performance": landing_page_performance,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_change_history(customer_id: str, days_back: int = 7) -> str:
        """Get recent account changes for anomaly detection and auditing."""
        try:
            normalized_days_back = normalize_positive_int("days_back", days_back)
            threshold = datetime.now() - timedelta(days=normalized_days_back)
            threshold_str = threshold.strftime("%Y-%m-%d %H:%M:%S")
            query = f"""
                SELECT
                    change_event.change_date_time,
                    change_event.change_resource_type,
                    change_event.resource_change_operation,
                    change_event.changed_fields,
                    change_event.user_email,
                    change_event.old_resource,
                    change_event.new_resource,
                    campaign.id, campaign.name,
                    ad_group.id, ad_group.name
                FROM change_event
                WHERE change_event.change_date_time >= '{threshold_str}'
                ORDER BY change_event.change_date_time DESC
                LIMIT 200
            """
            change_history = []
            for row in search_rows(customer_id, query):
                change_history.append(
                    {
                        "change_date_time": str(row.change_event.change_date_time),
                        "resource_type": enum_name(row.change_event.change_resource_type),
                        "operation": enum_name(row.change_event.resource_change_operation),
                        "changed_fields": message_to_string(row.change_event.changed_fields),
                        "user_email": row.change_event.user_email,
                        "old_resource": message_to_string(row.change_event.old_resource),
                        "new_resource": message_to_string(row.change_event.new_resource),
                        "campaign_id": str(row.campaign.id) if row.campaign.id else None,
                        "campaign_name": row.campaign.name if row.campaign.name else None,
                        "ad_group_id": str(row.ad_group.id) if row.ad_group.id else None,
                        "ad_group_name": row.ad_group.name if row.ad_group.name else None,
                    }
                )
            return fmt({"days_back": normalized_days_back, "change_history": change_history})
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_negative_keywords(customer_id: str, campaign_id: str | None = None) -> str:
        """Get negative keywords at both campaign and ad group levels."""
        try:
            campaign_where_clause = build_where(
                "campaign_criterion.type = 'KEYWORD'",
                "campaign_criterion.negative = TRUE",
                id_filter("campaign.id", "campaign_id", campaign_id),
            )
            ad_group_where_clause = build_where(
                "ad_group_criterion.type = 'KEYWORD'",
                "ad_group_criterion.negative = TRUE",
                id_filter("campaign.id", "campaign_id", campaign_id),
            )
            campaign_query = f"""
                SELECT
                    campaign_criterion.keyword.text,
                    campaign_criterion.keyword.match_type,
                    campaign_criterion.negative,
                    campaign.id, campaign.name
                FROM campaign_criterion
                WHERE {campaign_where_clause}
                ORDER BY campaign.name, campaign_criterion.keyword.text
            """
            ad_group_query = f"""
                SELECT
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.negative,
                    ad_group.id, ad_group.name,
                    campaign.id, campaign.name
                FROM ad_group_criterion
                WHERE {ad_group_where_clause}
                ORDER BY campaign.name, ad_group.name, ad_group_criterion.keyword.text
            """
            campaign_negative_keywords = []
            for row in search_rows(customer_id, campaign_query):
                campaign_negative_keywords.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "keyword_text": row.campaign_criterion.keyword.text,
                        "match_type": enum_name(row.campaign_criterion.keyword.match_type),
                        "negative": row.campaign_criterion.negative,
                    }
                )
            ad_group_negative_keywords = []
            for row in search_rows(customer_id, ad_group_query):
                ad_group_negative_keywords.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "ad_group_id": str(row.ad_group.id),
                        "ad_group_name": row.ad_group.name,
                        "keyword_text": row.ad_group_criterion.keyword.text,
                        "match_type": enum_name(row.ad_group_criterion.keyword.match_type),
                        "negative": row.ad_group_criterion.negative,
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "campaign_negative_keywords": campaign_negative_keywords,
                    "ad_group_negative_keywords": ad_group_negative_keywords,
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_impression_share_data(
        customer_id: str,
        campaign_id: str | None = None,
        date_range_days: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> str:
        """Get search impression share and lost impression share metrics."""
        try:
            date_range = build_date_clause(date_range_days=date_range_days, date_from=date_from, date_to=date_to)
            where_clause = build_where(
                "campaign.advertising_channel_type = 'SEARCH'",
                date_range.clause,
                id_filter("campaign.id", "campaign_id", campaign_id),
            )
            query = f"""
                SELECT
                    campaign.id, campaign.name,
                    metrics.search_impression_share,
                    metrics.search_budget_lost_impression_share,
                    metrics.search_rank_lost_impression_share,
                    metrics.search_exact_match_impression_share,
                    metrics.search_top_impression_share,
                    metrics.search_absolute_top_impression_share,
                    metrics.cost_micros, metrics.impressions, metrics.clicks
                FROM campaign
                WHERE {where_clause}
                ORDER BY metrics.cost_micros DESC
            """
            impression_share_data = []
            for row in search_rows(customer_id, query):
                impression_share_data.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "search_impression_share": row.metrics.search_impression_share,
                        "search_budget_lost_impression_share": row.metrics.search_budget_lost_impression_share,
                        "search_rank_lost_impression_share": row.metrics.search_rank_lost_impression_share,
                        "search_exact_match_impression_share": row.metrics.search_exact_match_impression_share,
                        "search_top_impression_share": row.metrics.search_top_impression_share,
                        "search_absolute_top_impression_share": row.metrics.search_absolute_top_impression_share,
                        "cost": cost_from_micros(row.metrics.cost_micros),
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "ctr": safe_percentage(row.metrics.clicks, row.metrics.impressions),
                    }
                )
            return fmt(
                {
                    "filters": {"campaign_id": campaign_id},
                    "date_range": date_range.as_dict(),
                    "impression_share_data": impression_share_data,
                }
            )
        except Exception as exc:
            return error_response(exc)
