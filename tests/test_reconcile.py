import math

from src.data_sources import FinancialRecord
from src.reconcile import (
    find_conflicting_reports,
    find_missing_fields,
    normalize_currency,
    resolve_conflicts_preferring_source,
)


def make_record(company="Acme", year=2025, currency="EUR", revenue=100.0,
                 margin=10.0, source="Annual Report", as_of="2025-01-01"):
    return FinancialRecord(
        company=company, fiscal_year=year, reported_currency=currency,
        revenue=revenue, ebit_margin_pct=margin, source=source, as_of_date=as_of,
    )


def test_normalize_currency_converts_usd_to_eur():
    records = [make_record(currency="USD", revenue=100.0)]
    normalized = normalize_currency(records)
    assert normalized[0].reported_currency == "EUR"
    assert normalized[0].revenue == 92.0  # 100 * 0.92


def test_normalize_currency_leaves_eur_unchanged():
    records = [make_record(currency="EUR", revenue=100.0)]
    normalized = normalize_currency(records)
    assert normalized[0].revenue == 100.0


def test_find_conflicting_reports_flags_material_spread():
    records = [
        make_record(company="Acme", year=2025, revenue=100.0, source="Annual Report"),
        make_record(company="Acme", year=2025, revenue=110.0, source="Analyst Estimate"),
    ]
    conflicts = find_conflicting_reports(records)
    assert len(conflicts) == 1
    assert conflicts[0].company == "Acme"
    assert conflicts[0].spread_pct == 10.0


def test_find_conflicting_reports_ignores_small_spread():
    records = [
        make_record(company="Acme", year=2025, revenue=100.0, source="Annual Report"),
        make_record(company="Acme", year=2025, revenue=101.0, source="Analyst Estimate"),
    ]
    conflicts = find_conflicting_reports(records)
    assert conflicts == []


def test_find_conflicting_reports_ignores_single_source_company():
    records = [make_record(company="Acme", year=2025, revenue=100.0)]
    assert find_conflicting_reports(records) == []


def test_find_missing_fields_detects_nan_margin():
    records = [make_record(margin=float("nan"))]
    missing = find_missing_fields(records)
    assert len(missing) == 1
    assert missing[0].field == "ebit_margin_pct"


def test_find_missing_fields_no_false_positive_on_real_value():
    records = [make_record(margin=8.5)]
    assert find_missing_fields(records) == []


def test_resolve_conflicts_prefers_annual_report():
    records = [
        make_record(company="Acme", year=2025, revenue=100.0, source="Annual Report"),
        make_record(company="Acme", year=2025, revenue=110.0, source="Analyst Estimate"),
    ]
    resolved = resolve_conflicts_preferring_source(records)
    assert len(resolved) == 1
    assert resolved[0].source == "Annual Report"
    assert resolved[0].revenue == 100.0


def test_resolve_conflicts_falls_back_when_no_preferred_source_present():
    records = [
        make_record(company="Acme", year=2025, revenue=100.0, source="Press Release"),
        make_record(company="Acme", year=2025, revenue=110.0, source="Analyst Estimate"),
    ]
    resolved = resolve_conflicts_preferring_source(records)
    assert len(resolved) == 1
    assert resolved[0].source in {"Press Release", "Analyst Estimate"}


def test_resolve_conflicts_passes_through_unique_records_unchanged():
    records = [make_record(company="Acme", year=2025, revenue=100.0)]
    resolved = resolve_conflicts_preferring_source(records)
    assert len(resolved) == 1
    assert resolved[0].revenue == 100.0
