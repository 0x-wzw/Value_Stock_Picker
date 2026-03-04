import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { Calculator, Info } from "lucide-react";
import { runDCF, runOwnerEarnings } from "../api/valuation";
import { formatPrice, formatPct } from "../utils/format";
import clsx from "clsx";

interface ValuationResult {
  method: string;
  intrinsic_value_per_share: number | null;
  intrinsic_with_margin_of_safety: number | null;
  current_price: number | null;
  margin_of_safety_pct: number | null;
  upside_pct: number | null;
  error?: string;
}

type Method = "dcf" | "owner_earnings";

// Slider field configuration
const DCF_FIELDS = [
  {
    key: "growth_rate_yr1_5",
    label: "Growth Rate (Years 1–5)",
    help: "How fast do you expect free cash flow to grow in the first 5 years?",
    min: 0, max: 0.3, step: 0.01,
    default: 0.10,
    format: (v: number) => `${(v * 100).toFixed(0)}%`,
  },
  {
    key: "growth_rate_yr6_10",
    label: "Growth Rate (Years 6–10)",
    help: "Growth typically slows as a company matures",
    min: 0, max: 0.2, step: 0.01,
    default: 0.07,
    format: (v: number) => `${(v * 100).toFixed(0)}%`,
  },
  {
    key: "terminal_growth_rate",
    label: "Long-term Growth Rate",
    help: "Rate the business grows forever. Usually 2–3% (similar to the economy)",
    min: 0.01, max: 0.05, step: 0.005,
    default: 0.03,
    format: (v: number) => `${(v * 100).toFixed(1)}%`,
  },
  {
    key: "discount_rate",
    label: "Required Return (Discount Rate)",
    help: "Your minimum acceptable annual return. 10% is a common choice.",
    min: 0.06, max: 0.20, step: 0.01,
    default: 0.10,
    format: (v: number) => `${(v * 100).toFixed(0)}%`,
  },
  {
    key: "safety_margin",
    label: "Margin of Safety",
    help: "Discount applied to your estimate to protect against being wrong. 25–35% is typical.",
    min: 0, max: 0.5, step: 0.05,
    default: 0.25,
    format: (v: number) => `${(v * 100).toFixed(0)}%`,
  },
];

export default function ValuationPage() {
  const { ticker = "" } = useParams<{ ticker: string }>();
  const sym = ticker.toUpperCase();

  const [method, setMethod] = useState<Method>("dcf");
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const [dcfInputs, setDcfInputs] = useState<Record<string, number>>({
    growth_rate_yr1_5: 0.10,
    growth_rate_yr6_10: 0.07,
    terminal_growth_rate: 0.03,
    discount_rate: 0.10,
    safety_margin: 0.25,
  });

  const [oeInputs, setOeInputs] = useState<Record<string, number>>({
    growth_rate: 0.08,
    discount_rate: 0.10,
    years: 10,
    terminal_multiple: 15,
    safety_margin: 0.25,
  });

  const runCalc = async () => {
    setLoading(true);
    try {
      const data =
        method === "dcf"
          ? await runDCF(sym, dcfInputs)
          : await runOwnerEarnings(sym, oeInputs);
      setResult(data);
    } catch (e: unknown) {
      setResult({ method, intrinsic_value_per_share: null, intrinsic_with_margin_of_safety: null, current_price: null, margin_of_safety_pct: null, upside_pct: null, error: String(e) });
    } finally {
      setLoading(false);
    }
  };

  const upside = result?.upside_pct ?? 0;
  const mosGood = (result?.margin_of_safety_pct ?? 0) > 20;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Calculator className="w-6 h-6 text-purple-600" />
          Valuation Calculator
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Estimate what <b>{sym}</b> is worth based on its cash flows. Adjust the sliders to see how your assumptions affect the result.
        </p>
      </div>

      {/* Method selector */}
      <div className="card !p-1 flex gap-1">
        {[
          { id: "dcf" as Method, label: "DCF (Cash Flow)", desc: "Most common method" },
          { id: "owner_earnings" as Method, label: "Owner Earnings", desc: "Buffett's favourite" },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => setMethod(m.id)}
            className={clsx(
              "flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors text-center",
              method === m.id
                ? "bg-brand-600 text-white shadow"
                : "text-slate-600 hover:bg-slate-50"
            )}
          >
            {m.label}
            <span className="block text-xs font-normal opacity-70">{m.desc}</span>
          </button>
        ))}
      </div>

      {/* Inputs */}
      <div className="card space-y-5">
        <div className="flex items-center gap-2 text-sm text-slate-500 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <Info className="w-4 h-4 text-blue-500 shrink-0" />
          Adjust the sliders below — the calculator uses the company's actual financial data fetched live. The inputs just control your assumptions about the future.
        </div>

        {method === "dcf" ? (
          DCF_FIELDS.map((field) => (
            <div key={field.key}>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium text-slate-700">{field.label}</label>
                <span className="text-sm font-bold text-brand-600">
                  {field.format(dcfInputs[field.key] ?? field.default)}
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-2">{field.help}</p>
              <input
                type="range"
                min={field.min}
                max={field.max}
                step={field.step}
                value={dcfInputs[field.key] ?? field.default}
                onChange={(e) =>
                  setDcfInputs((prev) => ({ ...prev, [field.key]: parseFloat(e.target.value) }))
                }
                className="w-full accent-brand-600"
              />
              <div className="flex justify-between text-xs text-slate-400 mt-0.5">
                <span>{field.format(field.min)}</span>
                <span>{field.format(field.max)}</span>
              </div>
            </div>
          ))
        ) : (
          [
            { key: "growth_rate", label: "Expected Growth Rate", min: 0, max: 0.20, step: 0.01, default: 0.08, format: (v: number) => `${(v*100).toFixed(0)}%`, help: "Annual growth in owner earnings" },
            { key: "discount_rate", label: "Required Return", min: 0.06, max: 0.20, step: 0.01, default: 0.10, format: (v: number) => `${(v*100).toFixed(0)}%`, help: "Minimum annual return you want" },
            { key: "years", label: "Projection Period (years)", min: 5, max: 20, step: 1, default: 10, format: (v: number) => `${v} yrs`, help: "How many years to project" },
            { key: "terminal_multiple", label: "Exit Multiple (P/E)", min: 8, max: 25, step: 1, default: 15, format: (v: number) => `${v}×`, help: "What P/E multiple to use at the end of the period" },
            { key: "safety_margin", label: "Margin of Safety", min: 0, max: 0.5, step: 0.05, default: 0.25, format: (v: number) => `${(v*100).toFixed(0)}%`, help: "Discount to protect against errors" },
          ].map((field) => (
            <div key={field.key}>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium text-slate-700">{field.label}</label>
                <span className="text-sm font-bold text-brand-600">
                  {field.format(oeInputs[field.key] ?? field.default)}
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-2">{field.help}</p>
              <input
                type="range"
                min={field.min}
                max={field.max}
                step={field.step}
                value={oeInputs[field.key] ?? field.default}
                onChange={(e) =>
                  setOeInputs((prev) => ({ ...prev, [field.key]: parseFloat(e.target.value) }))
                }
                className="w-full accent-brand-600"
              />
            </div>
          ))
        )}

        <button
          className="btn-primary w-full py-3 text-sm font-semibold flex items-center justify-center gap-2"
          onClick={runCalc}
          disabled={loading}
        >
          <Calculator className="w-4 h-4" />
          {loading ? "Calculating…" : "Calculate Intrinsic Value"}
        </button>
      </div>

      {/* Result */}
      {result && !result.error && (
        <div className={clsx(
          "card border-2",
          mosGood ? "border-emerald-300 bg-emerald-50" : "border-slate-200"
        )}>
          <h2 className="font-bold text-slate-900 text-lg mb-4">Results</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div className="text-center">
              <p className="text-xs text-slate-500 mb-1">Current Price</p>
              <p className="text-2xl font-bold text-slate-900">{formatPrice(result.current_price)}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-slate-500 mb-1">Intrinsic Value</p>
              <p className="text-2xl font-bold text-slate-900">{formatPrice(result.intrinsic_value_per_share)}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-slate-500 mb-1">With Safety Margin</p>
              <p className={clsx("text-2xl font-bold", mosGood ? "text-emerald-700" : "text-slate-900")}>
                {formatPrice(result.intrinsic_with_margin_of_safety)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-slate-500 mb-1">Potential Upside</p>
              <p className={clsx("text-2xl font-bold", upside >= 0 ? "text-emerald-700" : "text-red-600")}>
                {formatPct(upside)}
              </p>
            </div>
          </div>

          <div className={clsx(
            "p-4 rounded-xl text-sm leading-relaxed",
            mosGood ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
          )}>
            {mosGood ? (
              <>
                <b>Potentially undervalued.</b> Based on your assumptions, the stock appears to trade below its intrinsic value with a margin of safety of {result.margin_of_safety_pct?.toFixed(0)}%. This suggests a potential buying opportunity — but remember, the assumptions matter greatly.
              </>
            ) : upside >= 0 ? (
              <>
                The stock appears to be trading around its fair value based on your assumptions. The margin of safety is relatively small — consider waiting for a larger discount before investing.
              </>
            ) : (
              <>
                <b>Potentially overvalued.</b> Based on your assumptions, the current price appears higher than intrinsic value. This doesn't mean you should sell — future growth could justify the premium — but proceed cautiously.
              </>
            )}
          </div>

          <p className="text-xs text-slate-400 mt-3">
            These estimates are highly sensitive to your growth assumptions. Always do your own due diligence.
          </p>
        </div>
      )}

      {result?.error && (
        <div className="card border border-red-200 bg-red-50">
          <p className="text-sm text-red-700">
            <b>Could not run valuation:</b> {result.error}
          </p>
          <p className="text-xs text-red-500 mt-1">
            This usually means there isn't enough financial data available for {sym}.
          </p>
        </div>
      )}
    </div>
  );
}
