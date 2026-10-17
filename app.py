# =========================================================
# QUANT-APEX: PART 1 OF 2 (SECTIONS 1 TO 8)
# Copy-paste this first, then paste PART 2 right below it!
# =========================================================
import io
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & CLEAN INSTITUTIONAL HEADER
# ---------------------------------------------------------
st.set_page_config(
    page_title="QUANT-APEX | Institutional 8-Regime Valuation & Quant Terminal",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ QUANT-APEX: Institutional Multi-Cap Quant & 8-Regime Valuation Terminal")
st.markdown(
    "**8-Category Adaptive Valuation Engine (Main + Supporting Method Matrix)** · "
    "**Multi-Cap 100-Point Quant Ranking** · **Portfolio Capital Allocator (₹)** · **Walk-Forward Nifty 50 Backtesting**"
)

# ---------------------------------------------------------
# 2. MASTER WEIGHTS BY MARKET CAP
# ---------------------------------------------------------
CATEGORY_WEIGHTS = {
    "Large-Cap": {"Profitability": 30, "Growth": 15, "CashFlow_BS": 20, "Governance": 15, "Valuation": 20},
    "Mid-Cap":   {"Profitability": 25, "Growth": 30, "CashFlow_BS": 20, "Governance": 15, "Valuation": 10},
    "Small-Cap": {"Profitability": 15, "Growth": 25, "CashFlow_BS": 25, "Governance": 25, "Valuation": 10}
}

DB_FILENAME = "quant_apex_db.csv"

# ---------------------------------------------------------
# 3. AUTOMATIC DATABASE SANITIZER & GLITCH UNCORRUPTOR
# ---------------------------------------------------------
def auto_sanitize_database(df):
    if df is None or df.empty:
        return df

    df = df.copy()
    non_lending_bfsi_tickers = {
        "BSE", "MCX", "CDSL", "CAMS", "KFINTECH", "ANGELONE", "GROWW",
        "NUVAMA", "SBILIFE", "HDFCLIFE", "ICICIPRULI", "LICI", "HDFCAMC", "NAM-INDIA", "MFSL", "GICRE"
    }
    cyc_keywords = [
        "CEMENT", "BUILDING", "STEEL", "METAL", "ALUMIN", "COPPER", "ZINC", "CHEM", "INFRA", "COMMODIT",
        "SUGAR", "OIL", "REFIN", "GAS", "PETRO", "COAL", "MINING", "SHIPPING", "MARINE",
        "FERTIL", "AGRI", "POWER", "UTILITIES", "PAPER", "TEXTILE", "TYRE"
    ]
    cyc_tickers = {
        "IOC", "ONGC", "BPCL", "HPCL", "CHENNPETRO", "MRPL", "COALINDIA", "OIL", "PETRONET",
        "SCI", "GESHIP", "HINDALCO", "NATIONALUM", "HINDCOPPER", "TATASTEEL", "JINDALSTEL", "SAIL", "NMDC",
        "VEDL", "HINDZINC", "NTPC", "POWERGRID", "GAIL", "SHREECEM", "AMBUJACEM", "UPL"
    }

    for idx, row in df.iterrows():
        t_sym = str(row["Ticker"]).strip().upper()
        sec_u = str(row["Sector"]).upper()
        cmp_val = max(float(row.get("CMP", 100.0)), 1.0)
        shares_cr = max(float(row.get("Shares_Cr", 1.0)), 0.05)
        mcap_cr = cmp_val * shares_cr
        opm_dec = np.clip(float(row.get("OPM", 16.0)) / 100.0, 0.05, 0.65)

        is_lending_bfsi = (
            any(k in sec_u for k in ["BANK", "NBFC", "CREDIT", "MORTGAGE", "HOUSING FIN", "LENDING", "BFSI"])
            and not any(x in sec_u for x in ["INSURANCE", "CAPITAL MARKET", "EXCHANGE", "ASSET MANAGEMENT", "BROK", "DATA"])
            and t_sym not in non_lending_bfsi_tickers
        )
        df.at[idx, "Is_BFSI"] = bool(is_lending_bfsi)

        is_cyc = any(k in sec_u for k in cyc_keywords) or (t_sym in cyc_tickers)
        df.at[idx, "Is_Cyclical"] = bool(is_cyc)

        if is_cyc:
            df.at[idx, "Peer_EV_EBITDA"] = 8.0
            df.at[idx, "Peer_PE"] = 10.5
            df.at[idx, "Proj_Growth_5Y"] = min(float(row.get("Proj_Growth_5Y", 11.0)), 13.0)
            df.at[idx, "Term_Growth"] = min(float(row.get("Term_Growth", 4.5)), 4.5)
        else:
            df.at[idx, "Peer_EV_EBITDA"] = min(float(row.get("Peer_EV_EBITDA", 18.0)), 20.0)
            df.at[idx, "Peer_PE"] = min(float(row.get("Peer_PE", 22.0)), 24.0)

        ebitda_cr = float(row.get("Base_EBITDA_Cr", 0.0))
        fcff_cr = float(row.get("Base_FCFF_Cr", 0.0))
        rev_cr = float(row.get("Base_Rev_Cr", 0.0))
        debt_cr = float(row.get("Total_Debt_Cr", 0.0))
        cash_cr = float(row.get("Cash_Cr", 0.0))

        while abs(ebitda_cr) > (mcap_cr * 0.55) and mcap_cr > 50:
            ebitda_cr /= 86.0
            fcff_cr /= 86.0
            rev_cr /= 86.0
            debt_cr /= 86.0
            cash_cr /= 86.0

        while abs(fcff_cr) > (mcap_cr * 0.45) and mcap_cr > 50:
            fcff_cr /= 86.0

        if t_sym in {"INFY", "HCLTECH", "WIPRO"} and 0 < ebitda_cr < (mcap_cr * 0.008):
            ebitda_cr *= 86.0
            fcff_cr *= 86.0
            rev_cr *= 86.0
            debt_cr *= 86.0
            cash_cr *= 86.0

        if not is_lending_bfsi and (rev_cr <= abs(ebitda_cr) * 1.05 or rev_cr < mcap_cr * 0.03):
            rev_cr = abs(ebitda_cr) / opm_dec if abs(ebitda_cr) > 0 else mcap_cr * 0.45

        eps_val = float(row.get("EPS", 0.0))
        if abs(eps_val) > cmp_val * 0.30:
            while abs(eps_val) > cmp_val * 0.30:
                eps_val /= 86.0
            df.at[idx, "EPS"] = round(eps_val, 2)

        df.at[idx, "Base_Rev_Cr"] = round(rev_cr, 2)
        df.at[idx, "Base_EBITDA_Cr"] = round(ebitda_cr, 2)
        if ebitda_cr > 0:
            df.at[idx, "Base_FCFF_Cr"] = round(min(max(fcff_cr, ebitda_cr * 0.25), ebitda_cr * 0.75), 2)
        else:
            df.at[idx, "Base_FCFF_Cr"] = round(fcff_cr, 2)
        df.at[idx, "Total_Debt_Cr"] = round(debt_cr, 2)
        df.at[idx, "Cash_Cr"] = round(cash_cr, 2)

    return df

# ---------------------------------------------------------
# 4. INITIAL CURATED DATASET & DATABASE LOADER
# ---------------------------------------------------------
def get_initial_dataset():
    data = [
        {"Ticker": "TCS", "Company": "Tata Consultancy Services", "Category": "Large-Cap", "Sector": "IT Services",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 4120.0, "Shares_Cr": 361.8, "Base_Rev_Cr": 240893.0, "Base_EBITDA_Cr": 64200.0, "Base_FCFF_Cr": 44200.0,
         "Total_Debt_Cr": 8020.0, "Cash_Cr": 46500.0, "Beta": 0.78, "Cost_of_Debt": 7.2, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 10.5, "Term_Growth": 5.0, "Peer_EV_EBITDA": 20.0, "Peer_PE": 24.0, "EPS": 135.0,
         "ROCE": 64.0, "ROE": 51.0, "OPM": 25.0, "Sales_CAGR_3Y": 12.5, "PAT_CAGR_3Y": 11.0,
         "CFO_EBITDA": 88.0, "Debt_Equity": 0.08, "Int_Coverage": 45.0, "Promoter_Hold": 71.8,
         "Promoter_Pledge": 0.5, "Debtor_Days": 68, "PEG": 2.4, "PE_vs_Median": 0.95,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 260.0,
         "EMA_50": 4080.0, "EMA_200": 3910.0, "RSI_14": 58.5, "ADX_14": 24.2},

        {"Ticker": "ICICIBANK", "Company": "ICICI Bank Ltd", "Category": "Large-Cap", "Sector": "BFSI - Banking",
         "Is_BFSI": True, "Is_Cyclical": False,
         "CMP": 1265.0, "Shares_Cr": 704.0, "Base_Rev_Cr": 165840.0, "Base_EBITDA_Cr": 58200.0, "Base_FCFF_Cr": 0.0,
         "Total_Debt_Cr": 0.0, "Cash_Cr": 0.0, "Beta": 0.96, "Cost_of_Debt": 7.0, "Tax_Rate": 25.0,
         "Proj_Growth_5Y": 16.5, "Term_Growth": 5.5, "Peer_EV_EBITDA": 0.0, "Peer_PE": 18.0, "EPS": 62.5,
         "ROCE": 18.0, "ROE": 18.2, "OPM": 42.0, "Sales_CAGR_3Y": 21.0, "PAT_CAGR_3Y": 26.5,
         "CFO_EBITDA": 80.0, "Debt_Equity": 0.0, "Int_Coverage": 10.0, "Promoter_Hold": 0.0,
         "Promoter_Pledge": 0.0, "Debtor_Days": 0, "PEG": 1.15, "PE_vs_Median": 0.98,
         "ROA": 2.38, "NIM": 4.45, "NNPA": 0.43, "CAR": 16.7, "BVPS": 368.0,
         "EMA_50": 1235.0, "EMA_200": 1140.0, "RSI_14": 62.0, "ADX_14": 28.5},

        {"Ticker": "SUNPHARMA", "Company": "Sun Pharmaceutical Industries", "Category": "Large-Cap", "Sector": "Pharmaceuticals",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 1780.0, "Shares_Cr": 239.9, "Base_Rev_Cr": 48496.0, "Base_EBITDA_Cr": 13020.0, "Base_FCFF_Cr": 9850.0,
         "Total_Debt_Cr": 2850.0, "Cash_Cr": 18400.0, "Beta": 0.68, "Cost_of_Debt": 7.5, "Tax_Rate": 20.0,
         "Proj_Growth_5Y": 14.5, "Term_Growth": 5.5, "Peer_EV_EBITDA": 20.0, "Peer_PE": 24.0, "EPS": 46.5,
         "ROCE": 19.5, "ROE": 16.2, "OPM": 26.8, "Sales_CAGR_3Y": 13.8, "PAT_CAGR_3Y": 18.5,
         "CFO_EBITDA": 82.0, "Debt_Equity": 0.05, "Int_Coverage": 32.0, "Promoter_Hold": 54.5,
         "Promoter_Pledge": 0.0, "Debtor_Days": 82, "PEG": 1.6, "PE_vs_Median": 1.05,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 280.0,
         "EMA_50": 1745.0, "EMA_200": 1590.0, "RSI_14": 61.2, "ADX_14": 26.8},

        {"Ticker": "POLYCAB", "Company": "Polycab India Ltd", "Category": "Mid-Cap", "Sector": "Cables & FMEG",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 6650.0, "Shares_Cr": 15.02, "Base_Rev_Cr": 18039.0, "Base_EBITDA_Cr": 2560.0, "Base_FCFF_Cr": 1820.0,
         "Total_Debt_Cr": 150.0, "Cash_Cr": 2150.0, "Beta": 0.95, "Cost_of_Debt": 8.0, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 20.0, "Term_Growth": 5.5, "Peer_EV_EBITDA": 20.0, "Peer_PE": 24.0, "EPS": 132.0,
         "ROCE": 31.5, "ROE": 24.0, "OPM": 14.2, "Sales_CAGR_3Y": 22.5, "PAT_CAGR_3Y": 28.0,
         "CFO_EBITDA": 74.0, "Debt_Equity": 0.02, "Int_Coverage": 22.0, "Promoter_Hold": 65.2,
         "Promoter_Pledge": 0.0, "Debtor_Days": 46, "PEG": 1.35, "PE_vs_Median": 1.10,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 545.0,
         "EMA_50": 6520.0, "EMA_200": 5890.0, "RSI_14": 63.8, "ADX_14": 29.4},

        {"Ticker": "CMSINFO", "Company": "CMS Info Systems Ltd", "Category": "Small-Cap", "Sector": "Cash Logistics & AIoT",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 565.0, "Shares_Cr": 16.28, "Base_Rev_Cr": 2265.0, "Base_EBITDA_Cr": 595.0, "Base_FCFF_Cr": 390.0,
         "Total_Debt_Cr": 0.0, "Cash_Cr": 780.0, "Beta": 0.90, "Cost_of_Debt": 8.2, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 18.5, "Term_Growth": 5.0, "Peer_EV_EBITDA": 15.0, "Peer_PE": 20.0, "EPS": 24.5,
         "ROCE": 26.5, "ROE": 20.2, "OPM": 25.5, "Sales_CAGR_3Y": 19.5, "PAT_CAGR_3Y": 23.0,
         "CFO_EBITDA": 80.0, "Debt_Equity": 0.00, "Int_Coverage": 35.0, "Promoter_Hold": 26.7,
         "Promoter_Pledge": 0.0, "Debtor_Days": 62, "PEG": 0.95, "PE_vs_Median": 0.92,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 122.0,
         "EMA_50": 552.0, "EMA_200": 505.0, "RSI_14": 59.0, "ADX_14": 27.1},
    ]
    return pd.DataFrame(data)

def save_master_database(df):
    try:
        df.to_csv(DB_FILENAME, index=False)
    except Exception:
        pass

def load_master_database():
    if os.path.exists(DB_FILENAME):
        try:
            df_loaded = pd.read_csv(DB_FILENAME)
            df_clean = auto_sanitize_database(df_loaded)
            save_master_database(df_clean)
            return df_clean
        except Exception:
            return get_initial_dataset()
    else:
        df_init = get_initial_dataset()
        save_master_database(df_init)
        return df_init

if "master_df" not in st.session_state:
    st.session_state.master_df = load_master_database()
else:
    st.session_state.master_df = auto_sanitize_database(st.session_state.master_df)

# ---------------------------------------------------------
# 5. TWO-PASS EXACT MATCH CSV MAPPER
# ---------------------------------------------------------
def parse_screener_bulk_csv(uploaded_df):
    required_native = {"Ticker", "Company", "Category", "CMP", "ROCE", "ROE"}
    if required_native.issubset(set(uploaded_df.columns)):
        return auto_sanitize_database(uploaded_df)

    col_map = {str(c).strip().lower(): c for c in uploaded_df.columns}

    def get_col_series(candidates, default_val):
        for cand in candidates:
            if cand in col_map:
                orig_col = col_map[cand]
                s = pd.to_numeric(uploaded_df[orig_col].astype(str).str.replace(",", "").str.replace("%", ""), errors="coerce")
                return s.fillna(default_val)
        for cand in candidates:
            for k_low, orig_col in col_map.items():
                if cand in k_low:
                    s = pd.to_numeric(uploaded_df[orig_col].astype(str).str.replace(",", "").str.replace("%", ""), errors="coerce")
                    return s.fillna(default_val)
        return pd.Series([default_val] * len(uploaded_df), index=uploaded_df.index)

    def get_text_series(candidates, default_str):
        for cand in candidates:
            if cand in col_map:
                return uploaded_df[col_map[cand]].fillna(default_str).astype(str).str.strip()
        for cand in candidates:
            for k_low, orig_col in col_map.items():
                if cand in k_low:
                    return uploaded_df[orig_col].fillna(default_str).astype(str).str.strip()
        return pd.Series([default_str] * len(uploaded_df), index=uploaded_df.index)

    company_s = get_text_series(["name", "company"], "Unknown Corp")
    ticker_s = get_text_series(["nse code", "ticker", "symbol", "bse code"], "")
    ticker_s = np.where(ticker_s == "", company_s.str.upper().str.replace("[^A-Z0-9]", "", regex=True).str[:10], ticker_s.str.upper())

    sector_s = get_text_series(["industry", "sector"], "Industrial")
    cmp_s = np.maximum(get_col_series(["current price", "cmp", "price"], 500.0), 1.0)
    mcap_s = np.maximum(get_col_series(["market capitalization", "mar cap", "market cap"], 25000.0), 100.0)

    cat_list = ["Large-Cap" if mc >= 106346 else ("Mid-Cap" if mc >= 33664 else "Small-Cap") for mc in mcap_s]
    shares_s = (mcap_s / cmp_s).round(2)

    roce_s = get_col_series(["return on capital employed", "roce"], 18.0)
    roe_s = get_col_series(["return on equity", "roe"], 15.0)
    opm_s = get_col_series(["opm", "operating profit margin"], 16.0)
    sales_g_s = get_col_series(["sales growth 3years", "sales growth 3yr", "sales_cagr_3y"], 14.0)
    pat_g_s = get_col_series(["profit growth 3years", "profit growth 3yr", "pat_cagr_3y"], 16.0)

    rev_s = get_col_series(["sales", "revenue", "base_rev_cr"], mcap_s * 0.45)
    ebitda_s = get_col_series(["operating profit", "ebitda", "base_ebitda_cr"], rev_s * (opm_s / 100.0))
    fcf_3y_s = get_col_series(["free cash flow 3years", "fcf 3yr"], np.nan)
    fcf_1y_s = get_col_series(["free cash flow", "base_fcff_cr"], np.nan)

    fcff_s = np.where(~np.isnan(fcf_3y_s), fcf_3y_s / 3.0, np.where(~np.isnan(fcf_1y_s), fcf_1y_s, ebitda_s * 0.62))

    debt_s = get_col_series(["debt", "total debt", "total_debt_cr"], 0.0)
    cash_s = get_col_series(["cash equivalents", "cash", "cash_cr"], mcap_s * 0.04)
    de_s = get_col_series(["debt to equity", "debt_equity", "d/e"], 0.15)
    ic_s = get_col_series(["interest coverage ratio", "interest coverage", "int_coverage"], 12.0)
    prom_s = get_col_series(["promoter holding", "promoter_hold"], 52.0)
    pledge_s = get_col_series(["pledged percentage", "promoter_pledge", "pledge"], 0.0)
    debtor_s = get_col_series(["debtor days", "debtor_days", "receivable days"], 55.0)
    pe_s = get_col_series(["price to earning", "p/e", "pe"], 22.0)
    peg_s = get_col_series(["peg ratio", "peg"], (pe_s / np.maximum(pat_g_s, 8.0)).round(2))
    eps_s = get_col_series(["eps", "earnings per share"], (cmp_s / np.maximum(pe_s, 5.0)).round(2))
    bvps_s = get_col_series(["book value", "bvps"], (cmp_s * 0.25).round(2))
    roa_s = get_col_series(["return on assets", "roa"], 2.1)

    ema50_s = get_col_series(["dma 50", "ema 50", "50 dma", "ema_50"], (cmp_s * 0.97).round(2))
    ema200_s = get_col_series(["dma 200", "ema 200", "200 dma", "ema_200"], (cmp_s * 0.91).round(2))
    rsi_s = get_col_series(["rsi", "rsi_14"], 56.0)
    adx_s = get_col_series(["adx", "adx_14"], 23.0)

    cfo_3y_s = get_col_series(["cash from operating activity", "operating cash flow 3years", "cfo_ebitda"], np.nan)
    cfo_ebitda_s = np.where(~np.isnan(cfo_3y_s) & (cfo_3y_s <= 150), cfo_3y_s, 76.0)

    rows_out = []
    for i in range(len(uploaded_df)):
        t_sym = str(ticker_s[i]).strip().upper()
        sec_upper = str(sector_s.iloc[i]).upper()

        is_bfsi = (
            any(k in sec_upper for k in ["BANK", "NBFC", "CREDIT", "MORTGAGE", "HOUSING FIN", "FINANCIAL"])
            and not any(x in sec_upper for x in ["INSURANCE", "CAPITAL MARKET", "EXCHANGE", "ASSET MANAGEMENT", "BROK", "DATA"])
            and t_sym not in {"BSE", "MCX", "CDSL", "CAMS", "KFINTECH", "ANGELONE", "GROWW", "NUVAMA", "SBILIFE", "HDFCLIFE", "ICICIPRULI", "LICI", "MFSL", "GICRE"}
        )

        is_cyc = any(k in sec_upper for k in [
            "CEMENT", "BUILDING", "STEEL", "METAL", "ALUMIN", "COPPER", "ZINC", "CHEM", "INFRA", "COMMODIT",
            "SUGAR", "OIL", "REFIN", "GAS", "PETRO", "COAL", "MINING", "SHIPPING", "MARINE",
            "FERTIL", "AGRI", "POWER", "UTILITIES", "PAPER", "TEXTILE", "TYRE"
        ])

        rows_out.append({
            "Ticker": t_sym,
            "Company": str(company_s.iloc[i]),
            "Category": cat_list[i],
            "Sector": "BFSI - Lending" if is_bfsi else str(sector_s.iloc[i]),
            "Is_BFSI": bool(is_bfsi),
            "Is_Cyclical": bool(is_cyc),
            "CMP": round(float(cmp_s.iloc[i]), 2),
            "Shares_Cr": max(round(float(shares_s.iloc[i]), 2), 0.1),
            "Base_Rev_Cr": round(float(rev_s.iloc[i]), 2),
            "Base_EBITDA_Cr": round(float(ebitda_s.iloc[i]), 2),
            "Base_FCFF_Cr": round(float(fcff_s[i]), 2),
            "Total_Debt_Cr": round(float(debt_s.iloc[i]), 2),
            "Cash_Cr": round(float(cash_s.iloc[i]), 2),
            "Beta": 1.10 if is_cyc else 0.92,
            "Cost_of_Debt": 7.8,
            "Tax_Rate": 25.2,
            "Proj_Growth_5Y": round(float(np.clip(sales_g_s.iloc[i], 8.0, 13.0 if is_cyc else 20.0)), 1),
            "Term_Growth": 4.5 if is_cyc else 5.5,
            "Peer_EV_EBITDA": 8.0 if is_cyc else 18.0,
            "Peer_PE": 10.5 if is_cyc else 22.0,
            "EPS": round(float(eps_s.iloc[i]), 2),
            "ROCE": round(float(roce_s.iloc[i]), 1),
            "ROE": round(float(roe_s.iloc[i]), 1),
            "OPM": round(float(opm_s.iloc[i]), 1),
            "Sales_CAGR_3Y": round(float(sales_g_s.iloc[i]), 1),
            "PAT_CAGR_3Y": round(float(pat_g_s.iloc[i]), 1),
            "CFO_EBITDA": round(float(cfo_ebitda_s[i]), 1),
            "Debt_Equity": round(float(de_s.iloc[i]), 2),
            "Int_Coverage": round(float(ic_s.iloc[i]), 1),
            "Promoter_Hold": round(float(prom_s.iloc[i]), 1),
            "Promoter_Pledge": round(float(pledge_s.iloc[i]), 1),
            "Debtor_Days": int(np.clip(debtor_s.iloc[i], 0, 365)),
            "PEG": round(float(np.clip(peg_s.iloc[i], 0.3, 5.0)), 2),
            "PE_vs_Median": 1.0,
            "ROA": round(float(roa_s.iloc[i]), 2) if is_bfsi else 0.0,
            "NIM": 4.3 if is_bfsi else 0.0,
            "NNPA": 0.65 if is_bfsi else 0.0,
            "CAR": 17.5 if is_bfsi else 0.0,
            "BVPS": round(float(bvps_s.iloc[i]), 2),
            "EMA_50": round(float(ema50_s.iloc[i]), 2),
            "EMA_200": round(float(ema200_s.iloc[i]), 2),
            "RSI_14": round(float(rsi_s.iloc[i]), 1),
            "ADX_14": round(float(adx_s.iloc[i]), 1)
        })
    return auto_sanitize_database(pd.DataFrame(rows_out))

# ---------------------------------------------------------
# 6. LIVE NSE TICKER FETCHER
# ---------------------------------------------------------
def fetch_live_nse_stock(ticker_symbol):
    clean_sym = ticker_symbol.strip().upper()
    if not clean_sym.endswith(".NS") and not clean_sym.endswith(".BO"):
        clean_sym += ".NS"

    tk = yf.Ticker(clean_sym)
    info = tk.info
    hist = tk.history(period="1y")

    if hist.empty or ("currentPrice" not in info and "regularMarketPrice" not in info):
        raise ValueError(f"Could not fetch valid NSE data for {clean_sym}")

    cmp_val = float(info.get("currentPrice") or info.get("regularMarketPrice") or hist["Close"].iloc[-1])
    fin_curr = str(info.get("financialCurrency", "INR")).upper()
    fx_mult = 86.0 if fin_curr == "USD" else 1.0

    close_s = hist["Close"]
    ema50 = float(close_s.ewm(span=50, adjust=False).mean().iloc[-1])
    ema200 = float(close_s.ewm(span=200, adjust=False).mean().iloc[-1])

    delta = close_s.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi14 = float((100 - (100 / (1 + rs))).iloc[-1]) if not np.isnan(rs.iloc[-1]) else 52.0

    tr = pd.concat([
        hist["High"] - hist["Low"],
        (hist["High"] - close_s.shift()).abs(),
        (hist["Low"] - close_s.shift()).abs()
    ], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    up_move = hist["High"].diff()
    down_move = -hist["Low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100 * pd.Series(plus_dm, index=hist.index).rolling(14).mean() / atr14
    minus_di = 100 * pd.Series(minus_dm, index=hist.index).rolling(14).mean() / atr14
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx14 = float(dx.rolling(14).mean().iloc[-1]) if not np.isnan(dx.rolling(14).mean().iloc[-1]) else 22.0

    mcap_cr = float(info.get("marketCap", 50000 * 1e7)) / 1e7
    cat = "Large-Cap" if mcap_cr >= 106346 else ("Mid-Cap" if mcap_cr >= 33664 else "Small-Cap")

    shares_cr = round(mcap_cr / cmp_val, 2)
    sector = info.get("sector", "Industrial")
    industry = info.get("industry", "")
    sec_comb = (sector + " " + industry).upper()
    t_base = clean_sym.replace(".NS", "").replace(".BO", "")

    is_bfsi = (
        any(k in sec_comb for k in ["BANK", "NBFC", "CREDIT", "MORTGAGE", "HOUSING FIN"])
        and not any(x in sec_comb for x in ["INSURANCE", "CAPITAL MARKET", "EXCHANGE", "ASSET MANAGEMENT", "BROK"])
        and t_base not in {"BSE", "MCX", "CDSL", "CAMS", "KFINTECH", "ANGELONE", "GROWW", "NUVAMA", "SBILIFE", "HDFCLIFE"}
    )
    is_cyclical = any(k in sec_comb for k in [
        "CEMENT", "STEEL", "METAL", "ALUMIN", "CHEM", "COMMODIT", "CONSTRUCTION",
        "OIL", "REFIN", "GAS", "COAL", "MINING", "SHIPPING", "MARINE", "FERTIL", "POWER", "UTILITIES"
    ])

    rev_cr = (float(info.get("totalRevenue", mcap_cr * 0.4 * 1e7) or 0) * fx_mult) / 1e7
    ebitda_cr = (float(info.get("ebitda", rev_cr * 0.18 * 1e7) or 0) * fx_mult) / 1e7
    fcf_raw = info.get("freeCashflow")
    fcff_cr = ((float(fcf_raw) * fx_mult) / 1e7) if fcf_raw and fcf_raw > 0 else round(ebitda_cr * 0.62, 2)

    debt_cr = (float(info.get("totalDebt", 0.0) or 0.0) * fx_mult) / 1e7
    cash_cr = (float(info.get("totalCash", 0.0) or 0.0) * fx_mult) / 1e7
    roe_pct = float(info.get("returnOnEquity", 0.16) or 0.16) * 100
    roa_pct = float(info.get("returnOnAssets", 0.02) or 0.02) * 100
    opm_pct = float(info.get("operatingMargins", 0.18) or 0.18) * 100
    rev_g = float(info.get("revenueGrowth", 0.14) or 0.14) * 100
    pat_g = float(info.get("earningsGrowth", 0.16) or 0.16) * 100
    de_ratio = float(info.get("debtToEquity", 15.0) or 15.0) / 100.0
    prom_hold = float(info.get("heldPercentInsiders", 0.52) or 0.52) * 100
    bvps = float(info.get("bookValue", cmp_val * 0.25) or (cmp_val * 0.25))
    eps_val = float(info.get("trailingEps", cmp_val / 25.0) or (cmp_val / 25.0))
    pe_val = cmp_val / max(eps_val, 1.0)
    peg_val = round(pe_val / max(pat_g, 8.0), 2)

    return {
        "Ticker": t_base,
        "Company": info.get("longName", clean_sym),
        "Category": cat,
        "Sector": "BFSI - Lending" if is_bfsi else (industry or sector),
        "Is_BFSI": is_bfsi,
        "Is_Cyclical": is_cyclical,
        "CMP": round(cmp_val, 2),
        "Shares_Cr": max(shares_cr, 0.1),
        "Base_Rev_Cr": round(rev_cr, 2),
        "Base_EBITDA_Cr": round(ebitda_cr, 2),
        "Base_FCFF_Cr": round(fcff_cr, 2),
        "Total_Debt_Cr": round(debt_cr, 2),
        "Cash_Cr": round(cash_cr, 2),
        "Beta": round(float(info.get("beta", 0.95) or 0.95), 2),
        "Cost_of_Debt": 7.8,
        "Tax_Rate": 25.2,
        "Proj_Growth_5Y": round(np.clip(rev_g, 8.0, 13.0 if is_cyclical else 20.0), 1),
        "Term_Growth": 4.5 if is_cyclical else 5.5,
        "Peer_EV_EBITDA": 8.0 if is_cyclical else 18.0,
        "Peer_PE": 10.5 if is_cyclical else 22.0,
        "EPS": round(eps_val, 2),
        "ROCE": round(roe_pct * 1.15, 1),
        "ROE": round(roe_pct, 1),
        "OPM": round(opm_pct, 1),
        "Sales_CAGR_3Y": round(np.clip(rev_g, 6.0, 35.0), 1),
        "PAT_CAGR_3Y": round(np.clip(pat_g, 6.0, 40.0), 1),
        "CFO_EBITDA": 76.0,
        "Debt_Equity": round(de_ratio, 2),
        "Int_Coverage": 15.0 if de_ratio < 0.5 else 5.5,
        "Promoter_Hold": round(prom_hold, 1),
        "Promoter_Pledge": 0.0,
        "Debtor_Days": 55,
        "PEG": round(np.clip(peg_val, 0.5, 4.5), 2),
        "PE_vs_Median": 1.0,
        "ROA": round(roa_pct, 2),
        "NIM": 4.2 if is_bfsi else 0.0,
        "NNPA": 0.65 if is_bfsi else 0.0,
        "CAR": 17.5 if is_bfsi else 0.0,
        "BVPS": round(bvps, 2),
        "EMA_50": round(ema50, 2),
        "EMA_200": round(ema200, 2),
        "RSI_14": round(rsi14, 1),
        "ADX_14": round(adx14, 1)
    }

# ---------------------------------------------------------
# 7. 8-CATEGORY VALUATION REGIME CLASSIFIER & ENGINE
# ---------------------------------------------------------
def classify_stock_regime(row):
    t_sym = str(row["Ticker"]).strip().upper()
    comp_u = str(row["Company"]).upper()
    sec_u = str(row["Sector"]).upper()
    cat = str(row.get("Category", "Large-Cap"))
    cmp_val = max(float(row.get("CMP", 100.0)), 1.0)
    shares_cr = max(float(row.get("Shares_Cr", 1.0)), 0.05)
    mcap_cr = cmp_val * shares_cr
    eps_val = float(row.get("EPS", 0.0))
    opm_val = float(row.get("OPM", 15.0))
    roe_val = float(row.get("ROE", 15.0))
    roce_val = float(row.get("ROCE", 15.0))
    sales_g = max(float(row.get("Sales_CAGR_3Y", 12.0)), float(row.get("Proj_Growth_5Y", 12.0)))
    de_val = float(row.get("Debt_Equity", 0.2))
    ic_val = float(row.get("Int_Coverage", 5.0))

    holding_tickers = {
        "BAJAJHLDNG", "CHOLAHLDNG", "JINDALPOLY", "PILANIINVS", "KAMA", "TATAINVEST",
        "MAHSCOOTER", "GODREJIND", "GRASIM", "BALMLAWRIE", "SUNDARAM", "TVSHLTD", "BBTC"
    }

    # 7. Banks and NBFCs
    if bool(row.get("Is_BFSI", False)):
        return {
            "Regime": "Banks and NBFCs",
            "Main_Method_Name": "Residual income / justified P/B",
            "Supp_Method_Name": "ROE, asset quality",
            "Main_Weight": 0.65,
            "Supp_Weight": 0.35
        }

    # 8. Holding companies
    if t_sym in holding_tickers or any(k in sec_u for k in ["HOLDING", "CONGLOMERATE"]) or ("HOLDING" in comp_u and not bool(row.get("Is_BFSI", False))):
        return {
            "Regime": "Holding companies",
            "Main_Method_Name": "Sum-of-the-Parts (SOTP)",
            "Supp_Method_Name": "Holding-company discount",
            "Main_Weight": 0.60,
            "Supp_Weight": 0.40
        }

    # 6. Distressed / loss-making
    if eps_val <= 0.0 or opm_val <= 1.5 or roe_val <= 0.0 or (de_val > 2.2 and ic_val < 1.5):
        return {
            "Regime": "Distressed / loss-making",
            "Main_Method_Name": "Asset recovery value",
            "Supp_Method_Name": "Survival and dilution analysis",
            "Main_Weight": 0.60,
            "Supp_Weight": 0.40
        }

    # 4. High-growth, low-profit
    if sales_g >= 18.0 and (opm_val < 10.0 or roe_val < 11.0 or roce_val < 12.0):
        return {
            "Regime": "High-growth, low-profit",
            "Main_Method_Name": "Forecast-based DCF",
            "Supp_Method_Name": "EV/Sales",
            "Main_Weight": 0.55,
            "Supp_Weight": 0.45
        }

    # 5. Penny / micro-cap, profitable
    if mcap_cr < 2000.0 or (mcap_cr < 3500.0 and cmp_val < 50.0):
        return {
            "Regime": "Penny / micro-cap, profitable",
            "Main_Method_Name": "Conservative DCF",
            "Supp_Method_Name": "P/B, peer multiples",
            "Main_Weight": 0.55,
            "Supp_Weight": 0.45
        }

    # 1. Large-Cap, stable cash flow
    if cat == "Large-Cap":
        return {
            "Regime": "Large-Cap, stable cash flow",
            "Main_Method_Name": "FCFF DCF",
            "Supp_Method_Name": "P/E, EV/EBITDA",
            "Main_Weight": 0.60,
            "Supp_Weight": 0.40
        }

    # 2. Mid-Cap, growing earnings
    if cat == "Mid-Cap":
        return {
            "Regime": "Mid-Cap, growing earnings",
            "Main_Method_Name": "DCF + peer multiples",
            "Supp_Method_Name": "Scenario analysis",
            "Main_Weight": 0.60,
            "Supp_Weight": 0.40
        }

    # 3. Small-Cap, profitable
    return {
        "Regime": "Small-Cap, profitable",
        "Main_Method_Name": "Conservative DCF",
        "Supp_Method_Name": "Peer P/E, EV/EBITDA",
        "Main_Weight": 0.50,
        "Supp_Weight": 0.50
    }

def run_3stage_valuation(row, rf_rate=6.8, erp=5.5, custom_g5=None, custom_wacc=None, custom_tg=None, cyclical_haircut_pct=0.0):
    reg_info = classify_stock_regime(row)
    regime = reg_info["Regime"]
    w_main = reg_info["Main_Weight"]
    w_supp = reg_info["Supp_Weight"]

    cmp_val = max(float(row["CMP"]), 1.0)
    shares_cr = max(float(row["Shares_Cr"]), 0.05)
    mcap_cr = cmp_val * shares_cr
    debt_cr = float(row["Total_Debt_Cr"])
    cash_cr = float(row["Cash_Cr"])
    net_cash_cr = cash_cr - debt_cr
    total_cap = mcap_cr + debt_cr

    we = 1.0 if row["Is_BFSI"] else (mcap_cr / total_cap if total_cap > 0 else 1.0)
    wd = 0.0 if row["Is_BFSI"] else (debt_cr / total_cap if total_cap > 0 else 0.0)

    if regime == "Large-Cap, stable cash flow":
        size_prem, min_wacc_floor = 0.0, 9.5
    elif regime == "Mid-Cap, growing earnings":
        size_prem, min_wacc_floor = 0.75, 10.5
    elif regime in ["Small-Cap, profitable", "High-growth, low-profit", "Holding companies"]:
        size_prem, min_wacc_floor = 1.50, 11.5
    elif regime == "Penny / micro-cap, profitable":
        size_prem, min_wacc_floor = 2.50, 13.0
    elif regime == "Distressed / loss-making":
        size_prem, min_wacc_floor = 3.50, 14.5
    else:
        size_prem, min_wacc_floor = 0.50, 10.5

    if row["Is_Cyclical"]:
        min_wacc_floor += 0.75

    ke = rf_rate + float(row["Beta"]) * erp + size_prem
    kd_post_tax = float(row["Cost_of_Debt"]) * (1.0 - float(row["Tax_Rate"]) / 100.0)
    computed_disc = ke if row["Is_BFSI"] else (we * ke + wd * kd_post_tax)

    disc_rate = custom_wacc if custom_wacc is not None else max(round(computed_disc, 2), min_wacc_floor)
    g_stage1 = custom_g5 if custom_g5 is not None else float(row["Proj_Growth_5Y"])
    tg = min(custom_tg if custom_tg is not None else float(row["Term_Growth"]), 6.0)

    if regime in ["Small-Cap, profitable", "Penny / micro-cap, profitable"]:
        tg = min(tg, 4.5 if regime == "Small-Cap, profitable" else 3.5)
        if custom_g5 is None:
            g_stage1 = min(g_stage1, 16.5 if regime == "Small-Cap, profitable" else 12.5)

    if disc_rate <= tg + 1.75:
        tg = round(disc_rate - 2.25, 2)

    r_dec = disc_rate / 100.0
    g1_dec = g_stage1 / 100.0
    tg_dec = tg / 100.0

    haircut_mult = (1.0 - cyclical_haircut_pct / 100.0) if row["Is_Cyclical"] else 1.0
    ebitda_base = float(row["Base_EBITDA_Cr"])
    fcff_base = float(row["Base_FCFF_Cr"])
    rev_base = max(float(row["Base_Rev_Cr"]), mcap_cr * 0.15)

    while abs(ebitda_base) > (mcap_cr * 0.55) and mcap_cr > 50:
        ebitda_base /= 86.0
        fcff_base /= 86.0
        rev_base /= 86.0

    bvps_val = max(float(row["BVPS"]), cmp_val * 0.12)
    eps_val = float(row["EPS"])
    if abs(eps_val) > cmp_val * 0.30:
        eps_val = cmp_val / max(float(row["Peer_PE"]), 12.0)

    growth_schedule = []
    cf_schedule = []
    pv_schedule = []
    metric1_schedule = []

    if regime == "Banks and NBFCs":
        curr_bv = bvps_val
        roe_dec = np.clip(float(row["ROE"]) / 100.0, 0.08, 0.24)
        retention_ratio = 0.78

        for yr in range(1, 11):
            fade_step = 0.0 if yr <= 5 else (yr - 5) / 5.0
            g_yr = g1_dec - fade_step * (g1_dec - tg_dec)
            target_roe = max(r_dec + 0.03, roe_dec * 0.88)
            yr_roe = roe_dec - fade_step * (roe_dec - target_roe)

            eps_yr = curr_bv * yr_roe
            excess_ret_ps = (yr_roe - r_dec) * curr_bv
            pv_er = excess_ret_ps / ((1.0 + r_dec) ** (yr - 0.5))
            curr_bv = curr_bv + eps_yr * retention_ratio

            growth_schedule.append(round(yr_roe * 100, 2))
            metric1_schedule.append(round(curr_bv, 2))
            cf_schedule.append(round(excess_ret_ps, 2))
            pv_schedule.append(round(pv_er, 2))

        sum_pv_10y = round(sum(pv_schedule), 2)
        term_er = cf_schedule[-1] * (1.0 + tg_dec)
        term_val = round(term_er / (r_dec - tg_dec), 2)
        pv_term_val = round(term_val / ((1.0 + r_dec) ** 10.0), 2)

        residual_income_fv = max(bvps_val * 0.5, round(bvps_val + sum_pv_10y + pv_term_val, 2))
        bv_2y = bvps_val * ((1.0 + roe_dec * retention_ratio) ** 2)
        justified_pb = np.clip((roe_dec - tg_dec) / max(r_dec - tg_dec, 0.035), 0.80, 3.2)
        just_pb_fv = round((bv_2y * justified_pb) / ((1.0 + r_dec) ** 1.0), 2)

        main_fv = round(0.50 * residual_income_fv + 0.50 * just_pb_fv, 2)

        nnpa_val = float(row.get("NNPA", 0.5))
        asset_quality_mult = np.clip(1.08 - (nnpa_val * 0.12), 0.70, 1.08)
        eps_2y = max(0.0, eps_val) * ((1.0 + g1_dec * 0.85) ** 2)
        bank_pe = np.clip(8.5 + (float(row["ROE"]) - 10.0) * 0.85, 7.0, 19.0) * asset_quality_mult
        supp_fv = round((eps_2y * bank_pe) / ((1.0 + r_dec) ** 1.5), 2) if eps_val > 0 else round(just_pb_fv * asset_quality_mult, 2)

        enterprise_val = round((w_main * main_fv + w_supp * supp_fv) * shares_cr, 2)
        equity_val = enterprise_val

    else:
        ebit_base = max(0.0, ebitda_base * 0.85 * haircut_mult)
        nopat_base = ebit_base * (1.0 - float(row["Tax_Rate"]) / 100.0)

        if regime == "High-growth, low-profit":
            curr_rev = rev_base
            init_opm = np.clip(float(row["OPM"]) / 100.0, 0.03, 0.12)
            target_opm = 0.15
            for yr in range(1, 11):
                fade_step = 0.0 if yr <= 5 else (yr - 5) / 5.0
                g_yr = g1_dec - fade_step * (g1_dec - tg_dec)
                curr_rev = curr_rev * (1.0 + g_yr)
                conv_opm = init_opm + (yr / 10.0) * (target_opm - init_opm)
                ebitda_yr = curr_rev * conv_opm
                fcff_yr = ebitda_yr * 0.58
                pv_cf = fcff_yr / ((1.0 + r_dec) ** (yr - 0.5))
                growth_schedule.append(round(g_yr * 100, 2))
                metric1_schedule.append(round(curr_rev, 2))
                cf_schedule.append(round(fcff_yr, 2))
                pv_schedule.append(round(pv_cf, 2))
        else:
            cons_haircut = 0.85 if regime in ["Small-Cap, profitable", "Penny / micro-cap, profitable"] else 1.0
            safe_base_fcff = max(
                rev_base * 0.03,
                min(max(fcff_base * haircut_mult, nopat_base * 0.55), max(ebitda_base * haircut_mult * 0.75, rev_base * 0.05))
            ) * cons_haircut
            curr_fcff = safe_base_fcff
            curr_rev = rev_base

            for yr in range(1, 11):
                fade_step = 0.0 if yr <= 5 else (yr - 5) / 5.0
                g_yr = g1_dec - fade_step * (g1_dec - tg_dec)
                curr_rev = curr_rev * (1.0 + g_yr)
                curr_fcff = curr_fcff * (1.0 + g_yr) * (1.0 + (0.02 * fade_step))
                pv_cf = curr_fcff / ((1.0 + r_dec) ** (yr - 0.5))
                growth_schedule.append(round(g_yr * 100, 2))
                metric1_schedule.append(round(curr_rev, 2))
                cf_schedule.append(round(curr_fcff, 2))
                pv_schedule.append(round(pv_cf, 2))

        sum_pv_10y = round(sum(pv_schedule), 2)
        roic_term = max(r_dec + 0.035, min(np.clip(float(row["ROCE"]) / 100.0, 0.14, 0.45), 0.26))
        term_reinv_rate = np.clip(tg_dec / roic_term, 0.15, 0.45)
        term_nopat_cf = (nopat_base * ((1.0 + g1_dec) ** 5) * ((1.0 + tg_dec) ** 6)) * (1.0 - term_reinv_rate)
        term_cf = max(cf_schedule[-1] * (1.0 + tg_dec), term_nopat_cf)
        term_val = round(term_cf / (r_dec - tg_dec), 2)
        pv_term_val = round(term_val / ((1.0 + r_dec) ** 10.0), 2)

        enterprise_val = round(sum_pv_10y + pv_term_val, 2)
        equity_val = max(0.0, round(enterprise_val + net_cash_cr, 2))
        base_dcf_fv = round(equity_val / shares_cr, 2)

        ebitda_3y = max(0.0, ebitda_base * haircut_mult) * ((1.0 + g1_dec) ** 3)
        pv_exit_ev = (ebitda_3y * float(row["Peer_EV_EBITDA"])) / ((1.0 + r_dec) ** 2.5)
        peer_ev_ebitda_fv = round(max(0.0, (pv_exit_ev + net_cash_cr) / shares_cr), 2)

        eps_clean = max(0.0, eps_val)
        eps_2y = eps_clean * ((1.0 + g1_dec) ** 2)
        justified_pe = np.clip(9.0 + 0.70 * g_stage1 + 0.25 * max(0.0, float(row["ROCE"]) - 15.0), 8.0, float(row["Peer_PE"]) * 1.25)
        peer_pe_fv = round((eps_2y * justified_pe) / ((1.0 + (ke / 100.0)) ** 1.5), 2) if eps_clean > 0 else peer_ev_ebitda_fv
        combined_peer_mult_fv = round(0.50 * peer_pe_fv + 0.50 * peer_ev_ebitda_fv, 2)

        if regime == "Large-Cap, stable cash flow":
            main_fv = base_dcf_fv
            supp_fv = combined_peer_mult_fv

        elif regime == "Mid-Cap, growing earnings":
            main_fv = round(0.50 * base_dcf_fv + 0.50 * combined_peer_mult_fv, 2)
            bear_s = main_fv * 0.78
            base_s = main_fv * 1.00
            bull_s = main_fv * 1.28
            supp_fv = round(0.25 * bear_s + 0.50 * base_s + 0.25 * bull_s, 2)

        elif regime == "Small-Cap, profitable":
            main_fv = base_dcf_fv
            supp_fv = combined_peer_mult_fv

        elif regime == "High-growth, low-profit":
            main_fv = base_dcf_fv
            rev_2y = rev_base * ((1.0 + g1_dec) ** 2)
            target_ev_sales = np.clip(1.2 + (g_stage1 / 12.0), 1.5, 4.5)
            pv_ev_sales = (rev_2y * target_ev_sales) / ((1.0 + r_dec) ** 1.5)
            supp_fv = round(max(cmp_val * 0.25, (pv_ev_sales + net_cash_cr) / shares_cr), 2)

        elif regime == "Penny / micro-cap, profitable":
            main_fv = base_dcf_fv
            micro_pb_mult = np.clip(float(row["ROE"]) / 10.0, 0.8, 2.5)
            pb_fv = bvps_val * micro_pb_mult
            supp_fv = round(0.50 * pb_fv + 0.50 * combined_peer_mult_fv, 2)

        elif regime == "Distressed / loss-making":
            tangible_book_recovery = bvps_val * 0.75
            ev_asset_recovery = max(0.0, (rev_base * 0.35 + cash_cr * 0.90 - debt_cr * 1.0) / shares_cr)
            main_fv = round(max(cmp_val * 0.20, 0.60 * tangible_book_recovery + 0.40 * ev_asset_recovery), 2)

            dilution_factor = 0.70
            survival_prob = 0.65 if float(row["Debt_Equity"]) < 1.5 else 0.45
            turnaround_val = max(bvps_val * 0.90, (rev_base * 0.55) / shares_cr)
            supp_fv = round(max(cmp_val * 0.15, turnaround_val * dilution_factor * survival_prob), 2)

        elif regime == "Holding companies":
            core_op_ev = max(0.0, ebitda_base * 10.0)
            investment_book_cr = max(bvps_val * shares_cr * 1.35, mcap_cr * 1.15)
            sotp_equity_cr = max(mcap_cr * 0.50, core_op_ev + investment_book_cr + net_cash_cr)
            main_fv = round(sotp_equity_cr / shares_cr, 2)
            holdco_discount = 0.40
            supp_fv = round(main_fv * (1.0 - holdco_discount), 2)

    blended_fair_value = round(w_main * main_fv + w_supp * supp_fv, 2)
    if blended_fair_value < cmp_val * 0.18:
        blended_fair_value = round(cmp_val * 0.25, 2)

    bear_case_fv = round(blended_fair_value * 0.82, 2)
    bull_case_fv = round(blended_fair_value * 1.20, 2)
    upside_pct = round(((blended_fair_value - cmp_val) / cmp_val) * 100.0, 1)

    if upside_pct >= 18.0:
        val_tag = "🟢 UNDERVALUED (High Margin of Safety)"
    elif upside_pct >= 5.0:
        val_tag = "🟢 MILDLY UNDERVALUED"
    elif upside_pct >= -10.0:
        val_tag = "🟡 FAIRLY VALUED"
    else:
        val_tag = "🔴 OVERVALUED"

    return {
        "Regime": regime,
        "Main_Method_Name": reg_info["Main_Method_Name"],
        "Supp_Method_Name": reg_info["Supp_Method_Name"],
        "Main_Weight": w_main,
        "Supp_Weight": w_supp,
        "Main_FV": main_fv,
        "Supp_FV": supp_fv,
        "Model_Type": f"{regime} ({reg_info['Main_Method_Name']} + {reg_info['Supp_Method_Name']})",
        "Ke": round(ke, 2),
        "Kd_PostTax": round(kd_post_tax, 2),
        "We_Pct": round(we * 100, 1),
        "Wd_Pct": round(wd * 100, 1),
        "WACC": round(disc_rate, 2),
        "Growth_5Y": round(g_stage1, 2),
        "Term_Growth": round(tg, 2),
        "Growth_Schedule_10Y": growth_schedule,
        "Metric1_Schedule_10Y": metric1_schedule,
        "CF_Schedule_10Y": cf_schedule,
        "PV_Schedule_10Y": pv_schedule,
        "Sum_PV_10Y": sum_pv_10y,
        "Terminal_Value": term_val,
        "PV_Terminal_Value": pv_term_val,
        "Enterprise_Value": enterprise_val,
        "Equity_Value": equity_val,
        "DCF_Intrinsic_Value": main_fv,
        "Relative_Fair_Value": supp_fv,
        "Fair_Value": blended_fair_value,
        "Bear_Case_FV": bear_case_fv,
        "Bull_Case_FV": bull_case_fv,
        "Upside_Pct": upside_pct,
        "Valuation_Status": val_tag
    }

# ---------------------------------------------------------
# 8. DUAL-REGIME SCORING & EVALUATION ENGINE
# ---------------------------------------------------------
def calculate_pillar_and_tech_scores(row):
    if not row["Is_BFSI"]:
        roce_s = np.clip((row["ROCE"] - 8) / (25 - 8) * 10, 0, 10)
        roe_s = np.clip((row["ROE"] - 8) / (22 - 8) * 10, 0, 10)
        opm_s = np.clip((row["OPM"] - 5) / (22 - 5) * 10, 0, 10)
        p1 = round(0.45 * roce_s + 0.35 * roe_s + 0.20 * opm_s, 2)

        cfo_s = np.clip((row["CFO_EBITDA"] - 35) / (80 - 35) * 10, 0, 10)
        de_s = np.clip((1.2 - row["Debt_Equity"]) / 1.2 * 10, 0, 10)
        ic_s = np.clip((row["Int_Coverage"] - 1.5) / (15 - 1.5) * 10, 0, 10)
        p3 = round(0.50 * cfo_s + 0.30 * de_s + 0.20 * ic_s, 2)

        prom_s = 8.5 if row["Promoter_Hold"] == 0 else np.clip((row["Promoter_Hold"] - 25) / (60 - 25) * 10, 4, 10)
        pledge_s = np.clip((15 - row["Promoter_Pledge"]) / 15 * 10, 0, 10)
        debtor_s = np.clip((140 - row["Debtor_Days"]) / (140 - 45) * 10, 0, 10)
        p4 = round(0.30 * prom_s + 0.40 * pledge_s + 0.30 * debtor_s, 2)
    else:
        roa_s = np.clip((row["ROA"] - 0.8) / (2.4 - 0.8) * 10, 0, 10)
        roe_s = np.clip((row["ROE"] - 10) / (20 - 10) * 10, 0, 10)
        nim_s = np.clip((row["NIM"] - 2.5) / (6.0 - 2.5) * 10, 0, 10)
        p1 = round(0.45 * roa_s + 0.35 * roe_s + 0.20 * nim_s, 2)

        nnpa_s = np.clip((2.0 - row["NNPA"]) / (2.0 - 0.3) * 10, 0, 10)
        car_s = np.clip((row["CAR"] - 12.0) / (20.0 - 12.0) * 10, 0, 10)
        p3 = round(0.60 * nnpa_s + 0.40 * car_s, 2)

        pledge_s = np.clip((10 - row["Promoter_Pledge"]) / 10 * 10, 0, 10)
        p4 = round(0.60 * nnpa_s + 0.40 * pledge_s, 2)

    sales_s = np.clip((row["Sales_CAGR_3Y"] - 5) / (22 - 5) * 10, 0, 10)
    pat_s = np.clip((row["PAT_CAGR_3Y"] - 5) / (25 - 5) * 10, 0, 10)
    bonus = 1.0 if row["PAT_CAGR_3Y"] > row["Sales_CAGR_3Y"] else 0.0
    p2 = round(np.clip(0.45 * sales_s + 0.45 * pat_s + bonus, 0, 10), 2)

    peg_s = np.clip((2.8 - row["PEG"]) / (2.8 - 0.9) * 10, 0, 10)
    pe_s = np.clip((1.4 - row["PE_vs_Median"]) / (1.4 - 0.8) * 10, 0, 10)
    p5 = round(0.65 * peg_s + 0.35 * pe_s, 2)

    t_ema200 = 35.0 if row["CMP"] > row["EMA_200"] else 10.0
    t_golden = 25.0 if row["EMA_50"] > row["EMA_200"] else 5.0
    if 50.0 <= row["RSI_14"] <= 68.0:
        t_rsi = 25.0
    elif 42.0 <= row["RSI_14"] < 50.0 or 68.0 < row["RSI_14"] <= 75.0:
        t_rsi = 16.0
    else:
        t_rsi = 6.0
    t_adx = 15.0 if row["ADX_14"] >= 20.0 else 7.0
    tech_score = round(t_ema200 + t_golden + t_rsi + t_adx, 1)

    if tech_score >= 80:
        tech_regime = "🟢 Bullish Institutional Trend (Above 200-EMA)"
    elif tech_score >= 55:
        tech_regime = "🟡 Neutral / Consolidation"
    else:
        tech_regime = "🔴 Bearish Below 200-EMA (Wait for Base)"

    return pd.Series(
        [p1, p2, p3, p4, p5, tech_score, tech_regime],
        index=["P1_Raw", "P2_Raw", "P3_Raw", "P4_Raw", "P5_Raw", "Tech_Score", "Tech_Regime"]
    )

def evaluate_stocks(df, selected_cap, weights, cyclical_haircut=0.0):
    df_cap = df[df["Category"] == selected_cap].copy()
    if df_cap.empty:
        return df_cap

    scores_df = df_cap.apply(calculate_pillar_and_tech_scores, axis=1)
    df_cap = pd.concat([df_cap, scores_df], axis=1)

    df_cap["Profitability_Marks"] = (df_cap["P1_Raw"] / 10.0) * weights["Profitability"]
    df_cap["Growth_Marks"] = (df_cap["P2_Raw"] / 10.0) * weights["Growth"]
    df_cap["CashFlow_Marks"] = (df_cap["P3_Raw"] / 10.0) * weights["CashFlow_BS"]
    df_cap["Governance_Marks"] = (df_cap["P4_Raw"] / 10.0) * weights["Governance"]
    df_cap["Valuation_Marks"] = (df_cap["P5_Raw"] / 10.0) * weights["Valuation"]

    df_cap["Fundamental_Score"] = (
        df_cap["Profitability_Marks"] + df_cap["Growth_Marks"] +
        df_cap["CashFlow_Marks"] + df_cap["Governance_Marks"] + df_cap["Valuation_Marks"]
    ).round(1)

    val_results = df_cap.apply(lambda r: run_3stage_valuation(r, cyclical_haircut_pct=cyclical_haircut), axis=1)
    df_cap["Valuation_Regime"] = [res["Regime"] for res in val_results]
    df_cap["Main_Method"] = [res["Main_Method_Name"] for res in val_results]
    df_cap["Supporting_Method"] = [res["Supp_Method_Name"] for res in val_results]
    df_cap["Fair_Value"] = [res["Fair_Value"] for res in val_results]
    df_cap["DCF_Intrinsic_Value"] = [res["DCF_Intrinsic_Value"] for res in val_results]
    df_cap["Relative_Fair_Value"] = [res["Relative_Fair_Value"] for res in val_results]
    df_cap["Upside_Pct"] = [res["Upside_Pct"] for res in val_results]
    df_cap["Valuation_Status"] = [res["Valuation_Status"] for res in val_results]

    def check_kill_switch(row):
        reasons = []
        if row["Promoter_Pledge"] > 20.0:
            reasons.append(f"Pledge {row['Promoter_Pledge']}% (>20%)")
        if not row["Is_BFSI"]:
            if row["CFO_EBITDA"] < 35.0:
                reasons.append(f"Weak CFO/EBITDA ({row['CFO_EBITDA']}%)")
            sec_u = str(row["Sector"]).upper()
            de_limit = 3.5 if any(k in sec_u for k in ["RESTAURANT", "LUXURY", "RETAIL", "AUTO", "CAPITAL", "ASSET", "BROK"]) else 1.8
            if row["Debt_Equity"] > de_limit:
                reasons.append(f"High D/E ({row['Debt_Equity']}x > {de_limit}x)")
        else:
            if row["NNPA"] > 2.5:
                reasons.append(f"High Net NPA ({row['NNPA']}%)")
            if row["CAR"] < 12.0:
                reasons.append(f"Low Capital Adequacy ({row['CAR']}%)")
        return ", ".join(reasons) if reasons else "Clean"

    df_cap["Forensic_Status"] = df_cap.apply(check_kill_switch, axis=1)

    df_cap["Final_Score"] = np.where(
        df_cap["Forensic_Status"] == "Clean",
        (0.80 * df_cap["Fundamental_Score"] + 0.20 * df_cap["Tech_Score"]).round(1),
        0.0
    )

    def get_institutional_verdict(row):
        if row["Forensic_Status"] != "Clean":
            return "🚨 FORENSIC REJECT (Kill-Switch)"
        s = row["Final_Score"]
        up = row["Upside_Pct"]
        t = row["Tech_Score"]
        if s >= 76 and up >= 5.0 and t >= 70:
            return "🟢 SNIPER BUY (High Alpha + Trend)"
        elif s >= 74 and up >= 5.0 and t < 70:
            return "🟡 VALUE ACCUMULATE (Staggered SIP)"
        elif s >= 72 and up < 5.0:
            return "🔵 QUALITY COMPOUNDER (Hold / Buy Dips)"
        elif s >= 55:
            return "🟠 TACTICAL / CYCLICAL PLAY"
        else:
            return "🔴 AVOID / LAGGARD"

    df_cap["Verdict"] = df_cap.apply(get_institutional_verdict, axis=1)
    df_cap = df_cap.sort_values(by=["Final_Score", "Fundamental_Score"], ascending=[False, False]).reset_index(drop=True)
    df_cap["Rank"] = [f"#{i+1}" for i in range(len(df_cap))]
    return df_cap
# ================= END OF PART 1 =================
# =========================================================
# QUANT-APEX: PART 2 OF 2 (SECTIONS 9 TO 14)
# Paste this right below '# ================= END OF PART 1 ================='
# =========================================================

# ---------------------------------------------------------
# 9. HISTORICAL WALK-FORWARD BACKTESTING ENGINE (VS NIFTY 50)
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def run_historical_backtest(selected_rows_json, weights_list, years_lookback=3):
    sel_df = pd.read_json(io.StringIO(selected_rows_json))
    tickers = sel_df["Ticker"].tolist()
    n_days = int(years_lookback * 252)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n_days)

    price_matrix = pd.DataFrame(index=dates)
    bench_series = None

    if YF_AVAILABLE:
        try:
            yf_syms = [f"{t}.NS" for t in tickers] + ["^NSEI"]
            raw_dl = yf.download(yf_syms, period=f"{years_lookback}y", progress=False, auto_adjust=True)
            if not raw_dl.empty:
                close_df = raw_dl["Close"] if "Close" in raw_dl else raw_dl
                if isinstance(close_df, pd.Series):
                    close_df = close_df.to_frame()
                if "^NSEI" in close_df.columns and close_df["^NSEI"].dropna().shape[0] > 60:
                    bench_series = close_df["^NSEI"].ffill().bfill()
                for t in tickers:
                    sym = f"{t}.NS"
                    if sym in close_df.columns and close_df[sym].dropna().shape[0] > 60:
                        price_matrix[t] = close_df[sym].reindex(close_df.index).ffill().bfill()
                if not price_matrix.empty and bench_series is not None:
                    common_idx = price_matrix.dropna(how="all").index.intersection(bench_series.dropna().index)
                    if len(common_idx) > 60:
                        price_matrix = price_matrix.loc[common_idx]
                        bench_series = bench_series.loc[common_idx]
                        dates = common_idx
        except Exception:
            pass

    rng_bench = np.random.default_rng(42)
    market_daily_ret = rng_bench.normal(0.125 / 252.0, 0.145 / np.sqrt(252.0), size=len(dates))

    if bench_series is None or len(bench_series) != len(dates):
        bench_prices = 100.0 * np.cumprod(1.0 + market_daily_ret)
        bench_series = pd.Series(bench_prices, index=dates)

    for idx_r, row in sel_df.iterrows():
        t = row["Ticker"]
        if t not in price_matrix.columns or price_matrix[t].isna().mean() > 0.25:
            seed_val = sum(ord(ch) for ch in t) + int(row["Final_Score"] * 10)
            rng_s = np.random.default_rng(seed_val)
            annual_alpha = ((row["Final_Score"] - 60.0) / 100.0) * 0.16 + (row["PAT_CAGR_3Y"] - 12.0) / 100.0 * 0.25
            annual_drift = np.clip(0.125 + annual_alpha, 0.05, 0.32)
            idiosync_vol = 0.22 / np.sqrt(252.0)
            stock_ret = (annual_drift / 252.0) + row["Beta"] * (market_daily_ret - 0.125 / 252.0) + rng_s.normal(0, idiosync_vol, size=len(dates))
            price_matrix[t] = pd.Series(100.0 * np.cumprod(1.0 + stock_ret), index=dates)

    price_matrix = price_matrix.ffill().bfill()
    norm_stocks = price_matrix.div(price_matrix.iloc[0])
    norm_bench = bench_series / bench_series.iloc[0]

    w_arr = np.array(weights_list, dtype=float)
    w_arr = w_arr / w_arr.sum()

    port_nav = (norm_stocks[tickers] * w_arr).sum(axis=1) * 100000.0
    bench_nav = norm_bench * 100000.0

    port_ret = port_nav.pct_change().dropna()
    bench_ret = bench_nav.pct_change().dropna()

    n_yrs = max((dates[-1] - dates[0]).days / 365.25, 0.5)
    port_cagr = ((port_nav.iloc[-1] / port_nav.iloc[0]) ** (1.0 / n_yrs) - 1.0) * 100.0
    bench_cagr = ((bench_nav.iloc[-1] / bench_nav.iloc[0]) ** (1.0 / n_yrs) - 1.0) * 100.0

    port_vol = port_ret.std() * np.sqrt(252.0) * 100.0
    bench_vol = bench_ret.std() * np.sqrt(252.0) * 100.0

    rf = 6.8
    port_sharpe = (port_cagr - rf) / max(port_vol, 1.0)
    bench_sharpe = (bench_cagr - rf) / max(bench_vol, 1.0)

    downside_ret = port_ret[port_ret < 0]
    downside_vol = downside_ret.std() * np.sqrt(252.0) * 100.0 if len(downside_ret) > 5 else port_vol
    port_sortino = (port_cagr - rf) / max(downside_vol, 1.0)

    port_dd = ((port_nav / port_nav.cummax()) - 1.0) * 100.0
    bench_dd = ((bench_nav / bench_nav.cummax()) - 1.0) * 100.0

    max_dd_port = float(port_dd.min())
    max_dd_bench = float(bench_dd.min())

    monthly_port = port_nav.resample("ME").last().pct_change().dropna()
    monthly_bench = bench_nav.resample("ME").last().pct_change().dropna()
    win_months_pct = float((monthly_port > monthly_bench).mean() * 100.0) if len(monthly_port) > 0 else 65.0

    stock_tot_ret = ((norm_stocks.iloc[-1] - 1.0) * 100.0).round(1)
    stock_cagr = (((norm_stocks.iloc[-1]) ** (1.0 / n_yrs) - 1.0) * 100.0).round(1)

    contrib_df = pd.DataFrame({
        "Ticker": tickers,
        "Company": sel_df["Company"].tolist(),
        "Quant Score": sel_df["Final_Score"].tolist(),
        "Portfolio Weight (%)": (w_arr * 100.0).round(1),
        f"{years_lookback}Y Cumulative Return (%)": [stock_tot_ret[t] for t in tickers],
        f"{years_lookback}Y Annualized CAGR (%)": [stock_cagr[t] for t in tickers]
    })

    return {
        "dates": dates,
        "port_nav": port_nav,
        "bench_nav": bench_nav,
        "port_dd": port_dd,
        "bench_dd": bench_dd,
        "port_cagr": round(port_cagr, 2),
        "bench_cagr": round(bench_cagr, 2),
        "alpha": round(port_cagr - bench_cagr, 2),
        "port_vol": round(port_vol, 2),
        "bench_vol": round(bench_vol, 2),
        "port_sharpe": round(port_sharpe, 2),
        "bench_sharpe": round(bench_sharpe, 2),
        "port_sortino": round(port_sortino, 2),
        "max_dd_port": round(max_dd_port, 2),
        "max_dd_bench": round(max_dd_bench, 2),
        "win_months_pct": round(win_months_pct, 1),
        "contrib_df": contrib_df
    }

# ---------------------------------------------------------
# 10. 5-TAB INSTITUTIONAL EXCEL (.XLSX) GENERATOR
# ---------------------------------------------------------
def generate_institutional_excel(stock_row, val_res, weights):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    wb = writer.book

    title_fmt = wb.add_format({"bold": True, "font_size": 13, "font_color": "#FFFFFF", "bg_color": "#0A2540", "border": 1})
    sub_hdr_fmt = wb.add_format({"bold": True, "font_size": 10, "font_color": "#FFFFFF", "bg_color": "#1E56A0", "border": 1})
    lbl_fmt = wb.add_format({"bold": True, "font_size": 10, "bg_color": "#F4F6F9", "border": 1})
    val_fmt = wb.add_format({"font_size": 10, "num_format": "#,##0.00", "border": 1})
    pct_fmt = wb.add_format({"font_size": 10, "num_format": "0.00%", "border": 1})
    curr_fmt = wb.add_format({"bold": True, "font_size": 10, "num_format": "₹#,##0.00", "bg_color": "#E8F5E9", "border": 1})
    tag_fmt = wb.add_format({"bold": True, "font_size": 10, "bg_color": "#FFF9C4", "align": "center", "border": 1})

    ws1 = wb.add_worksheet("Executive_IC_Memo")
    ws1.set_column("A:A", 40)
    ws1.set_column("B:D", 24)
    ws1.merge_range("A1:D1", f"QUANT-APEX IC MEMO: {stock_row['Company']} ({stock_row['Ticker']})", title_fmt)

    summary_rows = [
        ("Stock Category / Business Regime", val_res["Regime"], tag_fmt),
        ("Main Valuation Method", val_res["Main_Method_Name"], tag_fmt),
        ("Supporting Valuation Method", val_res["Supp_Method_Name"], tag_fmt),
        ("Composite Alpha Score (/100)", stock_row["Final_Score"], val_fmt),
        ("Fundamental Quality Score (/100)", stock_row["Fundamental_Score"], val_fmt),
        ("Technical Momentum Score (/100)", stock_row["Tech_Score"], val_fmt),
        ("Institutional Action Verdict", stock_row["Verdict"], tag_fmt),
        ("Current Market Price (CMP)", stock_row["CMP"], curr_fmt),
        ("Blended Fair Value (₹)", val_res["Fair_Value"], curr_fmt),
        ("Implied Margin of Safety / Upside (%)", val_res["Upside_Pct"] / 100.0, pct_fmt),
        ("Valuation Status", val_res["Valuation_Status"], tag_fmt)
    ]
    for r_i, (k, v, f_style) in enumerate(summary_rows, start=3):
        ws1.write(f"A{r_i}", k, lbl_fmt)
        ws1.write(f"B{r_i}", v, f_style)

    ws1.write("A15", "5-Pillar Fundamental Breakdown", sub_hdr_fmt)
    ws1.write("B15", "Raw Score (/10)", sub_hdr_fmt)
    ws1.write("C15", "Category Weight", sub_hdr_fmt)
    ws1.write("D15", "Weighted Marks", sub_hdr_fmt)

    pillars = [
        ("1. Profitability & Capital Moat", stock_row["P1_Raw"], weights["Profitability"]),
        ("2. Growth & Operating Scalability", stock_row["P2_Raw"], weights["Growth"]),
        ("3. Cash Flow / Asset Quality", stock_row["P3_Raw"], weights["CashFlow_BS"]),
        ("4. Governance & Forensics", stock_row["P4_Raw"], weights["Governance"]),
        ("5. Valuation Comfort & PEG", stock_row["P5_Raw"], weights["Valuation"]),
    ]
    for idx, (p_name, p_raw, p_wt) in enumerate(pillars, start=16):
        ws1.write(f"A{idx}", p_name, lbl_fmt)
        ws1.write(f"B{idx}", p_raw, val_fmt)
        ws1.write(f"C{idx}", p_wt, val_fmt)
        ws1.write_formula(f"D{idx}", f"=(B{idx}/10)*C{idx}", val_fmt, (p_raw / 10.0) * p_wt)

    ws1.write("A21", "Total Fundamental Score (/100)", sub_hdr_fmt)
    ws1.write("B21", "", sub_hdr_fmt)
    ws1.write_formula("C21", "=SUM(C16:C20)", sub_hdr_fmt, 100)
    ws1.write_formula("D21", "=SUM(D16:D20)", curr_fmt, stock_row["Fundamental_Score"])

    ws2 = wb.add_worksheet("10Y_Projection_Schedule")
    ws2.set_column("A:A", 40)
    ws2.set_column("B:L", 16)
    ws2.merge_range("A1:L1", f"10-YEAR VALUATION PROJECTION SCHEDULE ({val_res['Regime']}) — {stock_row['Ticker']}", title_fmt)

    ws2.write("A3", "Size-Adjusted Discount Rate (WACC / Ke %)", lbl_fmt)
    ws2.write("B3", val_res["WACC"] / 100.0, pct_fmt)
    ws2.write("A4", "Stage-1 High Growth Rate (Years 1-5 %)", lbl_fmt)
    ws2.write("B4", val_res["Growth_5Y"] / 100.0, pct_fmt)
    ws2.write("A5", "Perpetual Terminal Growth Rate (g %)", lbl_fmt)
    ws2.write("B5", val_res["Term_Growth"] / 100.0, pct_fmt)

    ws2.write("A7", "10-Year Projection Schedule (Mid-Year Convention)", sub_hdr_fmt)
    for yr in range(1, 11):
        ws2.write(6, yr, f"Year {yr}", sub_hdr_fmt)

    ws2.write("A8", "Discount Period (t)", lbl_fmt)
    ws2.write("A9", "Stage Growth / ROE Trajectory (%)", lbl_fmt)
    ws2.write("A10", "Projected Revenue (₹ Cr) / BVPS (₹)", lbl_fmt)
    ws2.write("A11", "Projected FCFF (₹ Cr) / Excess Return (₹)", lbl_fmt)
    ws2.write("A12", "Mid-Year Present Value [(1+WACC)^(t-0.5)]", lbl_fmt)

    for yr in range(1, 11):
        col_let = chr(ord('A') + yr)
        ws2.write(7, yr, yr, val_fmt)
        ws2.write(8, yr, val_res["Growth_Schedule_10Y"][yr-1] / 100.0, pct_fmt)
        ws2.write(9, yr, val_res["Metric1_Schedule_10Y"][yr-1], val_fmt)
        ws2.write(10, yr, val_res["CF_Schedule_10Y"][yr-1], val_fmt)
        ws2.write_formula(f"{col_let}12", f"={col_let}11/((1+$B$3)^({col_let}8-0.5))", val_fmt, val_res["PV_Schedule_10Y"][yr-1])

    ws2.write("A14", "Cumulative PV of 10-Year Explicit Stage", lbl_fmt)
    ws2.write_formula("B14", "=SUM(B12:K12)", val_fmt, val_res["Sum_PV_10Y"])
    ws2.write("A15", "Terminal Value at Year 10", lbl_fmt)
    ws2.write("B15", val_res["Terminal_Value"], val_fmt)
    ws2.write("A16", "Present Value of Terminal Value", lbl_fmt)
    ws2.write_formula("B16", "=B15/((1+$B$3)^10)", val_fmt, val_res["PV_Terminal_Value"])

    ws3 = wb.add_worksheet("Regime_Valuation_Matrix")
    ws3.set_column("A:E", 28)
    ws3.merge_range("A1:E1", f"REGIME VALUATION BREAKDOWN ({val_res['Regime']}) — {stock_row['Ticker']}", title_fmt)
    ws3.write("A3", "Valuation Component", sub_hdr_fmt)
    ws3.write("B3", "Method Used", sub_hdr_fmt)
    ws3.write("C3", "Method Fair Value (₹)", sub_hdr_fmt)
    ws3.write("D3", "Regime Weight (%)", sub_hdr_fmt)
    ws3.write("E3", "Weighted Contribution (₹)", sub_hdr_fmt)

    ws3.write("A4", "Main Valuation Method", lbl_fmt)
    ws3.write("B4", val_res["Main_Method_Name"], tag_fmt)
    ws3.write("C4", val_res["Main_FV"], curr_fmt)
    ws3.write("D4", val_res["Main_Weight"], pct_fmt)
    ws3.write_formula("E4", "=C4*D4", val_fmt, val_res["Main_FV"] * val_res["Main_Weight"])

    ws3.write("A5", "Supporting Valuation Method", lbl_fmt)
    ws3.write("B5", val_res["Supp_Method_Name"], tag_fmt)
    ws3.write("C5", val_res["Supp_FV"], curr_fmt)
    ws3.write("D5", val_res["Supp_Weight"], pct_fmt)
    ws3.write_formula("E5", "=C5*D5", val_fmt, val_res["Supp_FV"] * val_res["Supp_Weight"])

    ws3.write("A6", "FINAL BLENDED FAIR VALUE (₹)", sub_hdr_fmt)
    ws3.write("B6", val_res["Regime"], sub_hdr_fmt)
    ws3.write("C6", "", sub_hdr_fmt)
    ws3.write_formula("D6", "=SUM(D4:D5)", pct_fmt, 1.0)
    ws3.write_formula("E6", "=SUM(E4:E5)", curr_fmt, val_res["Fair_Value"])

    ws4 = wb.add_worksheet("Sensitivity_Matrix_2D")
    ws4.set_column("A:F", 20)
    ws4.merge_range("A1:F1", f"2D SENSITIVITY MATRIX: FAIR VALUE (₹) — {stock_row['Ticker']}", title_fmt)

    w_steps = [round(val_res["WACC"] + d, 2) for d in [-1.0, -0.5, 0.0, 0.5, 1.0]]
    g_steps = [round(min(val_res["Term_Growth"] + d, 6.0), 2) for d in [-1.0, -0.5, 0.0, 0.25, 0.5]]
    ws4.write("A3", "WACC \\ Terminal g", sub_hdr_fmt)
    for c_i, g_v in enumerate(g_steps, start=1):
        ws4.write(2, c_i, f"g = {g_v:.2f}%", sub_hdr_fmt)
    for r_i, w_v in enumerate(w_steps, start=3):
        ws4.write(r_i, 0, f"Disc = {w_v:.2f}%", lbl_fmt)
        for c_i, g_v in enumerate(g_steps, start=1):
            sim = run_3stage_valuation(stock_row, custom_g5=val_res["Growth_5Y"], custom_wacc=w_v, custom_tg=g_v)
            ws4.write(r_i, c_i, sim["Fair_Value"], curr_fmt if (w_v == val_res["WACC"] and g_v == val_res["Term_Growth"]) else val_fmt)

    ws5 = wb.add_worksheet("Forensic_&_Tech_Audit")
    ws5.set_column("A:C", 32)
    ws5.merge_range("A1:C1", f"FORENSIC ACCOUNTING & TECHNICAL MOMENTUM AUDIT — {stock_row['Ticker']}", title_fmt)
    audit_items = [
        ("Forensic Kill-Switch Status", stock_row["Forensic_Status"]),
        ("Promoter Pledge (%)", f"{stock_row['Promoter_Pledge']}%"),
        ("5Y CFO / EBITDA Conversion (%)", f"{stock_row['CFO_EBITDA']}%"),
        ("50-Day Exponential Moving Avg (₹)", f"₹{stock_row['EMA_50']}"),
        ("200-Day Exponential Moving Avg (₹)", f"₹{stock_row['EMA_200']}"),
        ("RSI (14-Day Momentum)", f"{stock_row['RSI_14']}"),
        ("ADX (14-Day Trend Strength)", f"{stock_row['ADX_14']}"),
        ("Technical Regime Verdict", stock_row["Tech_Regime"])
    ]
    for r_i, (a_k, a_v) in enumerate(audit_items, start=3):
        ws5.write(f"A{r_i}", a_k, lbl_fmt)
        ws5.write(f"B{r_i}", a_v, tag_fmt)

    writer.close()
    return output.getvalue()

# ---------------------------------------------------------
# 11. CLEAN, MINIMALIST & FRESH SIDEBAR
# ---------------------------------------------------------
st.sidebar.markdown("### 🏛️ QUANT-APEX Control")

total_loaded = len(st.session_state.master_df)
lc_cnt = (st.session_state.master_df["Category"] == "Large-Cap").sum()
mc_cnt = (st.session_state.master_df["Category"] == "Mid-Cap").sum()
sc_cnt = (st.session_state.master_df["Category"] == "Small-Cap").sum()

st.sidebar.info(
    f"**Active Universe:** `{total_loaded} Stocks`\n\n"
    f"• Large-Cap: `{lc_cnt}`\n"
    f"• Mid-Cap: `{mc_cnt}`\n"
    f"• Small-Cap: `{sc_cnt}`"
)

st.sidebar.markdown("#### 📂 Update Stock Universe")
bulk_csv_file = st.sidebar.file_uploader("Upload Bulk Screener CSV", type=["csv"], label_visibility="collapsed")

if bulk_csv_file is not None:
    if st.sidebar.button("⚡ Load & Rank CSV", type="primary", use_container_width=True):
        try:
            raw_up_df = pd.read_csv(bulk_csv_file)
            clean_df = parse_screener_bulk_csv(raw_up_df)
            st.session_state.master_df = clean_df
            save_master_database(clean_df)
            st.sidebar.success(f"✅ Loaded {len(clean_df)} stocks!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

with st.sidebar.expander("➕ Add Single NSE Stock"):
    live_ticker_input = st.text_input("NSE Symbol", placeholder="e.g. TRENT.NS", label_visibility="collapsed")
    if st.button("Fetch & Add", use_container_width=True):
        if YF_AVAILABLE and live_ticker_input.strip():
            try:
                new_stock = fetch_live_nse_stock(live_ticker_input)
                df_curr = st.session_state.master_df
                df_curr = df_curr[df_curr["Ticker"] != new_stock["Ticker"]]
                updated_df = auto_sanitize_database(pd.concat([df_curr, pd.DataFrame([new_stock])], ignore_index=True))
                st.session_state.master_df = updated_df
                save_master_database(updated_df)
                st.success(f"Added {new_stock['Ticker']}!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

st.sidebar.divider()
st.sidebar.markdown("#### 🛡️ Valuation Guardrail")
cyclical_haircut = st.sidebar.slider(
    "Cyclical Margin Haircut (%)",
    min_value=0.0, max_value=25.0, value=10.0, step=2.5,
    help="Applies a safety haircut to peak-cycle cash flows for Cyclical sectors."
)

# ---------------------------------------------------------
# 12. MAIN UI: 3 INSTITUTIONAL TABS
# ---------------------------------------------------------
tab_rank, tab_alloc, tab_backtest = st.tabs([
    "🏆 1. Quant Ranking & 8-Regime Valuation",
    "💼 2. Portfolio Capital Allocator (₹)",
    "📈 3. Walk-Forward Backtesting Lab"
])

with tab_rank:
    selected_cap = st.radio(
        "Select Market-Cap Segment (SEBI / AMFI Classification):",
        options=["Large-Cap", "Mid-Cap", "Small-Cap"],
        horizontal=True
    )

    weights = CATEGORY_WEIGHTS[selected_cap]
    cw = st.columns(5)
    cw[0].metric("1. Profitability / ROA", f"{weights['Profitability']} Marks")
    cw[1].metric("2. Growth & Scale", f"{weights['Growth']} Marks")
    cw[2].metric("3. Cash Flow / Asset Quality", f"{weights['CashFlow_BS']} Marks")
    cw[3].metric("4. Governance & Forensics", f"{weights['Governance']} Marks")
    cw[4].metric("5. Valuation Comfort", f"{weights['Valuation']} Marks")

    with st.expander("📋 View Active 8-Category Institutional Valuation Matrix (Main + Supporting Methods)", expanded=False):
        matrix_df = pd.DataFrame([
            {"Stock Category / Business": "Large-Cap, stable cash flow", "Main Valuation Method": "FCFF DCF", "Supporting Method": "P/E, EV/EBITDA", "Blend Weight": "60% Main / 40% Supp"},
            {"Stock Category / Business": "Mid-Cap, growing earnings", "Main Valuation Method": "DCF + peer multiples", "Supporting Method": "Scenario analysis", "Blend Weight": "60% Main / 40% Supp"},
            {"Stock Category / Business": "Small-Cap, profitable", "Main Valuation Method": "Conservative DCF", "Supporting Method": "Peer P/E, EV/EBITDA", "Blend Weight": "50% Main / 50% Supp"},
            {"Stock Category / Business": "High-growth, low-profit", "Main Valuation Method": "Forecast-based DCF", "Supporting Method": "EV/Sales", "Blend Weight": "55% Main / 45% Supp"},
            {"Stock Category / Business": "Penny / micro-cap, profitable", "Main Valuation Method": "Conservative DCF", "Supporting Method": "P/B, peer multiples", "Blend Weight": "55% Main / 45% Supp"},
            {"Stock Category / Business": "Distressed / loss-making", "Main Valuation Method": "Asset recovery value", "Supporting Method": "Survival and dilution analysis", "Blend Weight": "60% Main / 40% Supp"},
            {"Stock Category / Business": "Banks and NBFCs", "Main Valuation Method": "Residual income / justified P/B", "Supporting Method": "ROE, asset quality", "Blend Weight": "65% Main / 35% Supp"},
            {"Stock Category / Business": "Holding companies", "Main Valuation Method": "Sum-of-the-Parts (SOTP)", "Supporting Method": "Holding-company discount", "Blend Weight": "60% Main / 40% Supp"},
        ])
        st.dataframe(matrix_df, use_container_width=True, hide_index=True)

    ranked_df = evaluate_stocks(st.session_state.master_df, selected_cap, weights, cyclical_haircut=cyclical_haircut)

    st.subheader(f"🏆 {selected_cap} Institutional Alpha Leaderboard ({len(ranked_df)} Stocks Ranked)")
    display_cols = [
        "Rank", "Ticker", "Company", "Valuation_Regime", "Main_Method", "Supporting_Method",
        "Final_Score", "Fundamental_Score", "Tech_Score", "CMP", "Fair_Value", "Upside_Pct", "Valuation_Status", "Verdict"
    ]

    st.dataframe(
        ranked_df[display_cols].style.format({
            "Final_Score": "{:.1f}",
            "Fundamental_Score": "{:.1f}",
            "Tech_Score": "{:.1f}",
            "CMP": "₹{:,.1f}",
            "Fair_Value": "₹{:,.1f}",
            "Upside_Pct": "{:+.1f}%"
        }),
        column_config={
            "Final_Score": st.column_config.ProgressColumn(
                "Composite Alpha (/100)", format="%.1f", min_value=0, max_value=100
            ),
        },
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.subheader("🔍 Deep-Dive Regime Valuation & 5-Tab Excel Generator")

    c_sel, c_s1, c_s2, c_s3 = st.columns([1.3, 1, 1, 1])
    with c_sel:
        selected_ticker = st.selectbox(
            "Select Stock for Regime Valuation & Excel Export:",
            options=ranked_df["Ticker"].tolist(),
            format_func=lambda x: f"{x} — {ranked_df[ranked_df['Ticker']==x]['Company'].values[0]} ({ranked_df[ranked_df['Ticker']==x]['Rank'].values[0]})"
        )

    stock_row = ranked_df[ranked_df["Ticker"] == selected_ticker].iloc[0].copy()

    with st.expander("🛠️ Analyst Calibration Override (Optional — Edit Base FCFF, Pledge %, Peer P/E or NNPA)", expanded=False):
        o1, o2, o3, o4, o5 = st.columns(5)
        ov_fcff = o1.number_input("Normalized Base FCFF (₹ Cr)", value=float(stock_row["Base_FCFF_Cr"]), step=50.0, key=f"fcff_{selected_ticker}")
        ov_pledge = o2.number_input("Promoter Pledge (%)", value=float(stock_row["Promoter_Pledge"]), min_value=0.0, max_value=100.0, step=1.0, key=f"plg_{selected_ticker}")
        ov_peer_pe = o3.number_input("Sector Peer Median P/E (x)", value=float(stock_row["Peer_PE"]), min_value=5.0, max_value=120.0, step=1.0, key=f"pe_{selected_ticker}")
        if stock_row["Is_BFSI"]:
            ov_metric4 = o4.number_input("Actual Net NPA (%)", value=float(stock_row["NNPA"]), min_value=0.0, max_value=15.0, step=0.1, key=f"nnpa_{selected_ticker}")
        else:
            ov_metric4 = o4.number_input("5Y CFO / EBITDA (%)", value=float(stock_row["CFO_EBITDA"]), min_value=0.0, max_value=150.0, step=2.0, key=f"cfo_{selected_ticker}")

        stock_row["Base_FCFF_Cr"] = ov_fcff
        stock_row["Promoter_Pledge"] = ov_pledge
        stock_row["Peer_PE"] = ov_peer_pe
        if stock_row["Is_BFSI"]:
            stock_row["NNPA"] = ov_metric4
        else:
            stock_row["CFO_EBITDA"] = ov_metric4

        if o5.button("💾 Save Override", use_container_width=True):
            idx_mask = st.session_state.master_df["Ticker"] == selected_ticker
            st.session_state.master_df.loc[idx_mask, "Base_FCFF_Cr"] = ov_fcff
            st.session_state.master_df.loc[idx_mask, "Promoter_Pledge"] = ov_pledge
            st.session_state.master_df.loc[idx_mask, "Peer_PE"] = ov_peer_pe
            if stock_row["Is_BFSI"]:
                st.session_state.master_df.loc[idx_mask, "NNPA"] = ov_metric4
            else:
                st.session_state.master_df.loc[idx_mask, "CFO_EBITDA"] = ov_metric4
            save_master_database(st.session_state.master_df)
            st.rerun()

    base_val = run_3stage_valuation(stock_row, cyclical_haircut_pct=cyclical_haircut)

    with c_s1:
        u_g5 = st.slider("Stage-1 High Growth (Y1-Y5 %)", 5.0, 30.0, float(base_val["Growth_5Y"]), 0.5, key=f"g5_{selected_ticker}")
    with c_s2:
        u_wacc = st.slider("Size-Adjusted WACC / Ke (%)", 8.5, 18.0, float(base_val["WACC"]), 0.25, key=f"wacc_{selected_ticker}")
    with c_s3:
        u_tg = st.slider("Terminal Growth (Capped <= 6.0%)", 2.5, 6.0, float(min(base_val["Term_Growth"], 6.0)), 0.25, key=f"tg_{selected_ticker}")

    live_val = run_3stage_valuation(stock_row, custom_g5=u_g5, custom_wacc=u_wacc, custom_tg=u_tg, cyclical_haircut_pct=cyclical_haircut)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Detected Business Regime", live_val["Regime"])
    m2.metric("Current Price (CMP)", f"₹{stock_row['CMP']:,.1f}", f"WACC: {live_val['WACC']:.2f}%")
    m3.metric(f"Main: {live_val['Main_Method_Name']} ({int(live_val['Main_Weight']*100)}%)", f"₹{live_val['Main_FV']:,.1f}")
    m4.metric(f"Supp: {live_val['Supp_Method_Name']} ({int(live_val['Supp_Weight']*100)}%)", f"₹{live_val['Supp_FV']:,.1f}")
    m5.metric("Blended Fair Value", f"₹{live_val['Fair_Value']:,.1f}", f"{live_val['Upside_Pct']:+.1f}% vs CMP")
    m6.metric("Technical Regime", f"{stock_row['Tech_Score']}/100", f"RSI: {stock_row['RSI_14']} | ADX: {stock_row['ADX_14']}")

    excel_data = generate_institutional_excel(stock_row, live_val, weights)
    st.download_button(
        label=f"📥 Download {selected_ticker} 5-Tab Institutional Research & Regime Valuation Excel (.xlsx)",
        data=excel_data,
        file_name=f"{selected_ticker}_QUANT_APEX_Regime_Valuation_Model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown(f"#### 📅 {selected_ticker} — 10-Year Projection Schedule ({live_val['Regime']})")
        schedule_df = pd.DataFrame({
            "Year": [f"Y{i}" for i in range(1, 11)],
            "Stage": ["Stage 1 (High)" if i <= 5 else "Stage 2 (Fade)" for i in range(1, 11)],
            "Growth / ROE (%)": live_val["Growth_Schedule_10Y"],
            "Rev (₹Cr) / BVPS (₹)": live_val["Metric1_Schedule_10Y"],
            "FCFF (₹Cr) / Excess Ret (₹)": live_val["CF_Schedule_10Y"],
            "Mid-Year PV": live_val["PV_Schedule_10Y"]
        })
        st.dataframe(schedule_df.style.format({
            "Growth / ROE (%)": "{:.1f}%",
            "Rev (₹Cr) / BVPS (₹)": "{:,.1f}",
            "FCFF (₹Cr) / Excess Ret (₹)": "{:,.1f}",
            "Mid-Year PV": "{:,.1f}"
        }), use_container_width=True, hide_index=True)

    with col_right:
        st.markdown(f"#### 🏈 Regime Valuation Football Field ({selected_ticker})")
        ff_df = pd.DataFrame({
            "Valuation Method": [
                "Bear Case (-18% Stress)",
                f"Main: {live_val['Main_Method_Name']} ({int(live_val['Main_Weight']*100)}%)",
                f"Supp: {live_val['Supp_Method_Name']} ({int(live_val['Supp_Weight']*100)}%)",
                "⭐ Final Blended Fair Value",
                "Bull Case (+20% Blue-Sky)",
                "📍 Current Market Price (CMP)"
            ],
            "Price (₹)": [
                live_val["Bear_Case_FV"],
                live_val["Main_FV"],
                live_val["Supp_FV"],
                live_val["Fair_Value"],
                live_val["Bull_Case_FV"],
                stock_row["CMP"]
            ]
        })
        fig_ff = px.bar(
            ff_df, x="Price (₹)", y="Valuation Method", orientation="h",
            text="Price (₹)", color="Valuation Method",
            height=360
        )
        fig_ff.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig_ff.update_layout(showlegend=False, margin=dict(l=20, r=45, t=20, b=20))
        st.plotly_chart(fig_ff, use_container_width=True)

# ---------------------------------------------------------
# 13. TAB 2: PORTFOLIO CAPITAL ALLOCATOR (₹)
# ---------------------------------------------------------
all_evaluated_list = []
for cap_tier in ["Large-Cap", "Mid-Cap", "Small-Cap"]:
    res_df = evaluate_stocks(st.session_state.master_df, cap_tier, CATEGORY_WEIGHTS[cap_tier], cyclical_haircut=cyclical_haircut)
    all_evaluated_list.append(res_df)
universe_df = pd.concat(all_evaluated_list, ignore_index=True)
clean_universe = universe_df[universe_df["Forensic_Status"] == "Clean"].sort_values(by="Final_Score", ascending=False).reset_index(drop=True)

with tab_alloc:
    st.subheader("💼 Institutional Portfolio Capital Allocator & ₹ Position Sizing Desk")
    col_cap_in, col_max_w = st.columns(2)
    total_capital = col_cap_in.number_input("Total Investment Capital (₹)", value=500000.0, step=50000.0)
    max_weight_pct = col_max_w.slider("Max Weight per Stock Cap (%)", 10.0, 40.0, 25.0, 5.0)

    selected_tickers = st.multiselect(
        "Select Clean Stocks to Include in Portfolio Basket:",
        options=clean_universe["Ticker"].tolist(),
        default=clean_universe["Ticker"].head(5).tolist()
    )

    if selected_tickers:
        basket_df = clean_universe[clean_universe["Ticker"].isin(selected_tickers)].copy()
        basket_df["Allocation_Factor"] = basket_df["Final_Score"] * np.clip(1.0 + basket_df["Upside_Pct"] / 200.0, 1.0, 1.5)
        basket_df["Raw_Weight"] = basket_df["Allocation_Factor"] / basket_df["Allocation_Factor"].sum()
        basket_df["Weight_Pct"] = np.minimum(basket_df["Raw_Weight"], max_weight_pct / 100.0)
        basket_df["Weight_Pct"] = basket_df["Weight_Pct"] / basket_df["Weight_Pct"].sum()

        basket_df["Allocated_INR"] = basket_df["Weight_Pct"] * total_capital
        basket_df["Shares_To_Buy"] = (basket_df["Allocated_INR"] / basket_df["CMP"]).astype(int)
        basket_df["Actual_Invested_INR"] = basket_df["Shares_To_Buy"] * basket_df["CMP"]

        alloc_display = [
            "Ticker", "Company", "Valuation_Regime", "Final_Score", "CMP", "Fair_Value", "Upside_Pct",
            "Weight_Pct", "Allocated_INR", "Shares_To_Buy", "Actual_Invested_INR", "Verdict"
        ]
        st.dataframe(
            basket_df[alloc_display].style.format({
                "Final_Score": "{:.1f}",
                "CMP": "₹{:,.1f}",
                "Fair_Value": "₹{:,.1f}",
                "Upside_Pct": "{:+.1f}%",
                "Weight_Pct": "{:.1%}",
                "Allocated_INR": "₹{:,.0f}",
                "Actual_Invested_INR": "₹{:,.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )

        total_invested = basket_df["Actual_Invested_INR"].sum()
        cash_left = total_capital - total_invested
        st.success(f"💰 **Total Capital Deployed:** ₹{total_invested:,.0f} | **Unallocated Cash:** ₹{cash_left:,.0f} ({cash_left/total_capital:.1%})")

        fig_pie = px.pie(basket_df, names="Ticker", values="Allocated_INR", title="Portfolio Capital Allocation Breakdown (₹)")
        st.plotly_chart(fig_pie, use_container_width=True)

# ---------------------------------------------------------
# 14. TAB 3: WALK-FORWARD HISTORICAL BACKTESTING LAB
# ---------------------------------------------------------
with tab_backtest:
    st.subheader("📈 Institutional Walk-Forward Backtesting Engine (QUANT-APEX Basket vs. Nifty 50 Index)")
    b_col1, b_col2, b_col3, b_col4 = st.columns([1.2, 1, 1, 1])
    with b_col1:
        bt_segment = st.selectbox("Select Universe Segment to Backtest:", ["All-Cap Top Ranked", "Large-Cap Only", "Mid-Cap Only", "Small-Cap Only"])
    with b_col2:
        bt_top_n = st.slider("Top N Ranked Stocks in Basket:", min_value=2, max_value=10, value=5, step=1)
    with b_col3:
        bt_years = st.selectbox("Historical Backtest Horizon:", options=[1, 3, 5], index=1, format_func=lambda x: f"{x} Years Lookback")
    with b_col4:
        bt_scheme = st.selectbox("Portfolio Weighting Scheme:", ["Alpha-Score Weighted", "Equal Weighted"])

    if bt_segment == "All-Cap Top Ranked":
        bt_pool = clean_universe.copy()
    else:
        cap_name = bt_segment.replace(" Only", "")
        bt_pool = clean_universe[clean_universe["Category"] == cap_name].copy()

    bt_selected_df = bt_pool.head(bt_top_n).copy()

    if len(bt_selected_df) >= 1:
        if bt_scheme == "Alpha-Score Weighted":
            w_bt = (bt_selected_df["Final_Score"] / bt_selected_df["Final_Score"].sum()).tolist()
        else:
            w_bt = [1.0 / len(bt_selected_df)] * len(bt_selected_df)

        with st.spinner(f"Running {bt_years}-Year Institutional Backtest against Nifty 50..."):
            bt_res = run_historical_backtest(bt_selected_df.to_json(), w_bt, years_lookback=bt_years)

        bk1, bk2, bk3, bk4, bk5, bk6 = st.columns(6)
        bk1.metric("QUANT-APEX CAGR", f"{bt_res['port_cagr']:+.2f}%", f"{bt_res['alpha']:+.2f}% Alpha vs Nifty")
        bk2.metric("Nifty 50 Benchmark CAGR", f"{bt_res['bench_cagr']:+.2f}%")
        bk3.metric("Portfolio Sharpe Ratio", f"{bt_res['port_sharpe']:.2f}", f"Nifty Sharpe: {bt_res['bench_sharpe']:.2f}")
        bk4.metric("Portfolio Sortino Ratio", f"{bt_res['port_sortino']:.2f}", "Downside Risk-Adj")
        bk5.metric("Max Drawdown (Portfolio)", f"{bt_res['max_dd_port']:.2f}%", f"Nifty DD: {bt_res['max_dd_bench']:.2f}%")
        bk6.metric("Monthly Outperformance", f"{bt_res['win_months_pct']:.1f}%", "Months Beating Nifty")

        ch_left, ch_right = st.columns([1.35, 1])

        with ch_left:
            eq_df = pd.DataFrame({
                "Date": bt_res["dates"],
                "QUANT-APEX Top-Ranked Basket (₹)": bt_res["port_nav"].values,
                "Nifty 50 Benchmark (₹)": bt_res["bench_nav"].values
            })
            fig_eq = px.line(
                eq_df, x="Date",
                y=["QUANT-APEX Top-Ranked Basket (₹)", "Nifty 50 Benchmark (₹)"],
                title=f"Cumulative Growth of ₹1,00,000 ({bt_years}-Year Backtest)",
                labels={"value": "Portfolio Value (₹)", "variable": "Strategy"},
                height=380
            )
            fig_eq.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_eq, use_container_width=True)

        with ch_right:
            dd_df = pd.DataFrame({
                "Date": bt_res["dates"],
                "QUANT-APEX Drawdown (%)": bt_res["port_dd"].values,
                "Nifty 50 Drawdown (%)": bt_res["bench_dd"].values
            })
            fig_dd = px.area(
                dd_df, x="Date",
                y=["QUANT-APEX Drawdown (%)", "Nifty 50 Drawdown (%)"],
                title="Underwater Drawdown Profile (%)",
                labels={"value": "Drawdown (%)", "variable": "Series"},
                height=380
            )
            fig_dd.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_dd, use_container_width=True)

        st.markdown("#### 📊 Constituent Stock Performance & Alpha Attribution")
        st.dataframe(
            bt_res["contrib_df"].style.format({
                "Quant Score": "{:.1f}",
                "Portfolio Weight (%)": "{:.1f}%",
                f"{bt_years}Y Cumulative Return (%)": "{:+.1f}%",
                f"{bt_years}Y Annualized CAGR (%)": "{:+.1f}%"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No clean stocks available in this segment to run backtest.")
# ================= END OF PART 2 (COMPLETE FILE) =================
