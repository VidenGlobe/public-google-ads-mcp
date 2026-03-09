"""Formatting, validation, and GAQL utility helpers."""

from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


@dataclass(frozen=True)
class ResolvedDateRange:
    """Resolved GAQL date clause plus a response-friendly representation."""

    clause: str
    date_from: str | None = None
    date_to: str | None = None
    preset: str | None = None

    def as_dict(self) -> dict[str, Any]:
        if self.preset:
            return {"preset": self.preset}
        return {"date_from": self.date_from, "date_to": self.date_to}


def fmt(data: Any) -> str:
    """Format data as readable JSON."""
    return json.dumps(data, indent=2, default=str)


def error_response(exc: Exception) -> str:
    """Format an error consistently for MCP tool callers."""
    return fmt({"error": str(exc)})


def normalize_customer_id(customer_id: str) -> str:
    """Normalize a customer ID by stripping separators and validating digits."""
    normalized = "".join(ch for ch in str(customer_id).strip() if ch.isdigit())
    if not normalized:
        raise ValueError("customer_id must contain digits only.")
    return normalized


def normalize_numeric_id(name: str, value: str | None) -> str | None:
    """Validate numeric filter IDs used in GAQL WHERE clauses."""
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized.isdigit():
        raise ValueError(f"{name} must contain digits only.")
    return normalized


def normalize_positive_int(name: str, value: int | None) -> int | None:
    """Validate positive integer parameters."""
    if value is None:
        return None
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0.")
    return value


def parse_iso_date(value: str, name: str) -> date:
    """Parse an ISO date or raise a validation error."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be in YYYY-MM-DD format.") from exc


def build_date_clause(
    date_range_days: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> ResolvedDateRange:
    """Build a GAQL date filter clause from explicit or relative inputs."""
    if (date_from and not date_to) or (date_to and not date_from):
        raise ValueError("date_from and date_to must be provided together.")

    if date_from and date_to:
        start = parse_iso_date(date_from, "date_from")
        end = parse_iso_date(date_to, "date_to")
        if start > end:
            raise ValueError("date_from must be on or before date_to.")
        return ResolvedDateRange(
            clause=f"segments.date BETWEEN '{start.isoformat()}' AND '{end.isoformat()}'",
            date_from=start.isoformat(),
            date_to=end.isoformat(),
        )

    normalized_days = normalize_positive_int("date_range_days", date_range_days)
    if normalized_days:
        yesterday = date.today() - timedelta(days=1)
        start = yesterday - timedelta(days=normalized_days - 1)
        return ResolvedDateRange(
            clause=f"segments.date BETWEEN '{start.isoformat()}' AND '{yesterday.isoformat()}'",
            date_from=start.isoformat(),
            date_to=yesterday.isoformat(),
        )

    return ResolvedDateRange(clause="segments.date DURING LAST_30_DAYS", preset="LAST_30_DAYS")


def build_where(*clauses: str) -> str:
    """Join non-empty GAQL WHERE clauses with AND."""
    active_clauses = [clause for clause in clauses if clause]
    if not active_clauses:
        raise ValueError("At least one WHERE clause is required.")
    return " AND ".join(active_clauses)


def id_filter(field: str, parameter_name: str, value: str | None) -> str:
    """Return a GAQL equality filter for a numeric ID parameter."""
    normalized = normalize_numeric_id(parameter_name, value)
    return f"{field} = {normalized}" if normalized else ""


def cost_from_micros(cost_micros: float | int) -> float:
    """Convert micros to account currency units."""
    return round(float(cost_micros) / 1_000_000, 2)


def safe_divide(numerator: float | int, denominator: float | int, digits: int = 2) -> float | None:
    """Safely divide numbers and round the result."""
    if not denominator:
        return None
    return round(float(numerator) / float(denominator), digits)


def safe_percentage(numerator: float | int, denominator: float | int) -> float:
    """Safely calculate a percentage."""
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator) * 100, 2)


def enum_name(value: Any) -> str:
    """Return the enum name when available, otherwise stringify the value."""
    return getattr(value, "name", str(value))


def message_to_string(value: Any) -> Any:
    """Convert proto-ish values into JSON-serializable structures."""
    if value is None:
        return None
    if hasattr(value, "paths"):
        return list(value.paths)
    if isinstance(value, (list, tuple, set)):
        return [message_to_string(item) for item in value]
    return str(value)


def asset_payload(row: Any, scope: str) -> dict[str, Any]:
    """Normalize asset rows from campaign_asset/customer_asset queries."""
    payload: dict[str, Any] = {
        "scope": scope,
        "asset_id": str(row.asset.id),
        "asset_name": row.asset.name,
        "asset_type": enum_name(row.asset.type_),
        "field_type": enum_name(
            row.campaign_asset.field_type if scope == "campaign" else row.customer_asset.field_type
        ),
        "status": enum_name(row.campaign_asset.status if scope == "campaign" else row.customer_asset.status),
        "link_text": getattr(row.asset.sitelink_asset, "link_text", ""),
        "description1": getattr(row.asset.sitelink_asset, "description1", ""),
        "description2": getattr(row.asset.sitelink_asset, "description2", ""),
        "callout_text": getattr(row.asset.callout_asset, "callout_text", ""),
        "structured_snippet_header": getattr(row.asset.structured_snippet_asset, "header", ""),
        "structured_snippet_values": list(getattr(row.asset.structured_snippet_asset, "values", [])),
        "impressions": row.metrics.impressions,
        "clicks": row.metrics.clicks,
    }
    if scope == "campaign":
        payload["campaign_id"] = str(row.campaign.id)
        payload["campaign_name"] = row.campaign.name
        payload["cost"] = cost_from_micros(row.metrics.cost_micros)
        payload["ctr"] = safe_percentage(row.metrics.clicks, row.metrics.impressions)
    return payload


def today_month_context() -> tuple[date, date, int]:
    """Return current month start, yesterday, and days in month."""
    today = date.today()
    month_start = today.replace(day=1)
    yesterday = today - timedelta(days=1)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    return month_start, yesterday, days_in_month
