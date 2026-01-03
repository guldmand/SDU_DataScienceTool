import asyncio
import pandas as pd
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


async def main():
    # 🔧 Pandas display settings – så ALT vises
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", None)

    src = FinancialModelingPrepSource()

    df = await src.fetch_key_metrics("AAPL")

    print("\n📊 Full Key Metrics DataFrame:\n")
    print(df)

    print("\n🧾 Column names:\n")
    print(df.columns.tolist())

    # (valgfrit) gem til CSV for fuldt overblik
    df.to_csv("fmp_key_metrics_AAPL.csv", index=False)
    print("\n💾 Saved to fmp_key_metrics_AAPL.csv")

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
