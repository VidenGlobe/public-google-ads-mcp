# MCP Tools Design — Google Ads Server

## Cross-Cutting: Date Range & Account Selection

Every tool that queries metrics accepts these parameters:

```
customer_id: str          # REQUIRED — Google Ads customer ID (e.g. "1234567890", no dashes)
date_range_days: int      # Option 1: window — N days back from yesterday (e.g. 30 = last 30 days)
date_from: str            # Option 2: manual start date "YYYY-MM-DD"
date_to: str              # Option 2: manual end date "YYYY-MM-DD"
```

**Resolution logic** (helper `_build_date_clause`):
1. If `date_from` AND `date_to` → `segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'`
2. If `date_range_days` → calculate `(yesterday - N+1)` to `yesterday`, use BETWEEN
3. If nothing → default `DURING LAST_30_DAYS`

---

## Tier 0: Account Basics

### 1. `get_accessible_accounts`
List all accounts accessible under the configured MCC (login_customer_id).
Returns account ID, descriptive name, currency, timezone, status, whether it's a manager account.

**Skills served**: all (account discovery/selection)
**No date range needed.**

```
Parameters: (none — uses login_customer_id from env)
```

GAQL:
```sql
SELECT
    customer_client.id,
    customer_client.descriptive_name,
    customer_client.currency_code,
    customer_client.time_zone,
    customer_client.status,
    customer_client.manager
FROM customer_client
WHERE customer_client.status = 'ENABLED'
```

---

### 2. `get_account_info`
Get detailed info for a single account: name, currency, timezone, auto-tagging, tracking URL template, conversion tracking status.

**Skills served**: weekly summary (#30), pacing (#27), audit (#37), all reporting skills
**No date range needed.**

```
Parameters:
  customer_id: str
```

GAQL:
```sql
SELECT
    customer.id,
    customer.descriptive_name,
    customer.currency_code,
    customer.time_zone,
    customer.auto_tagging_enabled,
    customer.tracking_url_template,
    customer.has_partners_badge,
    customer.manager
FROM customer
LIMIT 1
```

---

## Tier 1: Existing Tools (add date range)

All 10 existing tools get the `date_range_days` / `date_from` + `date_to` parameters.
The hardcoded `DURING LAST_30_DAYS` is replaced with `_build_date_clause()` call.

### 3. `get_campaigns` (UPDATED)
### 4. `get_ad_groups` (UPDATED)
### 5. `get_keywords` (UPDATED)
### 6. `get_performance_report` (UPDATED — replaces `days` param with new date range)
### 7. `get_search_terms` (UPDATED)
### 8. `get_geo_performance` (UPDATED)
### 9. `get_device_performance` (UPDATED)
### 10. `get_ad_performance` (UPDATED)
### 11. `get_age_gender_performance` (UPDATED)
### 12. `get_audience_performance` (UPDATED)

---

## Tier 2: New Tools

### 13. `get_hourly_performance`
Performance by hour of day and day of week. Critical for ad scheduling optimization.

**Skills served**: day/hour breakdown (#12), anomaly detection (#6), pacing (#27)

```
Parameters:
  customer_id: str
  campaign_id: str | None
  date_range_days / date_from / date_to
```

GAQL:
```sql
SELECT
    segments.day_of_week,
    segments.hour,
    campaign.id, campaign.name,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.conversions, metrics.conversions_value
FROM campaign
WHERE {date_clause}
  {campaign_filter}
ORDER BY segments.day_of_week, segments.hour
```

---

### 14. `get_keyword_quality_details`
Keywords with full Quality Score component breakdown (expected CTR, ad relevance, landing page experience).

**Skills served**: QS breakdown (#14), audit (#37), CPA diagnostics (#1)

```
Parameters:
  customer_id: str
  campaign_id: str | None
  ad_group_id: str | None
  min_impressions: int = 0       # filter out low-volume keywords
```

GAQL:
```sql
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
WHERE ad_group_criterion.status != 'REMOVED'
  AND metrics.impressions >= {min_impressions}
  {campaign_filter}
  {ad_group_filter}
  AND {date_clause}
ORDER BY ad_group_criterion.quality_info.quality_score ASC
```

---

### 15. `get_ad_extensions`
All ad extensions/assets with type, status, performance. Covers sitelinks, callouts, structured snippets, call, image, price extensions.

**Skills served**: ad extension audit (#21), audit (#37), account structure (#17)

```
Parameters:
  customer_id: str
  campaign_id: str | None
  date_range_days / date_from / date_to
```

GAQL:
```sql
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
    campaign_asset.campaign,
    campaign_asset.field_type,
    campaign_asset.status,
    metrics.impressions, metrics.clicks, metrics.cost_micros
FROM campaign_asset
WHERE campaign_asset.status != 'REMOVED'
  {campaign_filter}
  AND {date_clause}
ORDER BY asset.type, metrics.impressions DESC
```

Plus account-level assets:
```sql
SELECT
    asset.id, asset.name, asset.type,
    customer_asset.field_type, customer_asset.status,
    metrics.impressions, metrics.clicks
FROM customer_asset
WHERE customer_asset.status != 'REMOVED'
  AND {date_clause}
```

---

### 16. `get_bid_strategies`
Campaign-level bid strategy info: type, target CPA, target ROAS, max CPC limit, enhanced CPC flag.

**Skills served**: bid strategy recommendations (#11), account structure (#17), audit (#37)

```
Parameters:
  customer_id: str
  campaign_id: str | None
  date_range_days / date_from / date_to
```

GAQL:
```sql
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
WHERE campaign.status != 'REMOVED'
  {campaign_filter}
  AND {date_clause}
ORDER BY metrics.cost_micros DESC
```

---

### 17. `get_conversion_actions`
All configured conversion actions: name, category, type, status, counting, value settings.

**Skills served**: audit (#37), CPA diagnostics (#1), ROAS forecasting (#19), attribution (#26)

```
Parameters:
  customer_id: str
```

**No date range needed.**

GAQL:
```sql
SELECT
    conversion_action.id,
    conversion_action.name,
    conversion_action.category,
    conversion_action.type,
    conversion_action.status,
    conversion_action.counting_type,
    conversion_action.value_settings.default_value,
    conversion_action.value_settings.always_use_default_value,
    conversion_action.attribution_model_settings.attribution_model,
    conversion_action.attribution_model_settings.data_driven_model_status
FROM conversion_action
WHERE conversion_action.status != 'HIDDEN'
ORDER BY conversion_action.name
```

---

### 18. `get_budget_pacing`
Month-to-date spend vs daily budget, with projected end-of-month spend and remaining daily budget needed.

**Skills served**: pacing monitor (#27), weekly summary (#30), budget scenario planner (#3)

```
Parameters:
  customer_id: str
  campaign_id: str | None
```

**Date range is auto-calculated** (1st of current month → yesterday for MTD, plus last 7 days for daily rate).

GAQL (MTD spend):
```sql
SELECT
    campaign.id, campaign.name, campaign.status,
    campaign_budget.amount_micros,
    metrics.cost_micros, metrics.conversions,
    metrics.impressions, metrics.clicks
FROM campaign
WHERE campaign.status = 'ENABLED'
  AND segments.date BETWEEN '{month_start}' AND '{yesterday}'
  {campaign_filter}
ORDER BY metrics.cost_micros DESC
```

Returns computed fields: `mtd_spend`, `daily_budget`, `days_elapsed`, `days_remaining`, `projected_eom_spend`, `needed_daily_spend_to_hit_target`, `pacing_status` (over/under/on_track).

---

### 19. `get_landing_page_performance`
Landing page URLs with metrics. Identifies high/low performing pages.

**Skills served**: landing page audit (#10, #39), QS breakdown (#14), CPA diagnostics (#1)

```
Parameters:
  customer_id: str
  campaign_id: str | None
  date_range_days / date_from / date_to
```

GAQL:
```sql
SELECT
    landing_page_view.unexpanded_final_url,
    campaign.id, campaign.name,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.conversions, metrics.conversions_value,
    metrics.speed_score,
    metrics.mobile_friendly_clicks_percentage
FROM landing_page_view
WHERE {date_clause}
  {campaign_filter}
ORDER BY metrics.cost_micros DESC
LIMIT 100
```

---

### 20. `get_change_history`
Recent account changes (bid changes, budget changes, status changes, keyword additions/removals).

**Skills served**: anomaly detection (#6), audit (#37), CPA diagnostics (#1)

```
Parameters:
  customer_id: str
  days_back: int = 7
```

Uses `ChangeEvent` resource:
```sql
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
WHERE change_event.change_date_time >= '{N_days_ago}'
ORDER BY change_event.change_date_time DESC
LIMIT 200
```

---

### 21. `get_campaign_labels`
Labels attached to campaigns/ad groups. Useful for organizing audit output and grouping.

**Skills served**: account structure (#17), weekly summary (#30), naming conventions (#23)

```
Parameters:
  customer_id: str
```

GAQL:
```sql
SELECT
    campaign.id, campaign.name,
    label.id, label.name
FROM campaign_label
```

---

### 22. `get_search_term_keyword_mapping`
Search terms mapped to the keyword that triggered them. Critical for cannibalization analysis.

**Skills served**: keyword cannibalization (#20), search term mining (#7), wasted spend (#2)

```
Parameters:
  customer_id: str
  campaign_id: str | None
  date_range_days / date_from / date_to
```

GAQL:
```sql
SELECT
    search_term_view.search_term,
    ad_group_criterion.keyword.text,
    ad_group_criterion.keyword.match_type,
    campaign.id, campaign.name,
    ad_group.id, ad_group.name,
    metrics.impressions, metrics.clicks, metrics.cost_micros,
    metrics.conversions
FROM search_term_view
WHERE {date_clause}
  {campaign_filter}
ORDER BY metrics.cost_micros DESC
LIMIT 500
```

---

### 23. `get_negative_keywords`
Negative keywords at campaign and ad group level.

**Skills served**: audit (#37), search term mining (#7), wasted spend (#2), keyword cannibalization (#20)

```
Parameters:
  customer_id: str
  campaign_id: str | None
```

GAQL (campaign-level negatives):
```sql
SELECT
    campaign_criterion.keyword.text,
    campaign_criterion.keyword.match_type,
    campaign_criterion.negative,
    campaign.id, campaign.name
FROM campaign_criterion
WHERE campaign_criterion.type = 'KEYWORD'
  AND campaign_criterion.negative = TRUE
  {campaign_filter}
```

GAQL (ad-group-level negatives):
```sql
SELECT
    ad_group_criterion.keyword.text,
    ad_group_criterion.keyword.match_type,
    ad_group_criterion.negative,
    ad_group.id, ad_group.name,
    campaign.id, campaign.name
FROM ad_group_criterion
WHERE ad_group_criterion.type = 'KEYWORD'
  AND ad_group_criterion.negative = TRUE
  {campaign_filter}
```

---

### 24. `get_impression_share_data`
Search impression share, lost IS (budget), lost IS (rank) at campaign level.

**Skills served**: bid strategy (#11), competitive analysis (#33), audit (#37), anomaly detection (#6)

```
Parameters:
  customer_id: str
  campaign_id: str | None
  date_range_days / date_from / date_to
```

GAQL:
```sql
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
WHERE campaign.advertising_channel_type = 'SEARCH'
  AND {date_clause}
  {campaign_filter}
ORDER BY metrics.cost_micros DESC
```

---

## Summary: All 24 Tools

| # | Tool | Date Range | New/Updated | Primary Skills Served |
|---|------|-----------|-------------|----------------------|
| 1 | `get_accessible_accounts` | No | NEW | All (account discovery) |
| 2 | `get_account_info` | No | NEW | All (context) |
| 3 | `get_campaigns` | Yes | UPDATED | Audit, summary, pacing, structure |
| 4 | `get_ad_groups` | Yes | UPDATED | Audit, structure, QS |
| 5 | `get_keywords` | Yes | UPDATED | QS, cannibalization, audit |
| 6 | `get_performance_report` | Yes | UPDATED | CPA diagnostics, anomaly, trends |
| 7 | `get_search_terms` | Yes | UPDATED | Wasted spend, search term mining |
| 8 | `get_geo_performance` | Yes | UPDATED | Geo analysis (#24) |
| 9 | `get_device_performance` | Yes | UPDATED | Device split (#25) |
| 10 | `get_ad_performance` | Yes | UPDATED | Creative analysis, ad copy |
| 11 | `get_age_gender_performance` | Yes | UPDATED | Demographics |
| 12 | `get_audience_performance` | Yes | UPDATED | Audience analysis |
| 13 | `get_hourly_performance` | Yes | NEW | Day/hour breakdown (#12) |
| 14 | `get_keyword_quality_details` | Yes | NEW | QS breakdown (#14), audit |
| 15 | `get_ad_extensions` | Yes | NEW | Extension audit (#21) |
| 16 | `get_bid_strategies` | Yes | NEW | Bid strategy (#11), audit |
| 17 | `get_conversion_actions` | No | NEW | CPA diag, ROAS, attribution |
| 18 | `get_budget_pacing` | Auto | NEW | Pacing (#27), budget planner (#3) |
| 19 | `get_landing_page_performance` | Yes | NEW | Landing page audit (#10, #39) |
| 20 | `get_change_history` | Custom | NEW | Anomaly detection (#6), audit |
| 21 | `get_campaign_labels` | No | NEW | Structure (#17), naming (#23) |
| 22 | `get_search_term_keyword_mapping` | Yes | NEW | Cannibalization (#20), mining (#7) |
| 23 | `get_negative_keywords` | No | NEW | Audit, wasted spend (#2) |
| 24 | `get_impression_share_data` | Yes | NEW | Bid strategy (#11), competitive |

---

## Helper: `_build_date_clause`

```python
from datetime import date, timedelta

def _build_date_clause(
    date_range_days: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """Build GAQL date filter clause.

    Option 1 (window): date_range_days=30 → last 30 days ending yesterday
    Option 2 (manual): date_from + date_to → explicit BETWEEN
    Default: DURING LAST_30_DAYS
    """
    if date_from and date_to:
        return f"segments.date BETWEEN '{date_from}' AND '{date_to}'"
    if date_range_days:
        yesterday = date.today() - timedelta(days=1)
        start = yesterday - timedelta(days=date_range_days - 1)
        return f"segments.date BETWEEN '{start}' AND '{yesterday}'"
    return "segments.date DURING LAST_30_DAYS"
```

---

## Skills → Tools Coverage Matrix

| Skill | Tools Used |
|-------|-----------|
| #1 CPA Diagnostics | `get_campaigns`, `get_performance_report`, `get_device_performance`, `get_hourly_performance` |
| #2 Wasted Spend | `get_search_terms`, `get_negative_keywords`, `get_keywords` |
| #3 Budget Planner | `get_campaigns`, `get_budget_pacing`, `get_performance_report` |
| #6 Anomaly Detection | `get_performance_report`, `get_hourly_performance`, `get_change_history`, `get_impression_share_data` |
| #7 Search Term Mining | `get_search_terms`, `get_search_term_keyword_mapping`, `get_keywords` |
| #11 Bid Strategy | `get_bid_strategies`, `get_campaigns`, `get_impression_share_data` |
| #12 Day/Hour Breakdown | `get_hourly_performance` |
| #14 Quality Score | `get_keyword_quality_details`, `get_ad_performance`, `get_landing_page_performance` |
| #17 Account Structure | `get_campaigns`, `get_ad_groups`, `get_keywords`, `get_campaign_labels`, `get_bid_strategies` |
| #19 ROAS Forecasting | `get_performance_report`, `get_campaigns`, `get_conversion_actions` |
| #20 Keyword Cannibalization | `get_search_term_keyword_mapping`, `get_keywords`, `get_negative_keywords` |
| #21 Extension Audit | `get_ad_extensions`, `get_campaigns` |
| #24 Geo Analysis | `get_geo_performance` |
| #25 Device Split | `get_device_performance` |
| #26 Attribution | `get_conversion_actions`, `get_campaigns`, `get_performance_report` |
| #27 Pacing | `get_budget_pacing`, `get_campaigns`, `get_account_info` |
| #30 Weekly Summary | `get_account_info`, `get_campaigns`, `get_performance_report`, `get_hourly_performance` |
| #37 Google Ads Audit | ALL tools (comprehensive audit) |
