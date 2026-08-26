from src.data_sources import FinancialRecord, MarketShareEstimate
from src.benchmarking import margin_benchmark, revenue_growth_ranking, segment_region_leaders


def fr(company, year, revenue, margin=10.0, source="Annual Report"):
    return FinancialRecord(
        company=company, fiscal_year=year, reported_currency="EUR",
        revenue=revenue, ebit_margin_pct=margin, source=source, as_of_date="2025-01-01",
    )


def test_revenue_growth_ranking_computes_correct_percentage():
    records = [fr("Acme", 2024, 100.0), fr("Acme", 2025, 120.0)]
    result = revenue_growth_ranking(records)
    assert len(result) == 1
    assert result[0].growth_pct == 20.0
    assert result[0].rank == 1


def test_revenue_growth_ranking_orders_fastest_first():
    records = [
        fr("Slow Co", 2024, 100.0), fr("Slow Co", 2025, 105.0),
        fr("Fast Co", 2024, 100.0), fr("Fast Co", 2025, 150.0),
    ]
    result = revenue_growth_ranking(records)
    assert result[0].company == "Fast Co"
    assert result[0].rank == 1
    assert result[1].company == "Slow Co"
    assert result[1].rank == 2


def test_revenue_growth_ranking_skips_companies_missing_a_year():
    records = [fr("Acme", 2024, 100.0)]  # no 2025 record
    result = revenue_growth_ranking(records)
    assert result == []


def test_margin_benchmark_computes_deviation_from_peer_average():
    records = [
        fr("Acme", 2025, 100.0, margin=10.0),
        fr("Beta", 2025, 100.0, margin=20.0),
    ]
    result = margin_benchmark(records, fiscal_year=2025)
    by_company = {m.company: m for m in result}
    # peer average = 15.0
    assert by_company["Acme"].vs_peer_average_pp == -5.0
    assert by_company["Beta"].vs_peer_average_pp == 5.0


def test_margin_benchmark_excludes_missing_margin_from_average():
    records = [
        fr("Acme", 2025, 100.0, margin=10.0),
        fr("Beta", 2025, 100.0, margin=float("nan")),
    ]
    result = margin_benchmark(records, fiscal_year=2025)
    # Only Acme should appear, and its deviation from the (Acme-only) average is 0
    assert len(result) == 1
    assert result[0].company == "Acme"
    assert result[0].vs_peer_average_pp == 0.0


def test_margin_benchmark_filters_by_fiscal_year():
    records = [fr("Acme", 2024, 100.0, margin=5.0), fr("Acme", 2025, 100.0, margin=10.0)]
    result = margin_benchmark(records, fiscal_year=2025)
    assert len(result) == 1
    assert result[0].ebit_margin_pct == 10.0


def test_margin_benchmark_returns_empty_list_for_no_data():
    assert margin_benchmark([], fiscal_year=2025) == []


def test_segment_region_leaders_picks_highest_share():
    estimates = [
        MarketShareEstimate(company="Acme", segment="Motors", region="EMEA", fiscal_year=2025, share_pct=30.0, source="x"),
        MarketShareEstimate(company="Beta", segment="Motors", region="EMEA", fiscal_year=2025, share_pct=15.0, source="x"),
    ]
    leaders = segment_region_leaders(estimates)
    assert len(leaders) == 1
    assert leaders[0].leading_company == "Acme"
    assert leaders[0].share_pct == 30.0


def test_segment_region_leaders_covers_all_distinct_pairs():
    estimates = [
        MarketShareEstimate(company="Acme", segment="Motors", region="EMEA", fiscal_year=2025, share_pct=30.0, source="x"),
        MarketShareEstimate(company="Acme", segment="Drives", region="APAC", fiscal_year=2025, share_pct=25.0, source="x"),
    ]
    leaders = segment_region_leaders(estimates)
    pairs = {(l.segment, l.region) for l in leaders}
    assert pairs == {("Motors", "EMEA"), ("Drives", "APAC")}
