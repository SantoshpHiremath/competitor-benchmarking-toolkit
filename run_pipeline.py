"""
Runs the full competitor-benchmarking pipeline end to end: generate
synthetic multi-source data -> normalize currency -> flag conflicts and
missing fields -> resolve conflicts -> rank revenue growth -> benchmark
margins -> identify segment leaders -> write a real, formatted Excel
report.
"""

from src.data_sources import (
    generate_financial_records,
    generate_market_share_estimates,
    generate_product_announcements,
)
from src.reconcile import (
    find_conflicting_reports,
    find_missing_fields,
    normalize_currency,
    resolve_conflicts_preferring_source,
)
from src.benchmarking import margin_benchmark, revenue_growth_ranking, segment_region_leaders
from src.report import build_report


def main():
    print("=== Competitor Benchmarking Pipeline ===\n")

    raw_financials = generate_financial_records()
    announcements = generate_product_announcements()
    share_estimates = generate_market_share_estimates()

    print(f"Loaded {len(raw_financials)} raw financial records from "
          f"{len({r.source for r in raw_financials})} sources.")

    normalized = normalize_currency(raw_financials)
    print("Normalized all revenue figures to EUR.")

    conflicts = find_conflicting_reports(normalized)
    missing = find_missing_fields(normalized)
    print(f"Data-quality check: {len(conflicts)} conflicting report(s), "
          f"{len(missing)} missing field(s) flagged.")
    for c in conflicts:
        print(f"  CONFLICT: {c.company} FY{c.fiscal_year} — spread {c.spread_pct}% "
              f"across {[s for s, _ in c.values]}")
    for m in missing:
        print(f"  MISSING: {m.company} FY{m.fiscal_year} — {m.field} not disclosed "
              f"(source: {m.source})")

    resolved = resolve_conflicts_preferring_source(normalized)
    print(f"\nResolved to {len(resolved)} records (preferring Annual Report where conflicting).")

    growth = revenue_growth_ranking(resolved)
    print("\nRevenue growth ranking (FY2024 -> FY2025):")
    for g in growth:
        print(f"  #{g.rank} {g.company}: {g.fy2024_revenue} -> {g.fy2025_revenue} EUR M ({g.growth_pct:+.1f}%)")

    margins = margin_benchmark(resolved, fiscal_year=2025)
    print("\nEBIT margin benchmark (FY2025, peer average excludes undisclosed):")
    for m in margins:
        print(f"  {m.company}: {m.ebit_margin_pct}% ({m.vs_peer_average_pp:+.1f}pp vs peer avg)")

    leaders = segment_region_leaders(share_estimates)
    print(f"\nIdentified segment/region leaders for {len(leaders)} combinations.")

    output_path = "output/competitor_benchmark_report.xlsx"
    import os
    os.makedirs("output", exist_ok=True)
    build_report(output_path, resolved, growth, margins, leaders, conflicts, missing, announcements)
    print(f"\nReport written to {output_path}")


if __name__ == "__main__":
    main()
