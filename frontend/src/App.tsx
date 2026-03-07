import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppShell from "./components/Layout/AppShell";
import Home from "./pages/Home";
import Screener from "./pages/Screener";
import CompanyDashboard from "./pages/CompanyDashboard";
import FinancialsPage from "./pages/FinancialsPage";
import ValuationPage from "./pages/ValuationPage";
import Watchlist from "./pages/Watchlist";
import Portfolio from "./pages/Portfolio";
import LearnPage from "./pages/LearnPage";

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/screener" element={<Screener />} />
          <Route path="/company/:ticker" element={<CompanyDashboard />} />
          <Route path="/company/:ticker/financials" element={<FinancialsPage />} />
          <Route path="/company/:ticker/valuation" element={<ValuationPage />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/learn" element={<LearnPage />} />
          <Route path="*" element={
            <div className="text-center py-20">
              <p className="text-2xl font-bold text-slate-400">404</p>
              <p className="text-slate-500 mt-2">Page not found</p>
            </div>
          } />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
