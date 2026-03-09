"""Account-level and metadata tools."""

from mcp.server.fastmcp import FastMCP

from google_ads_mcp.google_ads.client import manager_customer_id, search_rows
from google_ads_mcp.google_ads.utils import enum_name, error_response, fmt


def register(mcp: FastMCP) -> None:
    """Register account and metadata tools."""

    @mcp.tool()
    def get_accessible_accounts() -> str:
        """List all enabled accounts accessible under the configured MCC/login customer."""
        try:
            login_customer_id = manager_customer_id()
            query = """
                SELECT
                    customer_client.id,
                    customer_client.descriptive_name,
                    customer_client.currency_code,
                    customer_client.time_zone,
                    customer_client.status,
                    customer_client.manager
                FROM customer_client
                WHERE customer_client.status = 'ENABLED'
                ORDER BY customer_client.descriptive_name
            """
            accounts = []
            for row in search_rows(login_customer_id, query):
                accounts.append(
                    {
                        "customer_id": str(row.customer_client.id),
                        "name": row.customer_client.descriptive_name,
                        "currency_code": row.customer_client.currency_code,
                        "time_zone": row.customer_client.time_zone,
                        "status": enum_name(row.customer_client.status),
                        "is_manager": row.customer_client.manager,
                    }
                )
            return fmt({"login_customer_id": login_customer_id, "accessible_accounts": accounts})
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_account_info(customer_id: str) -> str:
        """Get core metadata for a single account, including name, currency, timezone, and tagging settings."""
        try:
            query = """
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
            """
            rows = search_rows(customer_id, query)
            if not rows:
                return fmt({"customer_id": customer_id, "account": None})
            row = rows[0]
            return fmt(
                {
                    "customer_id": customer_id,
                    "account": {
                        "customer_id": str(row.customer.id),
                        "name": row.customer.descriptive_name,
                        "currency_code": row.customer.currency_code,
                        "time_zone": row.customer.time_zone,
                        "auto_tagging_enabled": row.customer.auto_tagging_enabled,
                        "tracking_url_template": row.customer.tracking_url_template,
                        "has_partners_badge": row.customer.has_partners_badge,
                        "is_manager": row.customer.manager,
                    },
                }
            )
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_conversion_actions(customer_id: str) -> str:
        """List configured conversion actions, settings, and attribution models."""
        try:
            query = """
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
            """
            conversion_actions = []
            for row in search_rows(customer_id, query):
                conversion_actions.append(
                    {
                        "conversion_action_id": str(row.conversion_action.id),
                        "name": row.conversion_action.name,
                        "category": enum_name(row.conversion_action.category),
                        "type": enum_name(row.conversion_action.type_),
                        "status": enum_name(row.conversion_action.status),
                        "counting_type": enum_name(row.conversion_action.counting_type),
                        "default_value": row.conversion_action.value_settings.default_value,
                        "always_use_default_value": row.conversion_action.value_settings.always_use_default_value,
                        "attribution_model": enum_name(
                            row.conversion_action.attribution_model_settings.attribution_model
                        ),
                        "data_driven_model_status": enum_name(
                            row.conversion_action.attribution_model_settings.data_driven_model_status
                        ),
                    }
                )
            return fmt({"conversion_actions": conversion_actions})
        except Exception as exc:
            return error_response(exc)

    @mcp.tool()
    def get_campaign_labels(customer_id: str) -> str:
        """Get labels attached to campaigns and ad groups."""
        try:
            campaign_query = """
                SELECT
                    campaign.id, campaign.name,
                    label.id, label.name
                FROM campaign_label
                ORDER BY campaign.name, label.name
            """
            ad_group_query = """
                SELECT
                    campaign.id, campaign.name,
                    ad_group.id, ad_group.name,
                    label.id, label.name
                FROM ad_group_label
                ORDER BY campaign.name, ad_group.name, label.name
            """
            campaign_labels = []
            for row in search_rows(customer_id, campaign_query):
                campaign_labels.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "label_id": str(row.label.id),
                        "label_name": row.label.name,
                    }
                )
            ad_group_labels = []
            for row in search_rows(customer_id, ad_group_query):
                ad_group_labels.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "ad_group_id": str(row.ad_group.id),
                        "ad_group_name": row.ad_group.name,
                        "label_id": str(row.label.id),
                        "label_name": row.label.name,
                    }
                )
            return fmt({"campaign_labels": campaign_labels, "ad_group_labels": ad_group_labels})
        except Exception as exc:
            return error_response(exc)
