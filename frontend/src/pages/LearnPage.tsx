import React, { useState } from "react";
import { BookOpen, ChevronDown, ChevronRight, CheckCircle } from "lucide-react";
import clsx from "clsx";

const LESSONS = [
  {
    title: "What is Value Investing?",
    icon: "🏛️",
    summary: "Understanding the core idea: buy $1 worth of value for $0.50.",
    content: `Value investing means buying shares in businesses that are worth more than you paid for them.

The idea, popularized by Benjamin Graham and Warren Buffett, is simple: the stock market is not always rational. Prices fluctuate wildly, but a business's underlying value changes slowly. When prices fall below value, you have an opportunity.

Key insight: You are buying a piece of a real business, not a lottery ticket. Think like a business owner, not a speculator.

Li Lu, a prominent value investor, extends this: only invest in businesses you genuinely understand, that have durable competitive advantages, and are run by honest management.`,
  },
  {
    title: "The Margin of Safety",
    icon: "🛡️",
    summary: "Why paying less than something is worth protects you.",
    content: `Margin of safety is the gap between what you pay and what you believe something is worth.

If a business is worth $100/share but you pay $70, you have a 30% margin of safety. This protects you if:
• Your estimate of value was too optimistic
• Something unexpected happens to the business
• It takes longer than expected to recover

Think of it like buying a house: you wouldn't pay $500,000 for a house you think is worth $500,000. You'd want to pay $400,000 or less to protect yourself.

In ValuePicker, the Valuation Calculator shows you this margin of safety automatically.`,
  },
  {
    title: "Competitive Moat",
    icon: "🏰",
    summary: "Why some businesses are naturally protected from competition.",
    content: `A "moat" is Warren Buffett's term for a sustainable competitive advantage — something that prevents competitors from copying your business or stealing your customers.

Types of moats:
• **Network effects**: More users = more valuable (Visa, Facebook)
• **Switching costs**: Painful to change suppliers (enterprise software)
• **Cost advantages**: Can produce cheaper than anyone else (Costco, Amazon)
• **Brand/intangibles**: Customers pay a premium for the name (Apple, Coca-Cola)
• **Efficient scale**: Natural monopoly in a limited market (local utilities)

How to spot a moat: Look for high and consistent gross margins (>40%), high return on invested capital (>15%), and pricing power over time.

In ValuePicker, the "Moat Score" in the screener gives you a quick signal.`,
  },
  {
    title: "Reading Financial Statements",
    icon: "📊",
    summary: "The 3 reports every investor should understand.",
    content: `Three key financial reports tell the story of any business:

**1. Income Statement** — Did the business make money?
• Revenue: Sales to customers
• Gross Profit: Revenue minus cost of goods sold
• Net Income: What's left after all expenses

**2. Balance Sheet** — What does the business own and owe?
• Assets: Cash, equipment, patents, inventory
• Liabilities: Debt, bills to pay
• Equity: What shareholders own (Assets - Liabilities)

**3. Cash Flow Statement** — Did actual cash come in?
• Operating Cash Flow: Cash from running the business
• Free Cash Flow: Operating CF minus investment in equipment
• This is the most important number for value investing

Key ratio to remember: Free Cash Flow Yield = FCF / Market Cap. Higher = potentially cheaper.`,
  },
  {
    title: "The Li Lu Checklist",
    icon: "✅",
    summary: "8 questions to ask before investing in any company.",
    content: `Li Lu's framework for evaluating investments asks 8 key questions, each scored 1-5:

1. **Owner Economics**: Does the business generate durable free cash flow?
2. **Competitive Moat**: Is the advantage long-lasting?
3. **Management Integrity**: Are leaders honest and shareholder-focused?
4. **Financial Strength**: Is the balance sheet healthy with low debt?
5. **Margin of Safety**: Is the price well below intrinsic value?
6. **Circle of Competence**: Do I truly understand this business?
7. **Long-term Compounding**: Can it compound value for 10+ years?
8. **Downside Protection**: What's the worst case? Can I accept that loss?

A score ≥ 4.0 out of 5 on all criteria suggests a strong candidate for a concentrated investment.

The most important rule: Never invest in what you don't understand.`,
  },
  {
    title: "How to Use ValuePicker",
    icon: "🗺️",
    summary: "A step-by-step guide to your research workflow.",
    content: `Here's the recommended research workflow:

**Step 1: Find Candidates (Screener)**
Start in "Find Stocks" with a preset like "Quality Compounders". This filters to businesses with high returns on capital and low debt — the foundation of great businesses.

**Step 2: Investigate (Company Dashboard)**
Click a company. Read the business description. Does it make sense to you? Do you understand how it makes money?

**Step 3: Check the Numbers (Financials)**
Is revenue growing? Is free cash flow growing? Is debt increasing or stable? Look for consistent trends.

**Step 4: Estimate Value (Valuation)**
Run the DCF calculator with conservative assumptions. Does the current price offer a margin of safety?

**Step 5: Look at SEC Filings**
Read the annual report (10-K). Management's "Letter to Shareholders" is often revealing.

**Step 6: Save & Track (Watchlist)**
Add the company to your watchlist. Watch it for 6-12 months. Does the business perform as expected?

Remember: Patience is a competitive advantage. You don't have to invest today.`,
  },
];

export default function LearnPage() {
  const [open, setOpen] = useState<number | null>(0);
  const [completed, setCompleted] = useState<Set<number>>(new Set());

  const toggle = (i: number) => {
    setOpen(open === i ? null : i);
    if (!completed.has(i)) {
      setCompleted((prev) => new Set(prev).add(i));
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-brand-600" />
          Value Investing Guide
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Everything you need to start investing like a value investor — no finance background required.
        </p>
      </div>

      {/* Progress */}
      <div className="card !p-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-slate-700">Your Progress</p>
          <p className="text-sm text-brand-600 font-semibold">
            {completed.size} / {LESSONS.length} completed
          </p>
        </div>
        <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all"
            style={{ width: `${(completed.size / LESSONS.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Lessons */}
      <div className="space-y-3">
        {LESSONS.map((lesson, i) => (
          <div
            key={i}
            className={clsx(
              "card !p-0 overflow-hidden transition-all",
              open === i && "ring-2 ring-brand-300"
            )}
          >
            <button
              className="w-full flex items-center gap-4 p-5 text-left hover:bg-slate-50 transition-colors"
              onClick={() => toggle(i)}
            >
              <span className="text-2xl">{lesson.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-900">{lesson.title}</p>
                <p className="text-sm text-slate-500">{lesson.summary}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {completed.has(i) && (
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                )}
                {open === i ? (
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-slate-400" />
                )}
              </div>
            </button>

            {open === i && (
              <div className="px-5 pb-5 border-t border-slate-100">
                <div className="pt-4 text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                  {lesson.content}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
