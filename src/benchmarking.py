"""
Benchmarking and trend-analysis functions: revenue-growth ranking, EBIT
margin benchmarking against the peer average, and segment/region leaders,
structured so they can feed dashboards and ad-hoc research.
"""

from __future__ import annotations

from dataclasses import dataclass

from .data_sources import FinancialRecord, MarketShareEstimate


@dataclass
class RevenueGrowth:
    company: str
    fy2024_revenue: float
    fy2025_revenue: float
    growth_pct: float
    rank: int  # 1 = fastest growing


def revenue_growth_ranking(records: list[FinancialRecord]) -> list[RevenueGrowth]:
    """Rank competitors by year-over-year revenue growth (2024 -> 2025).
    Requires exactly one 2024 and one 2025 record per company (i.e. run
    this after conflict resolution)."""
    by_company: dict[str, dict[int, float]] = {}
    for r in records:
        by_company.setdefault(r.company, {})[r.fiscal_year] = r.revenue

    growths = []
    for company, years in by_company.items():
        if 2024 not in years or 2025 not in years:
            continue
        fy24, fy25 = years[2024], years[2025]
        growth_pct = round((fy25 - fy24) / fy24 * 100, 2)
        growths.append((company, fy24, fy25, growth_pct))

    growths.sort(key=lambda x: x[3], reverse=True)
    return [
        RevenueGrowth(company=c, fy2024_revenue=fy24, fy2025_revenue=fy25,
                      growth_pct=g, rank=i + 1)
        for i, (c, fy24, fy25, g) in enumerate(growths)
    ]


@dataclass
class MarginBenchmark:
    company: str
    ebit_margin_pct: float
    vs_peer_average_pp: float  # percentage points vs peer average


def margin_benchmark(records: list[FinancialRecord], fiscal_year: int) -> list[MarginBenchmark]:
    """Benchmark each competitor's EBIT margin against the peer average
    for a given fiscal year, excluding any competitor with a missing
    (NaN) margin from both the individual result and the peer average --
    an undisclosed margin must never silently drag the average down."""
    import math

    year_records = [r for r in records if r.fiscal_year == fiscal_year
                     and not (isinstance(r.ebit_margin_pct, float) and math.isnan(r.ebit_margin_pct))]
    if not year_records:
        return []

    peer_avg = sum(r.ebit_margin_pct for r in year_records) / len(year_records)
    return [
        MarginBenchmark(
            company=r.company, ebit_margin_pct=r.ebit_margin_pct,
            vs_peer_average_pp=round(r.ebit_margin_pct - peer_avg, 2),
        )
        for r in year_records
    ]


@dataclass
class SegmentLeader:
    segment: str
    region: str
    leading_company: str
    share_pct: float


def segment_region_leaders(estimates: list[MarketShareEstimate]) -> list[SegmentLeader]:
    """For each segment/region combination, identify the competitor with
    the highest estimated market share -- the 'who is leading where'
    question a market-intelligence dashboard needs to answer at a
    glance."""
    by_key: dict[tuple[str, str], list[MarketShareEstimate]] = {}
    for e in estimates:
        by_key.setdefault((e.segment, e.region), []).append(e)

    leaders = []
    for (segment, region), group in by_key.items():
        top = max(group, key=lambda e: e.share_pct)
        leaders.append(SegmentLeader(
            segment=segment, region=region,
            leading_company=top.company, share_pct=top.share_pct,
        ))
    return leaders
