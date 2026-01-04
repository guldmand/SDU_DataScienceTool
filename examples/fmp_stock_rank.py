import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Tuple

import pandas as pd
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


# ============================================================
# Output helpers
# ============================================================


def section(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def safe(series: Optional[pd.Series], key: str):
    if series is None:
        return None
    return series.get(key) if key in series else None


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


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def fmt_num(x, digits=2):
    if x is None:
        return "N/A"
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return str(x)


def fmt_pct(x, digits=2):
    if x is None:
        return "N/A"
    try:
        return f"{float(x)*100:.{digits}f}%"
    except Exception:
        return str(x)


# ============================================================
# Factor scoring (simple & explainable)
# ============================================================


def value_score(pe: Optional[float], ev_ebitda: Optional[float]) -> int:
    """
    Lower P/E and lower EV/EBITDA => higher value score.
    Conservative when missing (penalize).
    """
    score = 100

    if pe is None:
        score -= 25
    else:
        score -= pe * 1.2

    if ev_ebitda is None:
        score -= 25
    else:
        score -= ev_ebitda * 1.5

    return int(round(clamp(score)))


def profitability_score(roe: Optional[float], net_margin: Optional[float]) -> int:
    """
    Higher ROE and higher net margin => higher score.
    Conservative when missing.
    """
    score = 0

    if roe is None:
        score += 10
    else:
        score += roe * 40  # ROE is often 0-1 range, sometimes >1

    if net_margin is None:
        score += 10
    else:
        score += net_margin * 200  # net margin is 0-0.3 typical

    return int(round(clamp(score)))


def quality_score(roic: Optional[float], rd_intensity: Optional[float]) -> int:
    """
    Higher ROIC and higher R&D intensity (proxy for reinvestment) => higher score.
    Conservative when missing.
    """
    score = 0

    if roic is None:
        score += 10
    else:
        score += roic * 50  # ROIC typical 0-0.3+, sometimes higher

    if rd_intensity is None:
        score += 10
    else:
        score += rd_intensity * 400  # RD/rev typical 0-0.2

    return int(round(clamp(score)))


def capital_efficiency_score(
    roic: Optional[float], current_ratio: Optional[float]
) -> int:
    """
    ROIC + liquidity proxy. Clamp current ratio influence.
    Conservative when missing.
    """
    score = 0

    if roic is None:
        score += 10
    else:
        score += roic * 60

    if current_ratio is None:
        score += 10
    else:
        score += min(current_ratio, 2.0) * 20

    return int(round(clamp(score)))


# ============================================================
# Data model
# ============================================================


@dataclass
class RankedStock:
    symbol: str
    company: str
    price: Optional[float]
    change: Optional[float]
    change_pct: Optional[float]
    market_cap: Optional[float]

    pe_ttm: Optional[float]
    ev_ebitda: Optional[float]
    roe: Optional[float]
    roic: Optional[float]
    net_margin: Optional[float]
    current_ratio: Optional[float]
    rd_intensity: Optional[float]

    scores: Dict[str, int]
    total_score: float


# ============================================================
# Snapshot builder
# ============================================================


async def build_ranked_stock(
    src: FinancialModelingPrepSource, symbol: str
) -> RankedStock:
    # Fetch each endpoint; if one fails, keep going.
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

    company = safe(profile, "companyName") or safe(profile, "name") or symbol

    price = to_float(safe(quote, "price"))
    change = to_float(safe(quote, "change"))
    change_pct = to_float(safe(quote, "changesPercentage"))  # may be 0.49 or "0.49%"
    market_cap = to_float(safe(quote, "marketCap"))

    earnings_yield = to_float(safe(key, "earningsYieldTTM"))
    pe_ttm = (1.0 / earnings_yield) if earnings_yield else None

    ev_ebitda = to_float(safe(key, "evToEBITDATTM"))
    roe = to_float(safe(key, "returnOnEquityTTM"))
    roic = to_float(safe(key, "returnOnInvestedCapitalTTM"))
    current_ratio = to_float(safe(key, "currentRatioTTM"))

    net_margin = to_float(safe(ratios, "netProfitMarginTTM"))

    rd = to_float(safe(income, "researchAndDevelopmentExpenses"))
    revenue = to_float(safe(income, "revenue"))
    rd_intensity = (rd / revenue) if (rd is not None and revenue) else None

    scores = {
        "Value": value_score(pe_ttm, ev_ebitda),
        "Profitability": profitability_score(roe, net_margin),
        "Quality": quality_score(roic, rd_intensity),
        "CapitalEff": capital_efficiency_score(roic, current_ratio),
    }
    total_score = sum(scores.values()) / len(scores)

    return RankedStock(
        symbol=symbol,
        company=company,
        price=price,
        change=change,
        change_pct=change_pct,
        market_cap=market_cap,
        pe_ttm=pe_ttm,
        ev_ebitda=ev_ebitda,
        roe=roe,
        roic=roic,
        net_margin=net_margin,
        current_ratio=current_ratio,
        rd_intensity=rd_intensity,
        scores=scores,
        total_score=total_score,
    )


# ============================================================
# Main
# ============================================================


async def main():
    src = FinancialModelingPrepSource()

    # 👇 Redigér listen som du vil (keep it simple)
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]

    section("📈 STOCK RANKING (Investor Factors)")

    ranked: List[RankedStock] = []
    for t in tickers:
        try:
            ranked.append(await build_ranked_stock(src, t))
        except Exception as e:
            # fail-safe: never crash the ranker because one ticker failed
            print(f"⚠️ Skipped {t} (error: {e})")

    ranked.sort(key=lambda x: x.total_score, reverse=True)

    # Print table
    header = (
        f"{'Rank':<5} {'Ticker':<7} {'Company':<22} "
        f"{'Price':>10} {'Chg':>10} {'MCap':>14} "
        f"{'Value':>7} {'Prof':>7} {'Qual':>7} {'CapEff':>7} {'Total':>8}"
    )
    print(header)
    print("-" * len(header))

    for i, s in enumerate(ranked, start=1):
        chg_str = "N/A"
        if s.change is not None and s.change_pct is not None:
            chg_str = f"{s.change:+.2f} | {s.change_pct:+.2f}%"
        elif s.change is not None:
            chg_str = f"{s.change:+.2f}"
        elif s.change_pct is not None:
            chg_str = f"{s.change_pct:+.2f}%"

        print(
            f"{i:<5} {s.symbol:<7} {s.company[:22]:<22} "
            f"{fmt_num(s.price,2):>10} {chg_str:>10} {fmt_num(s.market_cap,0):>14} "
            f"{s.scores['Value']:>7} {s.scores['Profitability']:>7} {s.scores['Quality']:>7} {s.scores['CapitalEff']:>7} "
            f"{s.total_score:>8.1f}"
        )

    # Top pick explanation
    if ranked:
        top = ranked[0]
        section("🏆 TOP PICK (Conceptual)")
        print(f"✅ {top.symbol} — {top.company}")
        print(f"Total score: {top.total_score:.1f} / 100")
        print("Breakdown:")
        for k, v in top.scores.items():
            print(f"  - {k:<12}: {v} / 100")

        # Optional: show a few core metrics for context
        print("\nKey figures:")
        print(f"  - P/E (TTM): {fmt_num(top.pe_ttm,2)}")
        print(f"  - EV/EBITDA: {fmt_num(top.ev_ebitda,2)}")
        print(f"  - ROE:       {fmt_num(top.roe,3)}")
        print(f"  - ROIC:      {fmt_num(top.roic,3)}")
        print(f"  - Net margin:{fmt_pct(top.net_margin,2)}")
        print(f"  - R&D int.:  {fmt_pct(top.rd_intensity,2)}")
    else:
        print("No results to rank.")

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
