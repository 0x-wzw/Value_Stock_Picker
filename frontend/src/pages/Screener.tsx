import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Search, SlidersHorizontal, TrendingUp, X } from "lucide-react";
import { filterStocks } from "../api/screener";
import { formatMoney, formatRatio, formatMargin, moatBadge } from "../utils/format";
import clsx from "clsx";

interface ScreenerResult {
  ticker: string;
  name: string;
  sector: string;
  market_cap: number | null;
  pe_ratio: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  debt_to_equity: number | null;
  roic_pct: number | null;
  fcf_yield_pct: number | null;
  moat_score: number | null;
  dividend_yield: number | null;
}

interface Filters {
  min_roic?: number;
  max_pe?: number;
  max_debt_to_equity?: number;
  min_gross_margin?: number;
  min_fcf_yield?: number;
  min_current_ratio?: number;
}

// Preset filters for non-financial users
const PRESETS = [
  {
    label: "Quality Compounders",
    description: "High returns, low debt",
    filters: { min_roic: 15, max_debt_to_equity: 0.5, min_gross_margin: 0.3 },
  },
  {
    label: "Cheap & Profitable",
    description: "Low P/E, positive FCF",
    filters: { max_pe: 15, min_fcf_yield: 5 },
  },
  {
    label: "Wide Moat Candidates",
    description: "High margins, strong returns",
    filters: { min_gross_margin: 0.4, min_roic: 12 },
  },
  {
    label: "Conservative",
    description: "Low debt, liquid balance sheet",
    filters: { max_debt_to_equity: 0.3, min_current_ratio: 2.0 },
  },
];

export default function Screener() {
  const [results, setResults] = useState<ScreenerResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<Filters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const run = async (f: Filters = filters) => {
    setLoading(true);
    try {
      const data = await filterStocks(f);
      setResults(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setFilters(preset.filters);
    setActivePreset(preset.label);
    run(preset.filters);
    setShowFilters(false);
  };

  const resetFilters = () => {
    setFilters({});
    setActivePreset(null);
    setResults([]);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Find Stocks</h1>
        <p className="text-slate-500 text-sm mt-1">
          Screen 70+ major stocks using value investing criteria. No finance knowledge needed — just pick a preset!
        </p>
      </div>

      {/* Preset buttons — most prominent for non-financial users */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-3">Quick Presets</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              onClick={() => applyPreset(p)}
              className={clsx(
                "text-left p-3 rounded-xl border transition-all",
                activePreset === p.label
                  ? "bg-brand-50 border-brand-300 ring-1 ring-brand-400"
                  : "bg-white border-slate-200 hover:border-brand-300 hover:bg-brand-50"
              )}
            >
              <p className="text-sm font-semibold text-slate-900">{p.label}</p>
              <p className="text-xs text-slate-500 mt-0.5">{p.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Custom filter toggle + Run */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Custom Filters
        </button>
        {(Object.keys(filters).length > 0 || results.length > 0) && (
          <button
            onClick={() => run()}
            disabled={loading}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            <Search className="w-4 h-4" />
            {loading ? "Searching…" : "Run Screen"}
          </button>
        )}
        {activePreset && (
          <button
            onClick={resetFilters}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-red-600 transition-colors"
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Custom filter panel */}
      {showFilters && (
        <div className="card">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-slate-400" />
            Custom Filters
            <span className="text-xs font-normal text-slate-400">(all optional)</span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {[
              {
                key: "min_roic",
                label: "Min. Return on Capital (%)",
                help: "How efficiently the company uses money. >15 is excellent.",
                placeholder: "e.g. 15",
              },
              {
                key: "max_pe",
                label: "Max. P/E Ratio",
                help: "Price relative to earnings. Lower = potentially cheaper.",
                placeholder: "e.g. 20",
              },
              {
                key: "max_debt_to_equity",
                label: "Max. Debt / Equity",
                help: "How much debt vs. equity. <0.5 is conservative.",
                placeholder: "e.g. 0.5",
              },
              {
                key: "min_gross_margin",
                label: "Min. Gross Margin (0–1)",
                help: "Revenue kept after direct costs. >0.4 often signals pricing power.",
                placeholder: "e.g. 0.35",
              },
              {
                key: "min_fcf_yield",
                label: "Min. FCF Yield (%)",
                help: "Free cash flow as % of market cap. Higher = more value.",
                placeholder: "e.g. 4",
              },
              {
                key: "min_current_ratio",
                label: "Min. Current Ratio",
                help: "Short-term assets vs. liabilities. >1.5 is healthy.",
                placeholder: "e.g. 1.5",
              },
            ].map(({ key, label, help, placeholder }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
                <p className="text-xs text-slate-400 mb-1.5">{help}</p>
                <input
                  type="number"
                  step="any"
                  placeholder={placeholder}
                  value={(filters as Record<string, number | undefined>)[key] ?? ""}
                  onChange={(e) =>
                    setFilters((prev) => ({
                      ...prev,
                      [key]: e.target.value ? parseFloat(e.target.value) : undefined,
                    }))
                  }
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm
                             focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
              </div>
            ))}
          </div>
          <div className="mt-5 flex gap-3">
            <button
              className="btn-primary text-sm"
              disabled={loading}
              onClick={() => { run(); setShowFilters(false); }}
            >
              {loading ? "Searching…" : "Apply Filters"}
            </button>
            <button className="btn-secondary text-sm" onClick={resetFilters}>Reset</button>
          </div>
        </div>
      )}

      {/* Results */}
      {loading && (
        <div className="card text-center py-12">
          <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-500 text-sm">Fetching data for 70+ stocks… this may take a moment.</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="card !p-0 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">
                {results.length} stocks matched
              </h2>
              {activePreset && (
                <p className="text-xs text-slate-500">{activePreset}</p>
              )}
            </div>
            <div className="flex items-center gap-1 text-xs text-slate-400">
              <TrendingUp className="w-3 h-3" />
              Sorted by moat score
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  {["Company", "Sector", "Mkt Cap", "P/E", "Gross Margin", "ROIC", "FCF Yield", "Debt/Equity", "Moat Score"].map((h) => (
                    <th key={h} className="text-left text-xs font-medium text-slate-500 px-4 py-3">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {results.map((r) => (
                  <tr
                    key={r.ticker}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        to={`/company/${r.ticker}`}
                        className="font-semibold text-brand-600 hover:underline"
                      >
                        {r.ticker}
                      </Link>
                      <p className="text-xs text-slate-500 truncate max-w-[160px]">{r.name}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{r.sector}</td>
                    <td className="px-4 py-3 text-slate-700">{formatMoney(r.market_cap)}</td>
                    <td className="px-4 py-3 text-slate-700">{formatRatio(r.pe_ratio)}</td>
                    <td className="px-4 py-3">
                      <span className={clsx(
                        "font-medium",
                        (r.gross_margin ?? 0) >= 0.4 ? "text-emerald-600" : "text-slate-700"
                      )}>
                        {formatMargin(r.gross_margin)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx(
                        "font-medium",
                        (r.roic_pct ?? 0) >= 15 ? "text-emerald-600" :
                        (r.roic_pct ?? 0) >= 8 ? "text-slate-700" : "text-red-600"
                      )}>
                        {r.roic_pct != null ? `${r.roic_pct.toFixed(1)}%` : "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {r.fcf_yield_pct != null ? `${r.fcf_yield_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-700">{formatRatio(r.debt_to_equity)}</td>
                    <td className="px-4 py-3">
                      <span className={moatBadge(r.moat_score)}>
                        {r.moat_score ?? "—"}/100
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && results.length === 0 && activePreset && (
        <div className="card text-center py-12">
          <p className="text-slate-500 text-sm">No stocks matched your criteria. Try loosening the filters.</p>
        </div>
      )}
    </div>
  );
}
