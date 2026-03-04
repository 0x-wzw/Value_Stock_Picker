import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Globe,
  Users,
  ChevronRight,
  BarChart2,
  FileText,
  Calculator,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import {
  getCompanyFull,
  getPriceHistory,
  getFilings,
  getNews,
} from "../api/companies";
import PriceChart from "../components/Charts/PriceChart";
import MetricCard from "../components/Cards/MetricCard";
import SignalBadge from "../components/Cards/SignalBadge";
import {
  formatMoney,
  formatPrice,
  formatPct,
  formatRatio,
  formatMargin,
  pctColor,
} from "../utils/format";
import clsx from "clsx";

type Period = "6mo" | "1y" | "2y" | "5y";
const PERIODS: Period[] = ["6mo", "1y", "2y", "5y"];

export default function CompanyDashboard() {
  const { ticker = "" } = useParams<{ ticker: string }>();
  const sym = ticker.toUpperCase();

  const [period, setPeriod] = useState<Period>("1y");

  const company = useApi(() => getCompanyFull(sym), [sym]);
  const history = useApi(
    () => getPriceHistory(sym, period, period === "5y" ? "1wk" : "1d"),
    [sym, period]
  );
  const filings = useApi(() => getFilings(sym, "10-K,10-Q"), [sym]);
  const news = useApi(() => getNews(sym, 5), [sym]);

  if (company.loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-4 animate-pulse">
        <div className="card h-32" />
        <div className="grid grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => <div key={i} className="card h-20" />)}
        </div>
        <div className="card h-60" />
      </div>
    );
  }

  if (company.error || !company.data) {
    return (
      <div className="max-w-5xl mx-auto card text-center py-12">
        <p className="text-slate-500">Could not load data for <b>{sym}</b>.</p>
        <p className="text-xs text-slate-400 mt-1">{company.error}</p>
      </div>
    );
  }

  const { quote, overview, metrics, signals, recent_news } = company.data;
  const positive = (quote?.change_pct ?? 0) >= 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-10 h-10 bg-brand-50 rounded-lg flex items-center justify-center">
                <span className="text-xs font-bold text-brand-700">{sym.slice(0, 4)}</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">{overview?.name || sym}</h1>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>{sym}</span>
                  {overview?.exchange && <><span>·</span><span>{overview.exchange}</span></>}
                  {overview?.sector && <><span>·</span><span>{overview.sector}</span></>}
                </div>
              </div>
            </div>
            {overview?.website && (
              <a
                href={overview.website}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-brand-600 hover:underline mt-1"
              >
                <Globe className="w-3 h-3" />
                {overview.website.replace(/https?:\/\//, "")}
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          {/* Price block */}
          <div className="text-right">
            <p className="text-3xl font-bold text-slate-900">
              {formatPrice(quote?.price)}
            </p>
            <div className={clsx("flex items-center justify-end gap-1 text-sm font-semibold mt-0.5",
              positive ? "text-emerald-600" : "text-red-600")}>
              {positive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {formatPct(quote?.change_pct)}
              <span className="font-normal text-slate-400 ml-1">today</span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              52w: {formatPrice(quote?.["52w_low"])} – {formatPrice(quote?.["52w_high"])}
            </p>
          </div>
        </div>

        {/* Nav tabs */}
        <div className="flex gap-1 mt-4 pt-4 border-t border-slate-100">
          {[
            { label: "Overview", to: `/company/${sym}` },
            { label: "Financials", to: `/company/${sym}/financials` },
            { label: "Valuation", to: `/company/${sym}/valuation` },
            { label: "Filings", to: `/company/${sym}/filings` },
          ].map((tab) => (
            <Link
              key={tab.to}
              to={tab.to}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                location.pathname === tab.to
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </div>

      {/* Key metrics row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCard
          label="Market Cap"
          value={formatMoney(overview?.market_cap)}
          sub="Total company value"
          size="sm"
        />
        <MetricCard
          label="P/E Ratio"
          value={formatRatio(overview?.pe_ratio)}
          sub="Price ÷ earnings"
          size="sm"
          tooltip="How many years of current earnings you're paying. Lower is generally cheaper."
        />
        <MetricCard
          label="Return on Capital"
          value={metrics?.roic_pct != null ? `${metrics.roic_pct.toFixed(1)}%` : "—"}
          sub="How efficiently it uses money"
          trend={
            (metrics?.roic_pct ?? 0) >= 15
              ? "up"
              : (metrics?.roic_pct ?? 0) >= 8
              ? "neutral"
              : "down"
          }
          size="sm"
          tooltip="ROIC > 15% suggests a business with a strong competitive advantage."
        />
        <MetricCard
          label="Free Cash Flow Yield"
          value={metrics?.fcf_yield_pct != null ? `${metrics.fcf_yield_pct.toFixed(1)}%` : "—"}
          sub="Cash generated vs. price"
          trend={(metrics?.fcf_yield_pct ?? 0) >= 5 ? "up" : "neutral"}
          size="sm"
          tooltip="Free cash flow as % of market cap. Higher = more cash generated per dollar invested."
        />
      </div>

      {/* Price chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Price History</h2>
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={clsx(
                  "px-2.5 py-1 rounded text-xs font-medium transition-colors",
                  period === p
                    ? "bg-brand-100 text-brand-700"
                    : "text-slate-500 hover:bg-slate-100"
                )}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        {history.loading ? (
          <div className="h-52 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <PriceChart data={history.data?.data ?? []} ticker={sym} />
        )}
      </div>

      {/* Business description */}
      {overview?.description && (
        <div className="card">
          <h2 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-slate-400" />
            About {overview.name}
          </h2>
          <p className="text-sm text-slate-600 leading-relaxed">{overview.description}</p>
          {overview.employees && (
            <p className="text-xs text-slate-400 mt-3">
              {overview.employees.toLocaleString()} employees · {overview.country}
            </p>
          )}
        </div>
      )}

      {/* Value signals */}
      {signals && ((signals.flags?.length ?? 0) > 0 || (signals.warnings?.length ?? 0) > 0) && (
        <div className="card">
          <h2 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-slate-400" />
            Value Investing Signals
          </h2>

          {signals.fair_value_base && (
            <div className="mb-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <p className="text-xs text-slate-500 mb-1">Quick Fair Value Estimate (FCF-based)</p>
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-xs text-slate-400">Conservative (15× FCF)</p>
                  <p className="text-lg font-bold text-slate-900">
                    {formatPrice(signals.fair_value_conservative)}
                  </p>
                </div>
                <div className="w-px h-8 bg-slate-200" />
                <div>
                  <p className="text-xs text-slate-400">Base (20× FCF)</p>
                  <p className="text-lg font-bold text-slate-900">
                    {formatPrice(signals.fair_value_base)}
                  </p>
                </div>
                {signals.margin_of_safety_conservative_pct != null && (
                  <>
                    <div className="w-px h-8 bg-slate-200" />
                    <div>
                      <p className="text-xs text-slate-400">Margin of Safety</p>
                      <p className={clsx(
                        "text-lg font-bold",
                        signals.margin_of_safety_conservative_pct > 20 ? "text-emerald-600" : "text-red-600"
                      )}>
                        {signals.margin_of_safety_conservative_pct.toFixed(0)}%
                      </p>
                    </div>
                  </>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2">
                * Rough estimate only. Run a full DCF in the Valuation tab.
              </p>
            </div>
          )}

          <div className="space-y-2">
            {signals.flags?.map((f: string, i: number) => (
              <SignalBadge key={i} text={f} variant="good" />
            ))}
            {signals.warnings?.map((w: string, i: number) => (
              <SignalBadge key={i} text={w} variant="warn" />
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Fundamentals */}
        <div className="card">
          <h2 className="font-semibold text-slate-900 mb-4">Key Fundamentals</h2>
          <dl className="space-y-3">
            {[
              { label: "Gross Margin", value: formatMargin(overview?.gross_margin), help: "Revenue kept after direct costs" },
              { label: "Operating Margin", value: formatMargin(overview?.operating_margin), help: "Profit before interest & taxes" },
              { label: "Return on Equity", value: formatMargin(overview?.roe), help: "Profit generated on shareholders' money" },
              { label: "Debt / Equity", value: formatRatio(overview?.debt_to_equity), help: "Lower = less financial risk" },
              { label: "Current Ratio", value: formatRatio(overview?.current_ratio), help: "Short-term assets vs. liabilities" },
              { label: "Dividend Yield", value: overview?.dividend_yield != null ? formatMargin(overview.dividend_yield) : "—", help: "Annual dividend as % of price" },
            ].map(({ label, value, help }) => (
              <div key={label} className="flex justify-between items-center text-sm">
                <div>
                  <span className="text-slate-600">{label}</span>
                  <p className="text-xs text-slate-400">{help}</p>
                </div>
                <span className="font-semibold text-slate-900">{value}</span>
              </div>
            ))}
          </dl>
          <Link
            to={`/company/${sym}/financials`}
            className="mt-4 flex items-center gap-1 text-sm text-brand-600 hover:underline"
          >
            <BarChart2 className="w-4 h-4" />
            View Full Financials
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {/* SEC Filings */}
        <div className="card">
          <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-400" />
            Recent SEC Filings
          </h2>
          {filings.loading ? (
            <p className="text-sm text-slate-400">Loading…</p>
          ) : (filings.data as unknown[])?.length === 0 ? (
            <p className="text-sm text-slate-400">No filings found</p>
          ) : (
            <div className="space-y-2">
              {((filings.data as unknown[]) ?? []).slice(0, 6).map((f: unknown, i: number) => {
                const filing = f as Record<string, string>;
                return (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-medium text-slate-700">{filing.form_type}</span>
                      <span className="text-slate-400 ml-2 text-xs">{filing.filing_date}</span>
                    </div>
                    {filing.document_url ? (
                      <a
                        href={filing.document_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-600 hover:underline flex items-center gap-1 text-xs"
                      >
                        View <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <a
                        href={filing.edgar_viewer_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-600 hover:underline flex items-center gap-1 text-xs"
                      >
                        EDGAR <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          <Link
            to={`/company/${sym}/filings`}
            className="mt-4 flex items-center gap-1 text-sm text-brand-600 hover:underline"
          >
            <FileText className="w-4 h-4" />
            All Filings
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* News */}
      {(recent_news?.length ?? 0) > 0 && (
        <div className="card">
          <h2 className="font-semibold text-slate-900 mb-4">Recent News</h2>
          <div className="space-y-3">
            {(recent_news ?? []).map((item: Record<string, string>, i: number) => (
              <a
                key={i}
                href={item.link}
                target="_blank"
                rel="noreferrer"
                className="flex items-start gap-3 group"
              >
                {item.thumbnail && (
                  <img
                    src={item.thumbnail}
                    alt=""
                    className="w-14 h-14 rounded-lg object-cover shrink-0 bg-slate-100"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                  />
                )}
                <div>
                  <p className="text-sm font-medium text-slate-900 group-hover:text-brand-600 transition-colors line-clamp-2">
                    {item.title}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {item.publisher} · {item.published_at?.slice(0, 10)}
                  </p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Quick valuation CTA */}
      <Link
        to={`/company/${sym}/valuation`}
        className="card flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer group"
      >
        <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center shrink-0">
          <Calculator className="w-6 h-6 text-purple-600" />
        </div>
        <div className="flex-1">
          <p className="font-semibold text-slate-900">Run a Valuation</p>
          <p className="text-sm text-slate-500">
            Use our DCF calculator to estimate intrinsic value with your own assumptions
          </p>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-brand-600 transition-colors" />
      </Link>
    </div>
  );
}
