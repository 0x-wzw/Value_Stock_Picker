import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  BarChart2,
  Search,
  Star,
  TrendingUp,
  BookOpen,
  Menu,
  X,
  Home,
  ChevronRight,
} from "lucide-react";
import clsx from "clsx";
import SearchBar from "./SearchBar";

const NAV = [
  {
    to: "/",
    icon: Home,
    label: "Home",
    description: "Market overview",
  },
  {
    to: "/screener",
    icon: Search,
    label: "Find Stocks",
    description: "Screen & filter",
  },
  {
    to: "/watchlist",
    icon: Star,
    label: "Watchlist",
    description: "Your saved stocks",
  },
  {
    to: "/portfolio",
    icon: TrendingUp,
    label: "Portfolio",
    description: "Track holdings",
  },
  {
    to: "/learn",
    icon: BookOpen,
    label: "Learn",
    description: "Value investing guide",
  },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar — desktop */}
      <aside className="hidden md:flex flex-col w-60 bg-white border-r border-slate-200 shrink-0">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <BarChart2 className="w-6 h-6 text-brand-600 mr-2" />
          <span className="font-bold text-slate-900 text-lg">ValuePicker</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {NAV.map((item) => {
            const active = location.pathname === item.to ||
              (item.to !== "/" && location.pathname.startsWith(item.to));
            return (
              <Link
                key={item.to}
                to={item.to}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group",
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )}
              >
                <item.icon
                  className={clsx(
                    "w-5 h-5 shrink-0",
                    active ? "text-brand-600" : "text-slate-400 group-hover:text-slate-600"
                  )}
                />
                <div className="min-w-0">
                  <div className="text-sm font-medium">{item.label}</div>
                  <div className="text-xs text-slate-400">{item.description}</div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Tip card */}
        <div className="m-4 p-4 bg-brand-50 rounded-xl border border-brand-100">
          <p className="text-xs font-medium text-brand-800 mb-1">Li Lu's Rule #1</p>
          <p className="text-xs text-brand-700 leading-relaxed">
            "Only invest in businesses you genuinely understand."
          </p>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative w-64 bg-white flex flex-col h-full shadow-xl">
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-brand-600" />
                <span className="font-bold text-slate-900">ValuePicker</span>
              </div>
              <button onClick={() => setMobileOpen(false)}>
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            <nav className="flex-1 py-4 px-3 space-y-1">
              {NAV.map((item) => {
                const active = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileOpen(false)}
                    className={clsx(
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                      active ? "bg-brand-50 text-brand-700" : "text-slate-600"
                    )}
                  >
                    <item.icon className="w-5 h-5 shrink-0" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center gap-4 px-4 md:px-6 shrink-0">
          <button
            className="md:hidden p-1.5 text-slate-500 hover:text-slate-900"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1 max-w-xl">
            <SearchBar />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
