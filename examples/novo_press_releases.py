import asyncio
import pandas as pd

from sdu_dst.sources.stocknewsapi import StockNewsAPISource


async def main():
    src = StockNewsAPISource()

    # 1️⃣ Hent seneste nyheder for Novo Nordisk
    df = await src.fetch_stock_news(
        symbols=["NVO"],
        limit=100,  # tag lidt ekstra for at få hele december
    )

    await src.close()

    if df.empty:
        print("Ingen data modtaget.")
        return

    # 2️⃣ Filtrér lokalt på periode (december 2025)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)

    start = pd.Timestamp("2025-12-01", tz="UTC")
    end = pd.Timestamp("2025-12-31 23:59:59", tz="UTC")

    df_december = df[(df["ts"] >= start) & (df["ts"] <= end)]

    if df_december.empty:
        print("Ingen nyheder i december 2025.")
        return

    # 3️⃣ Optæl typer
    counts = df_december["type"].value_counts()

    print("\n📊 Novo Nordisk – December 2025")
    print("--------------------------------")
    print(f"Totalt antal events: {len(df_december)}\n")

    for k, v in counts.items():
        print(f"{k}: {v}")

    # 4️⃣ Vis press releases (hvis nogen)
    prs = df_december[df_december["type"] == "press_release"]

    if not prs.empty:
        print("\n📣 Press releases:\n")
        print(
            prs[
                [
                    "ts",
                    "headline",
                    "publisher",
                    "url",
                ]
            ].to_string(index=False)
        )
    else:
        print("\n📣 Ingen press releases fundet i perioden.")

    # 5️⃣ (valgfrit) Gem til CSV
    # df_december.to_csv("novo_december_2025_events.csv", index=False)


if __name__ == "__main__":
    asyncio.run(main())
