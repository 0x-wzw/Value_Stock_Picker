/** Format a number as compact currency: 1,234,567,890 → $1.23B */
export function formatMoney(n: number | null | undefined, currency = "USD"): string {
  if (n == null) return "—";
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  const sym = currency === "USD" ? "$" : currency + " ";
  if (abs >= 1e12) return `${sign}${sym}${(abs / 1e12).toFixed(2)}T`;
  if (abs >= 1e9)  return `${sign}${sym}${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6)  return `${sign}${sym}${(abs / 1e6).toFixed(1)}M`;
  if (abs >= 1e3)  return `${sign}${sym}${(abs / 1e3).toFixed(0)}K`;
  return `${sign}${sym}${abs.toFixed(2)}`;
}

export function formatPrice(n: number | null | undefined): string {
  if (n == null) return "—";
  return `$${n.toFixed(2)}`;
}

export function formatPct(n: number | null | undefined, decimals = 1): string {
  if (n == null) return "—";
  // Values already in percent form (e.g., 12.5 → "12.5%")
  return `${n >= 0 ? "+" : ""}${n.toFixed(decimals)}%`;
}

export function formatRatio(n: number | null | undefined, decimals = 1): string {
  if (n == null) return "—";
  return `${n.toFixed(decimals)}x`;
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

/** Convert a 0-1 margin to a percentage string (e.g. 0.423 → "42.3%") */
export function formatMargin(n: number | null | undefined): string {
  if (n == null) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

export function pctColor(n: number | null | undefined): string {
  if (n == null) return "text-slate-500";
  return n >= 0 ? "text-emerald-600" : "text-red-600";
}

export function moatBadge(score: number | null | undefined): string {
  if (score == null) return "badge-neutral";
  if (score >= 70) return "badge-good";
  if (score >= 40) return "badge-warn";
  return "badge-bad";
}
