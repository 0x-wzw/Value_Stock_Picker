import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { getFinancials, getKeyMetrics } from "../api/companies";
import BarMetricChart from "../components/Charts/BarMetricChart";
import { formatMoney, formatMargin } from "../utils/format";
import clsx from "clsx";

type Tab = "income" | "balance" | "cashflow";

export default function FinancialsPage() {
  const { ticker = "" } = useParams<{ ticker: string }>();
  const sym = ticker.toUpperCase();

  const financials = useApi(() => getFinancials(sym), [sym]);
  const metrics = useApi(() => getKeyMetrics(sym), [sym]);
  const [tab, setTab] = useState<Tab>("income");

  if (financials.loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-4 animate-pulse">
        <div className="card h-12 w-64" />
        <div className="card h-80" />
      </div>
    );
  }

  const { income_statement = [], balance_sheet = [], cash_flow = [] } = financials.data ?? {};

  const incomeCharts = [
    { key: "revenue", label: "Revenue" },
    { key: "gross_profit", label: "Gross Profit" },
    { key: "operating_income", label: "Operating Income" },
    { key: "net_income", label: "Net Income" },
  ];

  const cashCharts = [
    { key: "operating_cf", label: "Operating Cash Flow" },
    { key: "free_cash_flow", label: "Free Cash Flow" },
    { key: "capex", label: "Capital Expenditure" },
  ];

  const bsCharts = [
    { key: "total_assets", label: "Total Assets" },
    { key: "total_equity", label: "Shareholders' Equity" },
    { key: "total_debt", label: "Total Debt" },
    { key: "cash_and_equivalents", label: "Cash & Equivalents" },
  ];

  const buildChartData = (rows: Record<string, unknown>[], key: string) =>
    rows
      .map((r) => ({
        period: (r.period as string)?.slice(0, 4) ?? "",
        value: r[key] as number | null,
      }))
      .reverse();

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{sym} — Financials</h1>
        <p className="text-slate-500 text-sm mt-1">Annual financial data from yfinance and SEC EDGAR</p>
      </div>

      {/* Key metrics summary */}
      {metrics.data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "5-yr Avg Free Cash Flow", value: formatMoney(metrics.data.avg_fcf_5y), help: "Cash left after expenses" },
            { label: "Revenue CAGR", value: metrics.data.revenue_cagr_pct != null ? `${metrics.data.revenue_cagr_pct.toFixed(1)}%` : "—", help: "Annual growth rate" },
            { label: "Return on Capital (ROIC)", value: metrics.data.roic_pct != null ? `${metrics.data.roic_pct.toFixed(1)}%` : "—", help: ">15% = excellent" },
            { label: "Gross Margin", value: formatMargin(metrics.data.gross_margin_pct ? metrics.data.gross_margin_pct / 100 : null), help: "Revenue kept after COGS" },
          ].map(({ label, value, help }) => (
            <div key={label} className="card !p-4">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="text-xl font-bold text-slate-900 mt-1">{value}</p>
              <p className="text-xs text-slate-400">{help}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab switcher */}
      <div className="flex gap-1 bg-slate-100 rounded-xl p-1 w-fit">
        {([
          { id: "income" as Tab, label: "Income Statement" },
          { id: "cashflow" as Tab, label: "Cash Flow" },
          { id: "balance" as Tab, label: "Balance Sheet" },
        ] as const).map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={clsx(
              "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              tab === t.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Charts */}
      {tab === "income" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {incomeCharts.map(({ key, label }) => (
            <div key={key} className="card">
              <BarMetricChart data={buildChartData(income_statement, key)} label={label} />
            </div>
          ))}
        </div>
      )}

      {tab === "cashflow" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {cashCharts.map(({ key, label }) => (
            <div key={key} className="card">
              <BarMetricChart data={buildChartData(cash_flow, key)} label={label} color="#8b5cf6" />
            </div>
          ))}
        </div>
      )}

      {tab === "balance" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {bsCharts.map(({ key, label }) => (
            <div key={key} className="card">
              <BarMetricChart data={buildChartData(balance_sheet, key)} label={label} color="#f59e0b" />
            </div>
          ))}
        </div>
      )}

      {/* Raw table */}
      <div className="card !p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-900 text-sm">
            {tab === "income" ? "Income Statement" : tab === "cashflow" ? "Cash Flow Statement" : "Balance Sheet"} — Annual Data
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50">
                <th className="text-left px-4 py-3 font-medium text-slate-500 sticky left-0 bg-slate-50">
                  Metric
                </th>
                {(tab === "income" ? income_statement : tab === "cashflow" ? cash_flow : balance_sheet)
                  .map((r) => (
                    <th key={r.period as string} className="text-right px-4 py-3 font-medium text-slate-500">
                      {(r.period as string)?.slice(0, 4)}
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(tab === "income"
                ? [
                    { key: "revenue", label: "Revenue" },
                    { key: "gross_profit", label: "Gross Profit" },
                    { key: "operating_income", label: "Operating Income" },
                    { key: "ebitda", label: "EBITDA" },
                    { key: "net_income", label: "Net Income" },
                    { key: "diluted_eps", label: "EPS (Diluted)" },
                  ]
                : tab === "cashflow"
                ? [
                    { key: "operating_cf", label: "Operating Cash Flow" },
                    { key: "capex", label: "Capital Expenditure" },
                    { key: "free_cash_flow", label: "Free Cash Flow" },
                    { key: "depreciation_amortization", label: "D&A" },
                    { key: "dividends_paid", label: "Dividends Paid" },
                  ]
                : [
                    { key: "total_assets", label: "Total Assets" },
                    { key: "current_assets", label: "Current Assets" },
                    { key: "total_liabilities", label: "Total Liabilities" },
                    { key: "total_debt", label: "Total Debt" },
                    { key: "total_equity", label: "Shareholders' Equity" },
                    { key: "cash_and_equivalents", label: "Cash & Equivalents" },
                    { key: "retained_earnings", label: "Retained Earnings" },
                  ]
              ).map(({ key, label }) => {
                const rows = tab === "income" ? income_statement : tab === "cashflow" ? cash_flow : balance_sheet;
                return (
                  <tr key={key} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-medium text-slate-700 sticky left-0 bg-white">{label}</td>
                    {rows.map((r, i) => {
                      const val = r[key] as number | null;
                      return (
                        <td
                          key={i}
                          className={clsx(
                            "px-4 py-2.5 text-right",
                            val != null && val < 0 ? "text-red-600" : "text-slate-700"
                          )}
                        >
                          {key === "diluted_eps"
                            ? val != null ? `$${val.toFixed(2)}` : "—"
                            : formatMoney(val)}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
