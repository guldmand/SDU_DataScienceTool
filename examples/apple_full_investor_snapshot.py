import asyncio
import pandas as pd
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


def section(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def show(label, value):
    print(f"{label:<35}: {value if value is not None else 'N/A'}")


def safe(series: pd.Series, key: str):
    return series.get(key) if key in series else None


async def main():
    src = FinancialModelingPrepSource()
    symbol = "AAPL"

    # --------------------------------------------------
    # 🏢 Market & Company Profile
    # --------------------------------------------------
    section("🏢 Market & Company Profile")

    profile_df = await src.fetch_company_profile(symbol)
    quote_df = await src.fetch_market_quote(symbol)

    if profile_df.empty or quote_df.empty:
        print("No market/profile data available")
        return

    profile = profile_df.iloc[0]
    quote = quote_df.iloc[0]

    show("Price", safe(quote, "price"))
    show("Market Cap", safe(quote, "marketCap"))
    show("Beta", safe(quote, "beta"))
    show("Shares Outstanding", safe(quote, "sharesOutstanding"))
    show(
        "52W Range",
        (
            f"{safe(quote,'yearLow')} – {safe(quote,'yearHigh')}"
            if safe(quote, "yearLow") is not None
            else None
        ),
    )
    show("Sector", safe(profile, "sector"))
    show("Industry", safe(profile, "industry"))
    show("Currency", safe(profile, "currency"))

    # --------------------------------------------------
    # 📊 Key Metrics (TTM)
    # --------------------------------------------------
    section("📊 Key Metrics (TTM)")

    key_df = await src.fetch_key_metrics(symbol)
    if not key_df.empty:
        key = key_df.iloc[0]

        show(
            "P/E (TTM)",
            (
                1 / safe(key, "earningsYieldTTM")
                if safe(key, "earningsYieldTTM")
                else None
            ),
        )
        show("Earnings Yield", safe(key, "earningsYieldTTM"))
        show("EV / EBITDA", safe(key, "evToEBITDATTM"))
        show("ROE", safe(key, "returnOnEquityTTM"))
        show("ROIC", safe(key, "returnOnInvestedCapitalTTM"))
        show("Net Debt / EBITDA", safe(key, "netDebtToEBITDATTM"))
        show("Current Ratio", safe(key, "currentRatioTTM"))
        show("Free Cash Flow (Firm)", safe(key, "freeCashFlowToFirmTTM"))
        show("Free Cash Flow Yield", safe(key, "freeCashFlowYieldTTM"))

    # --------------------------------------------------
    # 📈 Ratios (TTM)
    # --------------------------------------------------
    section("📈 Valuation & Profitability Ratios")

    ratios_df = await src.fetch_ratios(symbol)
    if not ratios_df.empty:
        ratios = ratios_df.iloc[0]

        show("Forward P/E", safe(ratios, "forwardPE"))
        show("PEG Ratio", safe(ratios, "pegRatioTTM"))
        show("Gross Margin", safe(ratios, "grossProfitMarginTTM"))
        show("Operating Margin", safe(ratios, "operatingProfitMarginTTM"))
        show("Net Margin", safe(ratios, "netProfitMarginTTM"))
        show("Dividend Yield", safe(ratios, "dividendYieldTTM"))
        show("Dividend Payout Ratio", safe(ratios, "payoutRatioTTM"))

    # --------------------------------------------------
    # 📄 Income Statement (Annual)
    # --------------------------------------------------
    section("📄 Income Statement (Latest Annual)")

    income_df = await src.fetch_income_statement(symbol, period="annual", limit=1)
    if not income_df.empty:
        income = income_df.iloc[0]

        show("Revenue", safe(income, "revenue"))
        show("EBITDA", safe(income, "ebitda"))
        show("Operating Income", safe(income, "operatingIncome"))
        show("Net Income", safe(income, "netIncome"))
        show("EPS", safe(income, "eps"))

    # --------------------------------------------------
    # 🧠 Strategic / Quality Proxies
    # --------------------------------------------------
    section("🧠 Strategic / Quality Signals")

    rd = safe(income, "researchAndDevelopmentExpenses") if not income_df.empty else None
    revenue = safe(income, "revenue") if not income_df.empty else None

    show(
        "R&D Intensity",
        rd / revenue if rd is not None and revenue else None,
    )
    show(
        "Stock-based Comp / Revenue",
        safe(key, "stockBasedCompensationToRevenueTTM") if "key" in locals() else None,
    )
    show(
        "Capital Efficiency (ROIC)",
        safe(key, "returnOnInvestedCapitalTTM") if "key" in locals() else None,
    )

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
