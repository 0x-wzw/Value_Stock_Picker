import React from "react";
import { Link } from "react-router-dom";
import { TrendingUp, TrendingDown, Minus, Search, Star, ArrowRight } from "lucide-react";
import { getMarketOverview, getSectorPerformance } from "../api/screener";
import { useApi } from "../hooks/useApi";
import { formatPct } from "../utils/format";
import clsx from "clsx";

interface IndexQuote {
  symbol: string;
  price: number | null;
  change_pct: number | null;
}

interface SectorRow {
  sector: string;
  etf: string;
  performance_pct: number | null;
  pe_ratio: number | null;
}

export default function Home() {
  const market = useApi<Record<string, IndexQuote>>(getMarketOverview);
  const sectors = useApi<SectorRow[]>(() => getSectorPerformance("1y"));

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Hero */}
      <div className="card bg-gradient-to-br from-brand-600 to-brand-700 text-white p-8 !border-0">
        <h1 className="text-2xl font-bold mb-2">Welcome to ValuePicker</h1>
        <p className="text-brand-100 text-sm mb-6 max-w-xl leading-relaxed">
          A research tool inspired by Li Lu's value investing methodology.
          Find great businesses at fair prices — no financial jargon required.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            to="/screener"
            className="flex items-center gap-2 bg-white text-brand-700 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-brand-50 transition-colors"
          >
            <Search className="w-4 h-4" />
            Find Stocks
          </Link>
          <Link
            to="/learn"
            className="flex items-center gap-2 bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-brand-400 transition-colors"
          >
            Learn Value Investing
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Market indices */}
      <section>
        <h2 className="text-base font-semibold text-slate-700 mb-3">Market Today</h2>
        {market.loading ? (
          <div className="grid grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card animate-pulse h-20" />
            ))}
          </div>
        ) : market.data ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {Object.entries(market.data).map(([name, idx]) => {
              const up = (idx.change_pct ?? 0) >= 0;
              const Icon = up ? TrendingUp : (idx.change_pct ?? 0) === 0 ? Minus : TrendingDown;
              return (
                <div key={name} className="card flex items-center gap-4">
                  <div className={clsx(
                    "w-10 h-10 rounded-full flex items-center justify-center shrink-0",
                    up ? "bg-emerald-50" : "bg-red-50"
                  )}>
                    <Icon className={clsx("w-5 h-5", up ? "text-emerald-600" : "text-red-500")} />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">{name}</p>
                    <p className="font-bold text-slate-900">
                      {idx.price != null ? idx.price.toLocaleString() : "—"}
                    </p>
                    <p className={clsx("text-xs font-medium", up ? "text-emerald-600" : "text-red-600")}>
                      {formatPct(idx.change_pct)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Market data unavailable</p>
        )}
      </section>

      {/* Sector heatmap */}
      <section>
        <h2 className="text-base font-semibold text-slate-700 mb-3">
          Sector Performance <span className="text-slate-400 font-normal text-sm">(1-year)</span>
        </h2>
        {sectors.loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {Array(11).fill(0).map((_, i) => (
              <div key={i} className="card animate-pulse h-16" />
            ))}
          </div>
        ) : sectors.data ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {sectors.data.map((s) => {
              const pct = s.performance_pct ?? 0;
              const positive = pct >= 0;
              return (
                <div
                  key={s.sector}
                  className={clsx(
                    "rounded-xl border p-3 flex flex-col gap-1",
                    positive
                      ? "bg-emerald-50 border-emerald-200"
                      : "bg-red-50 border-red-200"
                  )}
                >
                  <p className="text-xs font-medium text-slate-700 truncate">{s.sector}</p>
                  <p className={clsx("text-lg font-bold", positive ? "text-emerald-700" : "text-red-700")}>
                    {formatPct(pct)}
                  </p>
                  <p className="text-xs text-slate-400">{s.etf}</p>
                </div>
              );
            })}
          </div>
        ) : null}
      </section>

      {/* Quick links */}
      <section>
        <h2 className="text-base font-semibold text-slate-700 mb-3">Quick Access</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link to="/screener" className="card hover:shadow-md transition-shadow flex items-start gap-4 !p-5">
            <div className="w-10 h-10 bg-brand-50 rounded-lg flex items-center justify-center shrink-0">
              <Search className="w-5 h-5 text-brand-600" />
            </div>
            <div>
              <p className="font-semibold text-slate-900 mb-0.5">Stock Screener</p>
              <p className="text-sm text-slate-500">
                Filter 70+ stocks by quality, valuation, and profitability
              </p>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 ml-auto mt-1 shrink-0" />
          </Link>
          <Link to="/watchlist" className="card hover:shadow-md transition-shadow flex items-start gap-4 !p-5">
            <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center shrink-0">
              <Star className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <p className="font-semibold text-slate-900 mb-0.5">Your Watchlist</p>
              <p className="text-sm text-slate-500">
                Save interesting companies and track them over time
              </p>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 ml-auto mt-1 shrink-0" />
          </Link>
        </div>
      </section>
    </div>
  );
}
