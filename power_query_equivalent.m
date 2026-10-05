// Power Query M equivalent of the currency-normalization and
// conflict-flagging logic in src/reconcile.py.
//
// NOTE: this M code is hand-written to mirror the tested Python logic
// in src/reconcile.py, showing how the same logic is expressed in M. It
// has not been executed inside a Power Query / Excel environment; the
// tested reference implementation is the Python code. The
// powerquery-sap-reporting project follows the same approach.

let
    Source = FinancialRecords, // assume a query/table with columns:
                                // Company, FiscalYear, ReportedCurrency,
                                // Revenue, EbitMarginPct, Source, AsOfDate

    // Step 1: normalize currency to EUR (mirrors normalize_currency)
    UsdToEurRate = 0.92,
    AddNormalizedRevenue = Table.AddColumn(
        Source,
        "RevenueEUR",
        each if [ReportedCurrency] = "USD"
             then Number.Round([Revenue] * UsdToEurRate, 1)
             else [Revenue]
    ),

    // Step 2: group by Company + FiscalYear to find multi-source rows
    // (mirrors find_conflicting_reports)
    Grouped = Table.Group(
        AddNormalizedRevenue,
        {"Company", "FiscalYear"},
        {
            {"SourceCount", each Table.RowCount(_), Int64.Type},
            {"MinRevenue", each List.Min([RevenueEUR]), type number},
            {"MaxRevenue", each List.Max([RevenueEUR]), type number},
            {"AllRows", each _, type table}
        }
    ),

    // Step 3: compute spread % and flag material conflicts (> 2%)
    AddSpread = Table.AddColumn(
        Grouped,
        "SpreadPct",
        each if [MinRevenue] = 0 then 0
             else Number.Round(([MaxRevenue] - [MinRevenue]) / [MinRevenue] * 100, 2)
    ),
    FlagConflicts = Table.AddColumn(
        AddSpread,
        "IsConflicting",
        each [SourceCount] > 1 and [SpreadPct] > 2.0
    ),

    // Step 4: keep only genuine multi-source conflicts for the
    // Data-Quality-Flags view (mirrors the ConflictFlag list)
    ConflictsOnly = Table.SelectRows(FlagConflicts, each [IsConflicting] = true)
in
    ConflictsOnly
