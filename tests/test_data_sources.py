import math

from src.data_sources import (
    COMPETITORS,
    generate_financial_records,
    generate_market_share_estimates,
    generate_product_announcements,
)


def test_generate_financial_records_covers_all_competitors_both_years():
    records = generate_financial_records()
    companies_years = {(r.company, r.fiscal_year) for r in records if r.source == "Annual Report"}
    for company in COMPETITORS:
        assert (company, 2024) in companies_years
        assert (company, 2025) in companies_years


def test_generate_financial_records_includes_injected_conflict():
    records = generate_financial_records()
    nordmotor_2025 = [r for r in records if r.company == "Nordmotor AG" and r.fiscal_year == 2025]
    assert len(nordmotor_2025) == 2
    sources = {r.source for r in nordmotor_2025}
    assert sources == {"Annual Report", "Analyst Estimate"}


def test_generate_financial_records_includes_injected_missing_value():
    records = generate_financial_records()
    vindex_press = [r for r in records if r.company == "Vindex Industrial" and r.source == "Press Release"]
    assert len(vindex_press) == 1
    assert math.isnan(vindex_press[0].ebit_margin_pct)


def test_generate_financial_records_reproducible_with_same_seed():
    a = generate_financial_records(seed=123)
    b = generate_financial_records(seed=123)
    assert [r.revenue for r in a] == [r.revenue for r in b]


def test_generate_financial_records_has_mixed_currencies():
    records = generate_financial_records()
    currencies = {r.reported_currency for r in records}
    assert currencies == {"EUR", "USD"}


def test_generate_product_announcements_all_reference_known_companies():
    announcements = generate_product_announcements()
    assert len(announcements) > 0
    for a in announcements:
        assert a.company in COMPETITORS


def test_generate_market_share_estimates_covers_all_segment_region_pairs():
    from src.data_sources import REGIONS, SEGMENTS

    estimates = generate_market_share_estimates()
    pairs = {(e.segment, e.region) for e in estimates}
    assert pairs == {(s, r) for s in SEGMENTS for r in REGIONS}


def test_generate_market_share_estimates_shares_are_valid_percentages():
    estimates = generate_market_share_estimates()
    for e in estimates:
        assert 0 < e.share_pct < 100
