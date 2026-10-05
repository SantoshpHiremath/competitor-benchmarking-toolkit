"""
Synthetic multi-source competitor/market data generator.

Models the shape of real market & competitive intelligence work: pulling
structured facts about competitors from several different sources that
don't agree perfectly with each other (different reporting currencies,
different as-of dates, some missing fields) — which is exactly the kind
of messiness a real competitive-intelligence analyst has to clean up
before anything can go into a dashboard or a slide.

All company names, financials, and product data below are entirely
fictional. This is not real market research and does not describe any
real company.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


COMPETITORS = ["Nordmotor AG", "Ferrotech Drives", "Vindex Industrial", "Halberg Motion"]
SEGMENTS = ["Low-Voltage Motors", "Large Drive Systems", "Digital Services"]
REGIONS = ["EMEA", "APAC", "Americas"]


@dataclass
class FinancialRecord:
    company: str
    fiscal_year: int
    reported_currency: str  # "EUR" or "USD" -- deliberately inconsistent across sources
    revenue: float
    ebit_margin_pct: float
    source: str
    as_of_date: str


@dataclass
class ProductAnnouncement:
    company: str
    segment: str
    region: str
    announcement_date: str
    headline: str
    source: str


@dataclass
class MarketShareEstimate:
    company: str
    segment: str
    region: str
    fiscal_year: int
    share_pct: float
    source: str


def generate_financial_records(seed: int = 42) -> list[FinancialRecord]:
    """Generate financial records for all competitors across two fiscal
    years, deliberately mixing EUR/USD reporting and injecting one
    missing-field row and one duplicate-with-conflicting-value row, the
    same class of real-world messiness a multi-source rollup has to
    catch."""
    rng = random.Random(seed)
    records: list[FinancialRecord] = []
    base_revenue = {
        "Nordmotor AG": 1850.0,
        "Ferrotech Drives": 940.0,
        "Vindex Industrial": 1220.0,
        "Halberg Motion": 610.0,
    }
    for year in (2024, 2025):
        for company in COMPETITORS:
            growth = rng.uniform(0.02, 0.09)
            revenue = round(base_revenue[company] * (1 + growth) ** (year - 2024), 1)
            currency = "USD" if company == "Halberg Motion" else "EUR"
            records.append(FinancialRecord(
                company=company,
                fiscal_year=year,
                reported_currency=currency,
                revenue=revenue,
                ebit_margin_pct=round(rng.uniform(6.0, 14.0), 1),
                source="Annual Report",
                as_of_date=f"{year}-03-31",
            ))

    # Deliberately injected: a second source reporting a conflicting
    # figure for the same company/year (real MCI work has to reconcile
    # this, not silently pick one).
    records.append(FinancialRecord(
        company="Nordmotor AG", fiscal_year=2025, reported_currency="EUR",
        revenue=2050.0, ebit_margin_pct=11.2, source="Analyst Estimate",
        as_of_date="2025-11-15",
    ))

    # Deliberately injected: a record with a missing EBIT margin (data
    # not disclosed by that competitor for that year -- a real,
    # common gap).
    records.append(FinancialRecord(
        company="Vindex Industrial", fiscal_year=2025, reported_currency="EUR",
        revenue=1310.5, ebit_margin_pct=float("nan"), source="Press Release",
        as_of_date="2025-09-01",
    ))

    return records


def generate_product_announcements(seed: int = 7) -> list[ProductAnnouncement]:
    rng = random.Random(seed)
    headlines = [
        "Launches next-gen IE5 synchronous reluctance motor line",
        "Announces predictive-maintenance add-on for drive systems",
        "Opens new large-drive assembly line",
        "Unveils digital twin platform for motor fleets",
        "Expands service network into new region",
        "Partners with automation vendor on edge AI retrofits",
    ]
    announcements = []
    dates = ["2025-02-14", "2025-04-02", "2025-06-20", "2025-08-11", "2025-09-30", "2025-11-05"]
    for i, (headline, date) in enumerate(zip(headlines, dates)):
        company = COMPETITORS[i % len(COMPETITORS)]
        announcements.append(ProductAnnouncement(
            company=company,
            segment=rng.choice(SEGMENTS),
            region=rng.choice(REGIONS),
            announcement_date=date,
            headline=headline,
            source="Company Press Release" if i % 2 == 0 else "Trade Publication",
        ))
    return announcements


def generate_market_share_estimates(seed: int = 99) -> list[MarketShareEstimate]:
    rng = random.Random(seed)
    estimates = []
    for segment in SEGMENTS:
        for region in REGIONS:
            # Shares within a segment/region should roughly sum near 100%
            # across the 4 competitors plus an implicit "Other" -- not
            # forced exact, since real market-share estimates from
            # different analyst sources never sum to a clean 100 either.
            raw = [rng.uniform(8, 30) for _ in COMPETITORS]
            for company, share in zip(COMPETITORS, raw):
                estimates.append(MarketShareEstimate(
                    company=company, segment=segment, region=region,
                    fiscal_year=2025, share_pct=round(share, 1),
                    source="Industry Analyst Report",
                ))
    return estimates
