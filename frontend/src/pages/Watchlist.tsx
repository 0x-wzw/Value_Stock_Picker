import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Star, Trash2, Plus, TrendingUp, TrendingDown } from "lucide-react";
import { getQuote } from "../api/companies";
import { formatPrice, formatPct } from "../utils/format";
import clsx from "clsx";
import SearchBar from "../components/Layout/SearchBar";

interface WatchItem {
  ticker: string;
  note: string;
  addedAt: string;
}

interface LiveData {
  price?: number;
  change_pct?: number;
  market_cap?: number;
}

const STORAGE_KEY = "vsp_watchlist";

function loadWatchlist(): WatchItem[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveWatchlist(items: WatchItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export default function Watchlist() {
  const [items, setItems] = useState<WatchItem[]>(loadWatchlist);
  const [liveData, setLiveData] = useState<Record<string, LiveData>>({});
  const [adding, setAdding] = useState(false);
  const [newTicker, setNewTicker] = useState("");
  const [newNote, setNewNote] = useState("");

  useEffect(() => {
    if (!items.length) return;
    items.forEach(async (item) => {
      try {
        const q = await getQuote(item.ticker);
        setLiveData((prev) => ({ ...prev, [item.ticker]: q }));
      } catch {
        // ignore
      }
    });
  }, [items.length]);

  const add = () => {
    const t = newTicker.trim().toUpperCase();
    if (!t || items.some((i) => i.ticker === t)) return;
    const updated = [
      ...items,
      { ticker: t, note: newNote.trim(), addedAt: new Date().toISOString() },
    ];
    setItems(updated);
    saveWatchlist(updated);
    setNewTicker("");
    setNewNote("");
    setAdding(false);
  };

  const remove = (ticker: string) => {
    const updated = items.filter((i) => i.ticker !== ticker);
    setItems(updated);
    saveWatchlist(updated);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Star className="w-6 h-6 text-amber-400 fill-amber-400" />
            Watchlist
          </h1>
          <p className="text-slate-500 text-sm mt-1">Save companies you want to research further</p>
        </div>
        <button
          onClick={() => setAdding(true)}
          className="btn-primary flex items-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Stock
        </button>
      </div>

      {/* Add form */}
      {adding && (
        <div className="card">
          <h3 className="font-semibold text-slate-900 mb-4">Add to Watchlist</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Ticker Symbol</label>
              <input
                autoFocus
                placeholder="e.g. AAPL"
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === "Enter" && add()}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Note <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <textarea
                placeholder="Why are you watching this? What do you want to research?"
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                rows={2}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none"
              />
            </div>
            <div className="flex gap-2">
              <button className="btn-primary text-sm" onClick={add}>Add</button>
              <button className="btn-secondary text-sm" onClick={() => { setAdding(false); setNewTicker(""); setNewNote(""); }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {items.length === 0 ? (
        <div className="card text-center py-16">
          <Star className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">Your watchlist is empty</p>
          <p className="text-slate-400 text-sm mt-1">
            Add companies you're researching to track them here
          </p>
          <button
            className="btn-primary text-sm mt-4"
            onClick={() => setAdding(true)}
          >
            Add your first stock
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const live = liveData[item.ticker];
            const up = (live?.change_pct ?? 0) >= 0;
            return (
              <div key={item.ticker} className="card flex items-center gap-4">
                {/* Ticker logo */}
                <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-brand-700">{item.ticker.slice(0, 4)}</span>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/company/${item.ticker}`}
                      className="font-semibold text-slate-900 hover:text-brand-600 transition-colors"
                    >
                      {item.ticker}
                    </Link>
                    {live?.price != null && (
                      <div className="flex items-center gap-1">
                        <span className="font-medium text-slate-700">{formatPrice(live.price)}</span>
                        <span className={clsx("flex items-center gap-0.5 text-xs font-semibold",
                          up ? "text-emerald-600" : "text-red-600")}>
                          {up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {formatPct(live.change_pct)}
                        </span>
                      </div>
                    )}
                  </div>
                  {item.note && (
                    <p className="text-sm text-slate-500 truncate mt-0.5">{item.note}</p>
                  )}
                  <p className="text-xs text-slate-400 mt-0.5">Added {item.addedAt.slice(0, 10)}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    to={`/company/${item.ticker}`}
                    className="btn-secondary text-xs !py-1.5"
                  >
                    Research
                  </Link>
                  <button
                    onClick={() => remove(item.ticker)}
                    className="p-1.5 text-slate-400 hover:text-red-500 transition-colors"
                    title="Remove from watchlist"
                  >
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
