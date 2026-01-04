import asyncio
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------


def section(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def score_block(name, scores):
    print(f"\n[{name}]")
    for k, v in scores.items():
        print(f"{k:<30}: {v:>3} / 100")

    total = sum(scores.values()) / len(scores)
    print(f"{'TOTAL SCORE':<30}: {round(total, 1):>6}")
    return total


# ------------------------------------------------------------
# Factor scoring logic (samme idé som før)
# ------------------------------------------------------------


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def value_score(pe, ev_ebitda):
    score = 100
    if pe:
        score -= pe * 1.2
    if ev_ebitda:
        score -= ev_ebitda * 1.5
    return clamp(score)


def profitability_score(roe, net_margin):
    score = 0
    if roe:
        score += roe * 40
    if net_margin:
        score += net_margin * 200
    return clamp(score)


def quality_score(roic, rd_intensity):
    score = 0
    if roic:
        score += roic * 50
    if rd_intensity:
        score += rd_intensity * 400
    return clamp(score)


def capital_efficiency_score(roic, current_ratio):
    score = 0
    if roic:
        score += roic * 60
    if current_ratio:
        score += min(current_ratio, 2) * 20
    return clamp(score)


# ------------------------------------------------------------
# Main comparison
# ------------------------------------------------------------


async def snapshot_scores(src, symbol):
    quote = (await src.fetch_market_quote(symbol)).iloc[0]
    key = (await src.fetch_key_metrics(symbol)).iloc[0]
    ratios = (await src.fetch_ratios(symbol)).iloc[0]
    income = (await src.fetch_income_statement(symbol, period="annual", limit=1)).iloc[
        0
    ]

    rd = income.get("researchAndDevelopmentExpenses")
    revenue = income.get("revenue")
    rd_intensity = rd / revenue if rd and revenue else None

    scores = {
        "Value Score": value_score(
            pe=1 / key["earningsYieldTTM"] if key.get("earningsYieldTTM") else None,
            ev_ebitda=key.get("evToEBITDATTM"),
        ),
        "Profitability Score": profitability_score(
            roe=key.get("returnOnEquityTTM"),
            net_margin=ratios.get("netProfitMarginTTM"),
        ),
        "Quality Score": quality_score(
            roic=key.get("returnOnInvestedCapitalTTM"),
            rd_intensity=rd_intensity,
        ),
        "Capital Efficiency Score": capital_efficiency_score(
            roic=key.get("returnOnInvestedCapitalTTM"),
            current_ratio=key.get("currentRatioTTM"),
        ),
    }

    return scores


async def main():
    src = FinancialModelingPrepSource()

    stock_a = "AAPL"
    stock_b = "MSFT"

    section("📊 STOCK COMPARISON")

    scores_a = await snapshot_scores(src, stock_a)
    total_a = score_block(stock_a, scores_a)

    scores_b = await snapshot_scores(src, stock_b)
    total_b = score_block(stock_b, scores_b)

    section("🏆 RECOMMENDATION")

    if total_a > total_b:
        print(f"✅ Recommend {stock_a}")
    elif total_b > total_a:
        print(f"✅ Recommend {stock_b}")
    else:
        print("🤝 Stocks are equally attractive")

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
