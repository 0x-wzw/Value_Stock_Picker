import React, { useState, useEffect, useRef } from "react";
import { Search, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { searchCompanies } from "../../api/companies";

interface Result {
  ticker: string;
  name: string;
  exchange: string;
  type: string;
}

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (query.trim().length < 1) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchCompanies(query);
        setResults(data.slice(0, 8));
        setOpen(true);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const select = (ticker: string) => {
    setQuery("");
    setOpen(false);
    navigate(`/company/${ticker.toUpperCase()}`);
  };

  return (
    <div className="relative" ref={ref}>
      <div className="flex items-center bg-slate-100 rounded-lg px-3 py-2 gap-2">
        <Search className="w-4 h-4 text-slate-400 shrink-0" />
        <input
          className="bg-transparent outline-none flex-1 text-sm placeholder:text-slate-400"
          placeholder="Search company or ticker (e.g. Apple, AAPL)…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
        />
        {query && (
          <button onClick={() => { setQuery(""); setOpen(false); }}>
            <X className="w-4 h-4 text-slate-400 hover:text-slate-600" />
          </button>
        )}
      </div>

      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-50 overflow-hidden">
          {loading ? (
            <div className="p-4 text-sm text-slate-500 text-center">Searching…</div>
          ) : results.length === 0 ? (
            <div className="p-4 text-sm text-slate-500 text-center">No results found</div>
          ) : (
            results.map((r) => (
              <button
                key={r.ticker}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors text-left"
                onClick={() => select(r.ticker)}
              >
                <div className="w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-brand-700">
                    {r.ticker.slice(0, 4)}
                  </span>
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-slate-900 truncate">{r.name || r.ticker}</div>
                  <div className="text-xs text-slate-500">
                    {r.ticker} · {r.exchange}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
