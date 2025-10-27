
# SDU Data Science Tool (sdu-dst)

Async HTTP client, WebSocket streaming, Redis cache, and pluggable data sources
for financial data, news events, and real-time analytics.

Built for:

- Data science experiments
- Visualization dashboards
- Event-driven analysis
- Academic research and teaching
- Real-time streaming experiments

> Academic, research, and educational use is explicitly permitted.
> Commercial use requires a separate commercial license agreement.
>
> See LICENSE and ACADEMIC_USE.md for details.

---

## ✨ Features

- ✅ Async REST API client
  - HTTP/2 multiplexing
  - Retry with exponential backoff
  - Rate limiting
  - TTL caching (Redis or in-memory)

- ✅ WebSocket streaming
  - Auto-reconnect
  - Configurable heartbeat interval

- ✅ Pluggable data Sources
  - YahooFinance (historical OHLCV)
  - GDELT (global news events)
  - (More coming)

- ✅ UTC-first timestamp handling

- ✅ Works with both venv and conda

- ✅ Modular OOP architecture

- ✅ Academic-friendly licensing

---

## 📦 Installation

### Install directly via Git

```bash
pip install git+https://github.com/guldmand/SDU_DataScienceTool.git
```

---

## 🧪 Development Install (Recommended)

Clone the repository:

```bash
git clone https://github.com/guldmand/SDU_DataScienceTool.git
cd SDU_DataScienceTool
```

Install in editable mode:

```bash
pip install -e ".[dev]"
```

---

## 🐍 Virtual Environments

This project supports both venv and conda.

### Option A — venv

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Option B — conda

```bash
conda create -n sdu-dst python=3.11
conda activate sdu-dst
pip install -e ".[dev]"
```

Both options are fully compatible.

---

## ✅ Quick verification

### Fetch price history (Yahoo)

```bash
python examples/fetch_prices_and_events.py
```

### Fetch news events (GDELT)

```bash
python examples/test_events.py
```

If both print tables, installation is working.

---

## 🧩 Usage Examples

### YahooFinanceSource

```python
from sdu_dst.sources.yahoo import YahooFinanceSource
import asyncio

async def main():
    y = YahooFinanceSource()
    df = await y.fetch_prices(["AAPL"], "2024-01-01", "2024-01-31")
    print(df.head())

asyncio.run(main())
```

---

### GDELTSource (events)

```python
from sdu_dst.sources.gdelt import GDELTSource
import asyncio

async def main():
    g = GDELTSource()
    events = await g.fetch_events("Apple", "2024-01-01", "2024-01-31")
    print(events.head())
    await g.close()

asyncio.run(main())
```

---

## 🔌 Available Sources

| Class                | Type  | Description                     |
|----------------------|-------|---------------------------------|
| YahooFinanceSource   | Stock | Historical OHLCV               |
| GDELTSource          | News  | Global news feed (JSON events) |

Upcoming:

- SEC EDGAR filings
- Nasdaq Nordic RSS
- Polygon.io tick WebSockets
- Alpaca streaming

---

## 🏗️ Project Structure

```
src/sdu_dst/
├─ api/          # Async HTTP/WebSocket clients
├─ cache/        # Redis cache + local TTL fallback
├─ sources/      # Plug-in data sources
├─ utils/        # Timezone helpers
└─ __init__.py
```

---

## 🚧 Roadmap

- Event aggregation service
- Tier severity scoring
- Statistical event windows
- Dash dashboards
- Machine learning modules
- Market impact heatmaps

---

## 🤝 Contributing

Pull requests and issues are welcome.

By contributing, you agree that your contributions are licensed under the
same terms as the project.

See LICENSE and ACADEMIC_USE.md.

---

## 🔐 License

This project is licensed under the Business Source License 1.1 (BUSL).

- Academic / research use: Allowed ✅
- Commercial use: Requires license ❌

See LICENSE and ACADEMIC_USE.md for full terms.

---

## 🏢 Commercial Licensing Contact

For commercial licensing inquiries:

```
guruguldmand@gmail.com
```

---

## 🧾 Citation (optional)

```
Guldmand, J. (2025).
SDU Data Science Tool (sdu-dst).
GitHub Repository: https://github.com/guldmand/SDU_DataScienceTool
```

---

## 😎 Author

**Jannik Busse Guldmand**  
MSc Data Science student — University of Southern Denmark  
GitHub: https://github.com/guldmand

