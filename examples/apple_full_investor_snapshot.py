import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any

import pandas as pd
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


import sdu_dst.api.client as api_client

api_client._redis = None


# ============================================================
# 🧱 Helper utilities
# ============================================================


def section(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def safe(series: Optional[pd.Series], key: str):
    if series is None:
        return None
    return series.get(key) if key in series else None


def first_available(*values):
    for v in values:
        if v is not None:
            return v
    return None


def show(label: str, value: Any):
    print(f"{label:<30}: {value if value is not None else 'N/A'}")


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def score_from_ratio(value, good, bad):
    """
    Lineær score:
    - good -> 100
    - bad  -> 0
    """
    if value is None:
        return None
    if good == bad:
        return None
    score = 100 * (bad - value) / (bad - good)
    return clamp(score)


def score_from_positive(value, low, high):
    """
    Højere = bedre
    """
    if value is None:
        return None
    score = 100 * (value - low) / (high - low)
    return clamp(score)


def avg(scores):
    vals = [s for s in scores if s is not None]
    return sum(vals) / len(vals) if vals else None


# ============================================================
# 📦 Metric container (KRITISK)
# ============================================================


@dataclass
class Metric:
    value: Any
    was_calculated: bool = False

    def __str__(self):
        if self.value is None:
            return "N/A"
        flag = " ⚙️ calculated" if self.was_calculated else ""
        return f"{self.value}{flag}"


# ============================================================
# 📊 Investor Snapshot
# ============================================================


@dataclass
class InvestorSnapshot:
    valuation: Dict[str, Metric]
    profitability: Dict[str, Metric]
    balance: Dict[str, Metric]
    cashflow: Dict[str, Metric]
    quality: Dict[str, Metric]

    def display(self):
        for block, metrics in self.__dict__.items():
            section(block.upper())
            for k, m in metrics.items():
                print(f"{k:<35}: {m}")


# ============================================================
# 🚀 Main pipeline
# ============================================================


async def main():
    src = FinancialModelingPrepSource()
    symbol = "AAPL"

    # --------------------------------------------------------
    # Raw data fetch
    # --------------------------------------------------------
    profile_df = await src.fetch_company_profile(symbol)
    quote_df = await src.fetch_market_quote(symbol)
    key_df = await src.fetch_key_metrics(symbol)
    ratios_df = await src.fetch_ratios(symbol)
    income_df = await src.fetch_income_statement(symbol, period="annual", limit=1)

    profile = profile_df.iloc[0] if not profile_df.empty else None
    quote = quote_df.iloc[0] if not quote_df.empty else None
    key = key_df.iloc[0] if not key_df.empty else None
    ratios = ratios_df.iloc[0] if not ratios_df.empty else None
    income = income_df.iloc[0] if not income_df.empty else None

    # --------------------------------------------------------
    # 📈 INVESTOR HEADER (WOW-FEELING)
    # --------------------------------------------------------
    section("📈 INVESTOR SNAPSHOT")

    show("Company", safe(profile, "companyName"))
    show("Ticker", symbol)
    show(
        "Sector",
        (
            f"{safe(profile,'sector')} / {safe(profile,'industry')}"
            if profile is not None
            else None
        ),
    )
    show("Currency", safe(profile, "currency"))

    def to_float(x):
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = x.strip().replace("%", "")
            try:
                return float(s)
            except ValueError:
                return None
        return None

    price = to_float(safe(quote, "price"))
    change = to_float(safe(quote, "change"))
    pct = safe(quote, "changesPercentage")  # kan være "0.49%" eller 0.49
    pct_f = to_float(pct)

    if price is not None:
        if change is not None and pct_f is not None:
            price_line = f"{price:.2f}  ({change:+.2f} | {pct_f:+.2f}%)"
        else:
            price_line = f"{price:.2f}"
        show("Price", price_line)

    show("Market Cap", safe(quote, "marketCap"))
    show(
        "52W Range",
        (
            f"{safe(quote,'yearLow')} – {safe(quote,'yearHigh')}"
            if safe(quote, "yearLow") is not None
            else None
        ),
    )

    # --------------------------------------------------------
    # 💰 Valuation
    # --------------------------------------------------------
    earnings_yield = safe(key, "earningsYieldTTM")

    pe = (
        Metric(1 / earnings_yield, was_calculated=True)
        if earnings_yield
        else Metric(None)
    )

    valuation = {
        "P/E (TTM)": pe,
        "EV / EBITDA": Metric(safe(key, "evToEBITDATTM")),
        "Forward P/E": Metric(safe(ratios, "forwardPE")),
        "PEG Ratio": Metric(safe(ratios, "pegRatioTTM")),
    }

    # --------------------------------------------------------
    # 📊 Profitability
    # --------------------------------------------------------
    profitability = {
        "Gross Margin": Metric(safe(ratios, "grossProfitMarginTTM")),
        "Operating Margin": Metric(safe(ratios, "operatingProfitMarginTTM")),
        "Net Margin": Metric(safe(ratios, "netProfitMarginTTM")),
        "ROE": Metric(safe(key, "returnOnEquityTTM")),
        "ROIC": Metric(safe(key, "returnOnInvestedCapitalTTM")),
    }

    # --------------------------------------------------------
    # 🧾 Balance & Debt
    # --------------------------------------------------------
    balance = {
        "Current Ratio": Metric(safe(key, "currentRatioTTM")),
        "Net Debt / EBITDA": Metric(safe(key, "netDebtToEBITDATTM")),
        "Shares Outstanding": Metric(
            first_available(
                safe(quote, "sharesOutstanding"),
                safe(profile, "sharesOutstanding"),
                safe(key, "sharesOutstanding"),
            )
        ),
    }

    # --------------------------------------------------------
    # 💸 Cash Flow
    # --------------------------------------------------------
    cashflow = {
        "Free Cash Flow (Firm)": Metric(safe(key, "freeCashFlowToFirmTTM")),
        "Free Cash Flow Yield": Metric(safe(key, "freeCashFlowYieldTTM")),
        "Dividend Yield": Metric(safe(ratios, "dividendYieldTTM")),
        "Dividend Payout Ratio": Metric(safe(ratios, "payoutRatioTTM")),
    }

    # --------------------------------------------------------
    # 🧠 Quality / Strategic signals
    # --------------------------------------------------------
    rd = safe(income, "researchAndDevelopmentExpenses")
    revenue = safe(income, "revenue")

    rd_intensity = (
        Metric(rd / revenue, was_calculated=True)
        if rd is not None and revenue
        else Metric(None)
    )

    quality = {
        "R&D Intensity": rd_intensity,
        "Stock-based Comp / Revenue": Metric(
            safe(key, "stockBasedCompensationToRevenueTTM")
        ),
        "Capital Efficiency (ROIC)": Metric(safe(key, "returnOnInvestedCapitalTTM")),
    }

    # ============================================================
    # 🧮 FACTOR SCORES (0–100)
    # ============================================================

    section("FACTOR SCORES")

    value_score = avg(
        [
            score_from_ratio(
                1 / earnings_yield if earnings_yield else None, good=10, bad=40
            ),  # P/E
            score_from_ratio(safe(key, "evToEBITDATTM"), good=8, bad=30),
            score_from_positive(safe(key, "freeCashFlowYieldTTM"), low=0.01, high=0.08),
        ]
    )

    profitability_score = avg(
        [
            score_from_positive(safe(ratios, "grossProfitMarginTTM"), 0.2, 0.6),
            score_from_positive(safe(ratios, "operatingProfitMarginTTM"), 0.1, 0.4),
            score_from_positive(safe(ratios, "netProfitMarginTTM"), 0.05, 0.3),
            score_from_positive(safe(key, "returnOnEquityTTM"), 0.1, 0.5),
        ]
    )

    quality_score = avg(
        [
            score_from_positive(safe(key, "returnOnInvestedCapitalTTM"), 0.1, 0.4),
            score_from_ratio(
                safe(key, "stockBasedCompensationToRevenueTTM"), good=0.0, bad=0.1
            ),
            score_from_positive(
                rd_intensity.value if rd_intensity else None, 0.02, 0.15
            ),
        ]
    )

    capital_efficiency_score = avg(
        [
            score_from_positive(safe(key, "returnOnInvestedCapitalTTM"), 0.1, 0.4),
            score_from_ratio(safe(key, "netDebtToEBITDATTM"), good=0.0, bad=3.0),
            score_from_positive(safe(key, "currentRatioTTM"), 1.0, 3.0),
        ]
    )

    factor_scores = {
        "Value Score": Metric(
            f"{value_score:.0f} / 100" if value_score else None, True
        ),
        "Profitability Score": Metric(
            f"{profitability_score:.0f} / 100" if profitability_score else None, True
        ),
        "Quality Score": Metric(
            f"{quality_score:.0f} / 100" if quality_score else None, True
        ),
        "Capital Efficiency Score": Metric(
            (
                f"{capital_efficiency_score:.0f} / 100"
                if capital_efficiency_score
                else None
            ),
            True,
        ),
    }

    for k, v in factor_scores.items():
        print(f"{k:<35}: {v}")

    # --------------------------------------------------------
    # 📦 Snapshot display
    # --------------------------------------------------------
    snapshot = InvestorSnapshot(
        valuation=valuation,
        profitability=profitability,
        balance=balance,
        cashflow=cashflow,
        quality=quality,
    )

    snapshot.display()

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
