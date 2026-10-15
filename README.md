# 🏛️ QUANT-APEX v2.5: Institutional Equity Research & 3-Stage Valuation Terminal

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Live_App-FF4B4B?style=for-the-badge&logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?style=for-the-badge&logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**QUANT-APEX v2.5** is an institutional-grade quantitative equity screening, forensic auditing, technical momentum timing, and intrinsic valuation workstation designed for Indian Equities (NSE/BSE). 

Unlike generic screeners that apply a single static formula across all stocks, **QUANT-APEX** dynamically adapts its fundamental weightages across **Large-Cap, Mid-Cap, and Small-Cap** tiers (SEBI/AMFI classification) and automatically switches between **Corporate (Non-BFSI)** and **BFSI (Banks & NBFCs)** valuation regimes.

---

## 🚀 Key Institutional Capabilities

### 1. Dynamic Multi-Cap 100-Point Scoring Matrix
Automatically shifts pillar weights based on Market-Cap risk profiles and ranks stocks in **hierarchical order (Highest Alpha Score First)**:

| Fundamental Pillar | Large-Cap Weight | Mid-Cap Weight | Small-Cap Weight | Primary Analytical Focus |
| :--- | :---: | :---: | :---: | :--- |
| **1. Profitability & Capital Moat** | **30** | **25** | **15** | ROCE, ROE, Operating Margin (or ROA & NIM for BFSI) |
| **2. Growth & Operating Scale** | **15** | **30** | **25** | 3Y Revenue & PAT CAGR + Operating Leverage Bonus |
| **3. Cash Flow & Balance Sheet** | **20** | **20** | **25** | 5Y CFO/EBITDA Conversion, Debt/Equity, Interest Coverage |
| **4. Governance & Forensics** | **15** | **15** | **25** | Promoter Skin-in-the-Game, Zero Pledge, Receivable Days |
| **5. Valuation Comfort** | **20** | **10** | **10** | PEG Ratio & Historical P/E Multiple Comfort |
| **Total Fundamental Score** | **100** | **100** | **100** | **Blended with Technical Score (80:20) for Composite Alpha** |

---

### 2. Dual-Regime Valuation Engine (Corporate vs. BFSI Auto-Switch)
* **🏭 Corporate Mode (Non-BFSI):** Executes a **10-Year 3-Stage FCFF Fade DCF Model** (5-Year High Growth $\rightarrow$ 5-Year Linear Fade $\rightarrow$ Perpetual Gordon Terminal Value) with a customizable **Cyclical Peak-Margin Haircut** for Cement, Metals, and Chemicals.
* **🏦 BFSI Mode (Banks & NBFCs):** Automatically bypasses Debt/Equity and FCFF distortions to run a **10-Year Excess Return (Residual Income) + Justified P/B Valuation Model** anchored on **ROA, ROE, NIM, Net NPA, and Capital Adequacy (CAR)**.
* **🏈 Football Field Blended Target:** Combines **70% Intrinsic DCF/Excess Return Value + 30% Sector Peer Relative Multiple (EV/EBITDA & P/E)** to compute Bear, Base, and Bull Case targets.

---

### 3. Forensic Kill-Switch (Knock-Out Protection)
Automatically overrides the Composite Score to **`0.0 (FORENSIC REJECT)`** if any critical governance or survival threshold is breached:
* **Promoter Pledging** $> 20\%$
* **5Y Cumulative CFO / EBITDA** $< 35\%$ (Paper profits not converting into operating cash)
* **Debt-to-Equity** $> 1.8\text{x}$ (Corporate) or **Net NPA** $> 2.5\%$ / **CAR** $< 12\%$ (BFSI)

---

### 4. Quant-Technical Institutional Timing Engine
Prevents **Value Traps** and "catching falling knives" by scoring each stock out of 100 across 4 price-action metrics:
* **Long-Term Trend:** $\text{CMP} > 200\text{-Day EMA}$
* **Golden Cross Structure:** $50\text{-Day EMA} > 200\text{-Day EMA}$
* **Momentum Sweet-Spot:** $\text{RSI}(14) \in [50, 68]$
* **Institutional Trend Strength:** $\text{ADX}(14) \ge 20$

---

### 5. Live NSE Ticker Fetcher & Analyst Calibration Desk
* **⚡ Live Yahoo Finance (`yfinance`) Integration:** Fetch live CMP, Market Cap, Beta, Debt, Cash, ROE, and 1-year daily technicals (`EMA-50`, `EMA-200`, `RSI-14`, `ADX-14`) for any NSE ticker (e.g., `BEL.NS`, `HAL.NS`, `TRENT.NS`).
* **🛠️ Analyst Override Desk:** Calibrate live inputs with verified Annual Report / Screener.in figures (Normalized Base FCFF, actual Promoter Pledge %, Peer Median P/E, or Bank NNPA %) and re-rank the leaderboard in real time.

---

### 6. 1-Click 5-Tab Institutional Excel Workbook (`.xlsx`) Generator
Exports a fully formatted, formula-driven Excel model (`=SUM`, `=IF`, dynamic discounting) containing:
1. **`Executive_IC_Memo`:** Investment Committee scorecard, valuation summary & action verdict.
2. **`10Y_3Stage_Valuation`:** Complete 10-year explicit cash flow/excess return schedule & EV-to-Equity bridge.
3. **`Football_Field_Scenarios`:** Bear, Base, Bull, Intrinsic DCF, and Relative Valuation comparison.
4. **`Sensitivity_Matrix_2D`:** $5 \times 5$ WACC vs. Terminal Growth Rate Fair Value matrix.
5. **`Forensic_&_Tech_Audit`:** Governance and technical indicator checklist.

---

## 💻 Local Installation & Usage

```bash
# 1. Clone the repository
git clone [https://github.com/YOUR-USERNAME/quant-apex-terminal.git](https://github.com/YOUR-USERNAME/quant-apex-terminal.git)
cd quant-apex-terminal

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Streamlit Terminal
streamlit run app.py
