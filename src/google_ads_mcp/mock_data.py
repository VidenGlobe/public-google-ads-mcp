"""Mock Google Ads data for testing without API credentials."""

from datetime import datetime, timedelta
import random

MOCK_CUSTOMER_ID = "123-456-7890"
MOCK_ACCOUNT_NAME = "Demo E-Commerce Store"

CAMPAIGNS = [
    {
        "id": "1001",
        "name": "Brand - Exact Match",
        "status": "ENABLED",
        "type": "SEARCH",
        "budget_amount_micros": 50_000_000,  # $50/day
        "bidding_strategy": "TARGET_CPA",
        "target_cpa_micros": 15_000_000,  # $15
    },
    {
        "id": "1002",
        "name": "Non-Brand - Broad Match",
        "status": "ENABLED",
        "type": "SEARCH",
        "budget_amount_micros": 100_000_000,  # $100/day
        "bidding_strategy": "MAXIMIZE_CONVERSIONS",
        "target_cpa_micros": None,
    },
    {
        "id": "1003",
        "name": "Shopping - All Products",
        "status": "ENABLED",
        "type": "SHOPPING",
        "budget_amount_micros": 200_000_000,  # $200/day
        "bidding_strategy": "TARGET_ROAS",
        "target_cpa_micros": None,
    },
    {
        "id": "1004",
        "name": "Display - Remarketing",
        "status": "ENABLED",
        "type": "DISPLAY",
        "budget_amount_micros": 30_000_000,  # $30/day
        "bidding_strategy": "TARGET_CPA",
        "target_cpa_micros": 8_000_000,  # $8
    },
    {
        "id": "1005",
        "name": "Performance Max - Holiday",
        "status": "PAUSED",
        "type": "PERFORMANCE_MAX",
        "budget_amount_micros": 150_000_000,
        "bidding_strategy": "MAXIMIZE_CONVERSION_VALUE",
        "target_cpa_micros": None,
    },
]

AD_GROUPS = {
    "1001": [
        {"id": "2001", "name": "Brand - Core Terms", "status": "ENABLED", "cpc_bid_micros": 2_000_000},
        {"id": "2002", "name": "Brand - Product Names", "status": "ENABLED", "cpc_bid_micros": 1_500_000},
    ],
    "1002": [
        {"id": "2003", "name": "Running Shoes - Broad", "status": "ENABLED", "cpc_bid_micros": 3_000_000},
        {"id": "2004", "name": "Athletic Apparel", "status": "ENABLED", "cpc_bid_micros": 2_500_000},
        {"id": "2005", "name": "Workout Equipment", "status": "PAUSED", "cpc_bid_micros": 4_000_000},
    ],
    "1003": [
        {"id": "2006", "name": "All Products", "status": "ENABLED", "cpc_bid_micros": 1_000_000},
    ],
    "1004": [
        {"id": "2007", "name": "Cart Abandoners", "status": "ENABLED", "cpc_bid_micros": 500_000},
        {"id": "2008", "name": "Past Purchasers", "status": "ENABLED", "cpc_bid_micros": 300_000},
    ],
}

KEYWORDS = {
    "2001": [
        {"id": "3001", "text": "demo store", "match_type": "EXACT", "status": "ENABLED", "quality_score": 9, "cpc_bid_micros": 1_500_000},
        {"id": "3002", "text": "demo ecommerce", "match_type": "EXACT", "status": "ENABLED", "quality_score": 8, "cpc_bid_micros": 1_200_000},
    ],
    "2002": [
        {"id": "3003", "text": "demo running shoes", "match_type": "EXACT", "status": "ENABLED", "quality_score": 7, "cpc_bid_micros": 2_000_000},
        {"id": "3004", "text": "demo athletic wear", "match_type": "PHRASE", "status": "ENABLED", "quality_score": 6, "cpc_bid_micros": 1_800_000},
    ],
    "2003": [
        {"id": "3005", "text": "running shoes", "match_type": "BROAD", "status": "ENABLED", "quality_score": 5, "cpc_bid_micros": 3_500_000},
        {"id": "3006", "text": "best running shoes 2026", "match_type": "BROAD", "status": "ENABLED", "quality_score": 4, "cpc_bid_micros": 4_000_000},
        {"id": "3007", "text": "cheap running shoes", "match_type": "BROAD", "status": "ENABLED", "quality_score": 3, "cpc_bid_micros": 2_000_000},
    ],
    "2004": [
        {"id": "3008", "text": "athletic apparel", "match_type": "BROAD", "status": "ENABLED", "quality_score": 5, "cpc_bid_micros": 2_500_000},
        {"id": "3009", "text": "workout clothes", "match_type": "BROAD", "status": "ENABLED", "quality_score": 6, "cpc_bid_micros": 2_200_000},
    ],
}

SEARCH_TERMS = [
    {"campaign_id": "1002", "ad_group_id": "2003", "search_term": "running shoes for flat feet", "impressions": 450, "clicks": 38, "cost_micros": 95_000_000, "conversions": 3, "match_type": "BROAD"},
    {"campaign_id": "1002", "ad_group_id": "2003", "search_term": "nike running shoes sale", "impressions": 1200, "clicks": 95, "cost_micros": 285_000_000, "conversions": 0, "match_type": "BROAD"},
    {"campaign_id": "1002", "ad_group_id": "2003", "search_term": "running shoes near me", "impressions": 800, "clicks": 62, "cost_micros": 186_000_000, "conversions": 0, "match_type": "BROAD"},
    {"campaign_id": "1002", "ad_group_id": "2003", "search_term": "best marathon training shoes", "impressions": 350, "clicks": 28, "cost_micros": 84_000_000, "conversions": 5, "match_type": "BROAD"},
    {"campaign_id": "1002", "ad_group_id": "2004", "search_term": "cheap gym clothes", "impressions": 600, "clicks": 40, "cost_micros": 100_000_000, "conversions": 0, "match_type": "BROAD"},
    {"campaign_id": "1002", "ad_group_id": "2004", "search_term": "lululemon dupes", "impressions": 900, "clicks": 70, "cost_micros": 175_000_000, "conversions": 0, "match_type": "BROAD"},
    {"campaign_id": "1002", "ad_group_id": "2004", "search_term": "athletic wear for women", "impressions": 500, "clicks": 42, "cost_micros": 105_000_000, "conversions": 4, "match_type": "BROAD"},
    {"campaign_id": "1001", "ad_group_id": "2001", "search_term": "demo store official", "impressions": 2000, "clicks": 400, "cost_micros": 600_000_000, "conversions": 80, "match_type": "EXACT"},
    {"campaign_id": "1001", "ad_group_id": "2001", "search_term": "demo store coupon", "impressions": 800, "clicks": 150, "cost_micros": 225_000_000, "conversions": 25, "match_type": "CLOSE_VARIANT"},
    {"campaign_id": "1001", "ad_group_id": "2002", "search_term": "demo running shoes review", "impressions": 400, "clicks": 50, "cost_micros": 100_000_000, "conversions": 8, "match_type": "EXACT"},
]


def _micros_to_dollars(micros: int) -> float:
    return micros / 1_000_000


def _generate_daily_metrics(campaign: dict, days: int = 30) -> list[dict]:
    """Generate realistic daily performance data for a campaign."""
    random.seed(int(campaign["id"]))
    base_impressions = {"SEARCH": 1500, "SHOPPING": 5000, "DISPLAY": 20000, "PERFORMANCE_MAX": 8000}
    base_imp = base_impressions.get(campaign["type"], 2000)
    base_ctr = {"SEARCH": 0.06, "SHOPPING": 0.02, "DISPLAY": 0.004, "PERFORMANCE_MAX": 0.015}
    ctr = base_ctr.get(campaign["type"], 0.03)
    base_cvr = {"SEARCH": 0.04, "SHOPPING": 0.025, "DISPLAY": 0.01, "PERFORMANCE_MAX": 0.02}
    cvr = base_cvr.get(campaign["type"], 0.02)
    avg_cpc = campaign.get("cpc_bid_micros", 2_000_000) or 2_000_000

    metrics = []
    today = datetime.now()
    for i in range(days):
        date = today - timedelta(days=days - i)
        # Add some variance and a slight upward CPA trend in recent days
        day_var = random.uniform(0.7, 1.3)
        cpa_trend = 1.0 + (i / days) * 0.15  # CPA drifts up ~15%
        impressions = int(base_imp * day_var)
        clicks = max(1, int(impressions * ctr * random.uniform(0.8, 1.2)))
        conversions = max(0, int(clicks * cvr * random.uniform(0.6, 1.4) / cpa_trend))
        cost = clicks * avg_cpc * random.uniform(0.8, 1.2)
        conv_value = conversions * random.uniform(40_000_000, 120_000_000)

        metrics.append({
            "date": date.strftime("%Y-%m-%d"),
            "impressions": impressions,
            "clicks": clicks,
            "cost": round(_micros_to_dollars(int(cost)), 2),
            "conversions": conversions,
            "conversion_value": round(_micros_to_dollars(int(conv_value)), 2),
            "ctr": round(clicks / impressions * 100, 2) if impressions else 0,
            "cpc": round(_micros_to_dollars(int(cost)) / clicks, 2) if clicks else 0,
            "cpa": round(_micros_to_dollars(int(cost)) / conversions, 2) if conversions else None,
            "roas": round(conv_value / cost, 2) if cost else None,
        })
    return metrics


def get_mock_campaigns() -> list[dict]:
    """Return campaign list with summary metrics."""
    results = []
    for c in CAMPAIGNS:
        daily = _generate_daily_metrics(c, 30)
        total_cost = sum(d["cost"] for d in daily)
        total_conv = sum(d["conversions"] for d in daily)
        total_clicks = sum(d["clicks"] for d in daily)
        total_impressions = sum(d["impressions"] for d in daily)
        total_value = sum(d["conversion_value"] for d in daily)
        results.append({
            "campaign_id": c["id"],
            "campaign_name": c["name"],
            "status": c["status"],
            "type": c["type"],
            "daily_budget": _micros_to_dollars(c["budget_amount_micros"]),
            "bidding_strategy": c["bidding_strategy"],
            "last_30d": {
                "impressions": total_impressions,
                "clicks": total_clicks,
                "cost": round(total_cost, 2),
                "conversions": total_conv,
                "conversion_value": round(total_value, 2),
                "ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions else 0,
                "avg_cpc": round(total_cost / total_clicks, 2) if total_clicks else 0,
                "cpa": round(total_cost / total_conv, 2) if total_conv else None,
                "roas": round(total_value / total_cost, 2) if total_cost else None,
            },
        })
    return results


def get_mock_ad_groups(campaign_id: str) -> list[dict]:
    """Return ad groups for a campaign."""
    groups = AD_GROUPS.get(campaign_id, [])
    return [
        {
            "ad_group_id": g["id"],
            "ad_group_name": g["name"],
            "status": g["status"],
            "cpc_bid": _micros_to_dollars(g["cpc_bid_micros"]),
        }
        for g in groups
    ]


def get_mock_keywords(campaign_id: str | None = None, ad_group_id: str | None = None) -> list[dict]:
    """Return keywords, optionally filtered."""
    results = []
    for ag_id, kws in KEYWORDS.items():
        if ad_group_id and ag_id != ad_group_id:
            continue
        # Check campaign filter
        if campaign_id:
            belongs = False
            for cid, ags in AD_GROUPS.items():
                if cid == campaign_id and any(a["id"] == ag_id for a in ags):
                    belongs = True
                    break
            if not belongs:
                continue
        for kw in kws:
            results.append({
                "keyword_id": kw["id"],
                "keyword_text": kw["text"],
                "match_type": kw["match_type"],
                "status": kw["status"],
                "quality_score": kw["quality_score"],
                "cpc_bid": _micros_to_dollars(kw["cpc_bid_micros"]),
            })
    return results


def get_mock_performance(campaign_id: str | None = None, days: int = 30) -> list[dict]:
    """Return daily performance metrics."""
    campaigns = CAMPAIGNS
    if campaign_id:
        campaigns = [c for c in CAMPAIGNS if c["id"] == campaign_id]
    if not campaigns:
        return []

    # Aggregate across campaigns per day
    from collections import defaultdict
    daily_totals: dict[str, dict] = defaultdict(lambda: {"impressions": 0, "clicks": 0, "cost": 0.0, "conversions": 0, "conversion_value": 0.0})
    for c in campaigns:
        if c["status"] == "PAUSED":
            continue
        for d in _generate_daily_metrics(c, days):
            dt = daily_totals[d["date"]]
            dt["impressions"] += d["impressions"]
            dt["clicks"] += d["clicks"]
            dt["cost"] += d["cost"]
            dt["conversions"] += d["conversions"]
            dt["conversion_value"] += d["conversion_value"]

    results = []
    for date in sorted(daily_totals.keys()):
        d = daily_totals[date]
        results.append({
            "date": date,
            "impressions": d["impressions"],
            "clicks": d["clicks"],
            "cost": round(d["cost"], 2),
            "conversions": d["conversions"],
            "conversion_value": round(d["conversion_value"], 2),
            "ctr": round(d["clicks"] / d["impressions"] * 100, 2) if d["impressions"] else 0,
            "cpc": round(d["cost"] / d["clicks"], 2) if d["clicks"] else 0,
            "cpa": round(d["cost"] / d["conversions"], 2) if d["conversions"] else None,
            "roas": round(d["conversion_value"] / d["cost"], 2) if d["cost"] else None,
        })
    return results


def get_mock_search_terms(campaign_id: str | None = None) -> list[dict]:
    """Return search term report."""
    terms = SEARCH_TERMS
    if campaign_id:
        terms = [t for t in terms if t["campaign_id"] == campaign_id]
    return [
        {
            "search_term": t["search_term"],
            "campaign_id": t["campaign_id"],
            "ad_group_id": t["ad_group_id"],
            "match_type": t["match_type"],
            "impressions": t["impressions"],
            "clicks": t["clicks"],
            "cost": round(_micros_to_dollars(t["cost_micros"]), 2),
            "conversions": t["conversions"],
            "cpa": round(_micros_to_dollars(t["cost_micros"]) / t["conversions"], 2) if t["conversions"] else None,
            "ctr": round(t["clicks"] / t["impressions"] * 100, 2) if t["impressions"] else 0,
        }
        for t in terms
    ]
