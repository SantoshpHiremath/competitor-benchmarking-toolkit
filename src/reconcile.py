"""
Reconciliation and data-quality checks for multi-source financial data.

This is the "collect, structure, validate, and analyze market, competitor,
financial, product, project, and industry information from internal and
external sources" step: raw records from several sources rarely agree
perfectly, and a real analyst has to normalize currency, flag conflicts,
and flag gaps -- not just concatenate everything into one table.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .data_sources import FinancialRecord

USD_TO_EUR = 0.92  # fixed illustrative rate -- documented, not hidden


def normalize_currency(records: list[FinancialRecord]) -> list[FinancialRecord]:
    """Return a new list where every record's revenue is expressed in EUR,
    converting USD-reported records at a fixed, documented rate."""
    normalized = []
    for r in records:
        if r.reported_currency == "USD":
            normalized.append(FinancialRecord(
                company=r.company, fiscal_year=r.fiscal_year,
                reported_currency="EUR", revenue=round(r.revenue * USD_TO_EUR, 1),
                ebit_margin_pct=r.ebit_margin_pct, source=r.source,
                as_of_date=r.as_of_date,
            ))
        else:
            normalized.append(r)
    return normalized


@dataclass
class ConflictFlag:
    company: str
    fiscal_year: int
    values: list[tuple[str, float]]  # (source, revenue) pairs
    spread_pct: float


def find_conflicting_reports(records: list[FinancialRecord]) -> list[ConflictFlag]:
    """Find company/fiscal_year pairs reported by more than one source
    with materially different revenue figures (>2% spread) -- these need
    a human decision on which source to trust, and should never be
    silently averaged or silently overwritten."""
    by_key: dict[tuple[str, int], list[FinancialRecord]] = {}
    for r in records:
        by_key.setdefault((r.company, r.fiscal_year), []).append(r)

    flags = []
    for (company, year), group in by_key.items():
        if len(group) < 2:
            continue
        values = [r.revenue for r in group]
        spread_pct = (max(values) - min(values)) / min(values) * 100
        if spread_pct > 2.0:
            flags.append(ConflictFlag(
                company=company, fiscal_year=year,
                values=[(r.source, r.revenue) for r in group],
                spread_pct=round(spread_pct, 2),
            ))
    return flags


@dataclass
class MissingDataFlag:
    company: str
    fiscal_year: int
    field: str
    source: str


def find_missing_fields(records: list[FinancialRecord]) -> list[MissingDataFlag]:
    """Flag records with a missing (NaN) required field -- e.g. a
    competitor that didn't disclose EBIT margin for a given year. These
    should show up explicitly in a report as 'not disclosed', never as a
    silent zero."""
    flags = []
    for r in records:
        if isinstance(r.ebit_margin_pct, float) and math.isnan(r.ebit_margin_pct):
            flags.append(MissingDataFlag(
                company=r.company, fiscal_year=r.fiscal_year,
                field="ebit_margin_pct", source=r.source,
            ))
    return flags


def resolve_conflicts_preferring_source(
    records: list[FinancialRecord], preferred_source: str = "Annual Report",
) -> list[FinancialRecord]:
    """Given conflicting reports for the same company/year, keep the
    record from the preferred, most-authoritative source (Annual Report
    over Analyst Estimate or Press Release) -- a documented, explicit
    tie-breaking rule rather than an arbitrary 'first row wins'."""
    by_key: dict[tuple[str, int], list[FinancialRecord]] = {}
    for r in records:
        by_key.setdefault((r.company, r.fiscal_year), []).append(r)

    resolved = []
    for (_company, _year), group in by_key.items():
        if len(group) == 1:
            resolved.append(group[0])
            continue
        preferred = [r for r in group if r.source == preferred_source]
        resolved.append(preferred[0] if preferred else group[0])
    return resolved
