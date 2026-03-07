import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { TrendingUp, Plus, Trash2, TrendingDown } from "lucide-react";
import { getQuote } from "../api/companies";
import { formatPrice, formatPct, formatMoney } from "../utils/format";
import clsx from "clsx";

interface Holding {
  id: string;
  ticker: string;
  shares: number;
  avgCost: number;
  thesis: string;
  dateAdded: string;
}

interface HoldingLive extends Holding {
  currentPrice?: number;
  changePct?: number;
  currentValue?: number;
  gainLoss?: number;
  gainLossPct?: number;
}

const STORAGE_KEY = "vsp_portfolio";

function load(): Holding[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function save(items: Holding[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export default function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>(load);
  const [live, setLive] = useState<Record<string, { price?: number; change_pct?: number }>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ ticker: "", shares: "", avgCost: "", thesis: "" });

  useEffect(() => {
    holdings.forEach(async (h) => {
      try {
        const q = await getQuote(h.ticker);
        setLive((prev) => ({ ...prev, [h.ticker]: q }));
      } catch {
        // ignore
      }
    });
  }, [holdings.length]);

  const addHolding = () => {
    const t = form.ticker.trim().toUpperCase();
    if (!t || !form.shares || !form.avgCost) return;
    const updated = [
      ...holdings,
      {
        id: crypto.randomUUID(),
        ticker: t,
        shares: parseFloat(form.shares),
        avgCost: parseFloat(form.avgCost),
        thesis: form.thesis.trim(),
        dateAdded: new Date().toISOString(),
      },
    ];
    setHoldings(updated);
    save(updated);
    setForm({ ticker: "", shares: "", avgCost: "", thesis: "" });
    setShowAdd(false);
  };

  const remove = (id: string) => {
    const updated = holdings.filter((h) => h.id !== id);
    setHoldings(updated);
    save(updated);
  };

  const enriched: HoldingLive[] = holdings.map((h) => {
    const q = live[h.ticker];
    const cp = q?.price;
    const cv = cp ? cp * h.shares : undefined;
    const costBasis = h.avgCost * h.shares;
    const gl = cv != null ? cv - costBasis : undefined;
    const glPct = gl != null ? (gl / costBasis) * 100 : undefined;
    return { ...h, currentPrice: cp, changePct: q?.change_pct, currentValue: cv, gainLoss: gl, gainLossPct: glPct };
  });

  const totalValue = enriched.reduce((s, h) => s + (h.currentValue ?? h.avgCost * h.shares), 0);
  const totalCost = enriched.reduce((s, h) => s + h.avgCost * h.shares, 0);
  const totalGl = totalValue - totalCost;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-brand-600" />
            Portfolio
          </h1>
          <p className="text-slate-500 text-sm mt-1">Track your value investing holdings</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-primary text-sm flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Holding
        </button>
      </div>

      {/* Summary */}
      {holdings.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card !p-4">
            <p className="text-xs text-slate-500">Portfolio Value</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{formatMoney(totalValue)}</p>
          </div>
          <div className="card !p-4">
            <p className="text-xs text-slate-500">Total Cost</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{formatMoney(totalCost)}</p>
          </div>
          <div className="card !p-4">
            <p className="text-xs text-slate-500">Total Gain / Loss</p>
            <p className={clsx("text-2xl font-bold mt-1", totalGl >= 0 ? "text-emerald-600" : "text-red-600")}>
              {totalGl >= 0 ? "+" : ""}{formatMoney(totalGl)}
            </p>
          </div>
        </div>
      )}

      {/* Add form */}
      {showAdd && (
        <div className="card">
          <h3 className="font-semibold text-slate-900 mb-4">Add Holding</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { key: "ticker", label: "Ticker", placeholder: "AAPL", type: "text" },
              { key: "shares", label: "Number of Shares", placeholder: "10", type: "number" },
              { key: "avgCost", label: "Average Cost per Share ($)", placeholder: "150.00", type: "number" },
            ].map(({ key, label, placeholder, type }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
                <input
                  type={type}
                  placeholder={placeholder}
                  value={(form as Record<string, string>)[key]}
                  onChange={(e) => setForm((p) => ({ ...p, [key]: key === "ticker" ? e.target.value.toUpperCase() : e.target.value }))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
              </div>
            ))}
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Investment Thesis <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <textarea
                placeholder="Why did you buy this? What needs to be true for this to be a good investment?"
                value={form.thesis}
                onChange={(e) => setForm((p) => ({ ...p, thesis: e.target.value }))}
                rows={2}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none"
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button className="btn-primary text-sm" onClick={addHolding}>Add</button>
            <button className="btn-secondary text-sm" onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Holdings list */}
      {holdings.length === 0 ? (
        <div className="card text-center py-16">
          <TrendingUp className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">No holdings yet</p>
          <p className="text-slate-400 text-sm mt-1">Track your value investing positions here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {enriched.map((h) => {
            const glPositive = (h.gainLossPct ?? 0) >= 0;
            return (
              <div key={h.id} className="card">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold text-brand-700">{h.ticker.slice(0, 4)}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-3 mb-1">
                      <Link to={`/company/${h.ticker}`} className="font-semibold text-brand-600 hover:underline">
                        {h.ticker}
                      </Link>
                      <span className="text-sm text-slate-500">{h.shares} shares @ {formatPrice(h.avgCost)}</span>
                      {h.currentPrice && (
                        <span className="flex items-center gap-1 text-sm">
                          <span className="text-slate-700">{formatPrice(h.currentPrice)}</span>
                          <span className={clsx("text-xs font-semibold", h.changePct != null && h.changePct >= 0 ? "text-emerald-600" : "text-red-600")}>
                            {formatPct(h.changePct ?? null)}
                          </span>
                        </span>
                      )}
                    </div>
                    {h.thesis && <p className="text-sm text-slate-500 line-clamp-2">{h.thesis}</p>}
                    <div className="flex flex-wrap gap-4 mt-2 text-xs text-slate-500">
                      <span>Cost basis: {formatMoney(h.avgCost * h.shares)}</span>
                      {h.currentValue != null && <span>Current: {formatMoney(h.currentValue)}</span>}
                      {h.gainLoss != null && (
                        <span className={clsx("font-semibold", glPositive ? "text-emerald-600" : "text-red-600")}>
                          {glPositive ? "+" : ""}{formatMoney(h.gainLoss)} ({h.gainLossPct?.toFixed(1)}%)
                        </span>
                      )}
                    </div>
                  </div>
                  <button onClick={() => remove(h.id)} className="p-1.5 text-slate-400 hover:text-red-500 transition-colors shrink-0">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
