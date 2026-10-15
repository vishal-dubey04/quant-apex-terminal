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
# 1. PAGE CONFIGURATION & HEADER
# ---------------------------------------------------------
st.set_page_config(
    page_title="QUANT-APEX v3.0 | Institutional Alpha, Auto-Save DB & Portfolio Allocator",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ QUANT-APEX v3.0: Institutional Multi-Cap Terminal with Permanent CSV DB & Capital Allocator")
st.markdown(
    "**Permanent Local CSV Auto-Save DB** | **Portfolio Position Sizing & ₹ Capital Allocator** | "
    "**Damodaran ROIC-Reinvestment Fade DCF** | **Technical Timing (EMA/RSI/ADX)** | **Live NSE Ticker Fetcher**"
)

# ---------------------------------------------------------
# 2. MASTER WEIGHTS BY MARKET CAP
# ---------------------------------------------------------
CATEGORY_WEIGHTS = {
    "Large-Cap": {"Profitability": 30, "Growth": 15, "CashFlow_BS": 20, "Governance": 15, "Valuation": 20},
    "Mid-Cap":   {"Profitability": 25, "Growth": 30, "CashFlow_BS": 20, "Governance": 15, "Valuation": 10},
    "Small-Cap": {"Profitability": 15, "Growth": 25, "CashFlow_BS": 25, "Governance": 25, "Valuation": 10}
}

# ---------------------------------------------------------
# 3. PERMANENT LOCAL DB AUTO-SAVE & INITIAL DATASET
# ---------------------------------------------------------
DB_FILENAME = "quant_apex_db.csv"

def get_initial_dataset():
    data = [
        # ================= LARGE CAPS =================
        {"Ticker": "TCS", "Company": "Tata Consultancy Services", "Category": "Large-Cap", "Sector": "IT Services",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 4120.0, "Shares_Cr": 361.8, "Base_Rev_Cr": 240893.0, "Base_EBITDA_Cr": 64200.0, "Base_FCFF_Cr": 44200.0,
         "Total_Debt_Cr": 8020.0, "Cash_Cr": 46500.0, "Beta": 0.78, "Cost_of_Debt": 7.2, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 10.5, "Term_Growth": 5.0, "Peer_EV_EBITDA": 24.0, "Peer_PE": 28.0, "EPS": 135.0,
         "ROCE": 64.0, "ROE": 51.0, "OPM": 25.0, "Sales_CAGR_3Y": 12.5, "PAT_CAGR_3Y": 11.0,
         "CFO_EBITDA": 88.0, "Debt_Equity": 0.08, "Int_Coverage": 45.0, "Promoter_Hold": 71.8,
         "Promoter_Pledge": 0.5, "Debtor_Days": 68, "PEG": 2.4, "PE_vs_Median": 0.95,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 260.0,
         "EMA_50": 4080.0, "EMA_200": 3910.0, "RSI_14": 58.5, "ADX_14": 24.2},

        {"Ticker": "ICICIBANK", "Company": "ICICI Bank Ltd", "Category": "Large-Cap", "Sector": "BFSI - Banking",
         "Is_BFSI": True, "Is_Cyclical": False,
         "CMP": 1265.0, "Shares_Cr": 704.0, "Base_Rev_Cr": 165840.0, "Base_EBITDA_Cr": 58200.0, "Base_FCFF_Cr": 0.0,
         "Total_Debt_Cr": 0.0, "Cash_Cr": 0.0, "Beta": 0.96, "Cost_of_Debt": 7.0, "Tax_Rate": 25.0,
         "Proj_Growth_5Y": 16.5, "Term_Growth": 6.0, "Peer_EV_EBITDA": 0.0, "Peer_PE": 19.5, "EPS": 62.5,
         "ROCE": 18.0, "ROE": 18.2, "OPM": 42.0, "Sales_CAGR_3Y": 21.0, "PAT_CAGR_3Y": 26.5,
         "CFO_EBITDA": 80.0, "Debt_Equity": 0.0, "Int_Coverage": 10.0, "Promoter_Hold": 0.0,
         "Promoter_Pledge": 0.0, "Debtor_Days": 0, "PEG": 1.15, "PE_vs_Median": 0.98,
         "ROA": 2.38, "NIM": 4.45, "NNPA": 0.43, "CAR": 16.7, "BVPS": 368.0,
         "EMA_50": 1235.0, "EMA_200": 1140.0, "RSI_14": 62.0, "ADX_14": 28.5},

        {"Ticker": "SUNPHARMA", "Company": "Sun Pharmaceutical Industries", "Category": "Large-Cap", "Sector": "Pharmaceuticals",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 1780.0, "Shares_Cr": 239.9, "Base_Rev_Cr": 48496.0, "Base_EBITDA_Cr": 13020.0, "Base_FCFF_Cr": 9850.0,
         "Total_Debt_Cr": 2850.0, "Cash_Cr": 18400.0, "Beta": 0.68, "Cost_of_Debt": 7.5, "Tax_Rate": 20.0,
         "Proj_Growth_5Y": 14.5, "Term_Growth": 5.5, "Peer_EV_EBITDA": 26.0, "Peer_PE": 32.0, "EPS": 46.5,
         "ROCE": 19.5, "ROE": 16.2, "OPM": 26.8, "Sales_CAGR_3Y": 13.8, "PAT_CAGR_3Y": 18.5,
         "CFO_EBITDA": 82.0, "Debt_Equity": 0.05, "Int_Coverage": 32.0, "Promoter_Hold": 54.5,
         "Promoter_Pledge": 0.0, "Debtor_Days": 82, "PEG": 1.6, "PE_vs_Median": 1.05,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 280.0,
         "EMA_50": 1745.0, "EMA_200": 1590.0, "RSI_14": 61.2, "ADX_14": 26.8},

        {"Ticker": "ULTRACEMCO", "Company": "UltraTech Cement Ltd", "Category": "Large-Cap", "Sector": "Cement (Cyclical)",
         "Is_BFSI": False, "Is_Cyclical": True,
         "CMP": 11250.0, "Shares_Cr": 28.87, "Base_Rev_Cr": 70908.0, "Base_EBITDA_Cr": 13450.0, "Base_FCFF_Cr": 8900.0,
         "Total_Debt_Cr": 10298.0, "Cash_Cr": 7830.0, "Beta": 0.89, "Cost_of_Debt": 7.6, "Tax_Rate": 25.5,
         "Proj_Growth_5Y": 15.5, "Term_Growth": 5.5, "Peer_EV_EBITDA": 22.0, "Peer_PE": 35.0, "EPS": 265.0,
         "ROCE": 15.8, "ROE": 13.2, "OPM": 19.0, "Sales_CAGR_3Y": 16.5, "PAT_CAGR_3Y": 14.0,
         "CFO_EBITDA": 79.0, "Debt_Equity": 0.17, "Int_Coverage": 11.5, "Promoter_Hold": 59.96,
         "Promoter_Pledge": 0.0, "Debtor_Days": 22, "PEG": 2.1, "PE_vs_Median": 1.08,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 2085.0,
         "EMA_50": 11100.0, "EMA_200": 10450.0, "RSI_14": 55.4, "ADX_14": 21.0},

        # ================= MID CAPS =================
        {"Ticker": "POLYCAB", "Company": "Polycab India Ltd", "Category": "Mid-Cap", "Sector": "Cables & FMEG",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 6650.0, "Shares_Cr": 15.02, "Base_Rev_Cr": 18039.0, "Base_EBITDA_Cr": 2560.0, "Base_FCFF_Cr": 1820.0,
         "Total_Debt_Cr": 150.0, "Cash_Cr": 2150.0, "Beta": 0.95, "Cost_of_Debt": 8.0, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 21.0, "Term_Growth": 6.0, "Peer_EV_EBITDA": 34.0, "Peer_PE": 42.0, "EPS": 132.0,
         "ROCE": 31.5, "ROE": 24.0, "OPM": 14.2, "Sales_CAGR_3Y": 22.5, "PAT_CAGR_3Y": 28.0,
         "CFO_EBITDA": 74.0, "Debt_Equity": 0.02, "Int_Coverage": 22.0, "Promoter_Hold": 65.2,
         "Promoter_Pledge": 0.0, "Debtor_Days": 46, "PEG": 1.35, "PE_vs_Median": 1.10,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 545.0,
         "EMA_50": 6520.0, "EMA_200": 5890.0, "RSI_14": 63.8, "ADX_14": 29.4},

        {"Ticker": "PERSISTENT", "Company": "Persistent Systems Ltd", "Category": "Mid-Cap", "Sector": "IT Engineering",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 5320.0, "Shares_Cr": 15.4, "Base_Rev_Cr": 9822.0, "Base_EBITDA_Cr": 1720.0, "Base_FCFF_Cr": 1240.0,
         "Total_Debt_Cr": 420.0, "Cash_Cr": 1890.0, "Beta": 1.02, "Cost_of_Debt": 7.9, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 19.5, "Term_Growth": 5.5, "Peer_EV_EBITDA": 32.0, "Peer_PE": 45.0, "EPS": 92.0,
         "ROCE": 29.0, "ROE": 24.5, "OPM": 17.5, "Sales_CAGR_3Y": 27.0, "PAT_CAGR_3Y": 26.5,
         "CFO_EBITDA": 81.0, "Debt_Equity": 0.09, "Int_Coverage": 25.0, "Promoter_Hold": 31.0,
         "Promoter_Pledge": 0.0, "Debtor_Days": 64, "PEG": 1.85, "PE_vs_Median": 1.20,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 325.0,
         "EMA_50": 5180.0, "EMA_200": 4650.0, "RSI_14": 60.5, "ADX_14": 25.0},

        {"Ticker": "CHOLAFIN", "Company": "Cholamandalam Investment & Fin", "Category": "Mid-Cap", "Sector": "BFSI - NBFC",
         "Is_BFSI": True, "Is_Cyclical": False,
         "CMP": 1440.0, "Shares_Cr": 84.0, "Base_Rev_Cr": 19200.0, "Base_EBITDA_Cr": 6400.0, "Base_FCFF_Cr": 0.0,
         "Total_Debt_Cr": 0.0, "Cash_Cr": 0.0, "Beta": 1.12, "Cost_of_Debt": 8.1, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 21.0, "Term_Growth": 6.0, "Peer_EV_EBITDA": 0.0, "Peer_PE": 26.0, "EPS": 48.0,
         "ROCE": 14.0, "ROE": 20.4, "OPM": 35.0, "Sales_CAGR_3Y": 25.0, "PAT_CAGR_3Y": 27.0,
         "CFO_EBITDA": 75.0, "Debt_Equity": 0.0, "Int_Coverage": 5.0, "Promoter_Hold": 50.4,
         "Promoter_Pledge": 0.0, "Debtor_Days": 0, "PEG": 1.10, "PE_vs_Median": 1.02,
         "ROA": 2.55, "NIM": 6.80, "NNPA": 1.15, "CAR": 18.6, "BVPS": 248.0,
         "EMA_50": 1410.0, "EMA_200": 1315.0, "RSI_14": 57.0, "ADX_14": 23.5},

        # ================= SMALL CAPS =================
        {"Ticker": "CMSINFO", "Company": "CMS Info Systems Ltd", "Category": "Small-Cap", "Sector": "Cash Logistics & AIoT",
         "Is_BFSI": False, "Is_Cyclical": False,
         "CMP": 565.0, "Shares_Cr": 16.28, "Base_Rev_Cr": 2265.0, "Base_EBITDA_Cr": 595.0, "Base_FCFF_Cr": 390.0,
         "Total_Debt_Cr": 0.0, "Cash_Cr": 780.0, "Beta": 0.90, "Cost_of_Debt": 8.2, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 18.5, "Term_Growth": 5.5, "Peer_EV_EBITDA": 15.0, "Peer_PE": 22.0, "EPS": 24.5,
         "ROCE": 26.5, "ROE": 20.2, "OPM": 25.5, "Sales_CAGR_3Y": 19.5, "PAT_CAGR_3Y": 23.0,
         "CFO_EBITDA": 80.0, "Debt_Equity": 0.00, "Int_Coverage": 35.0, "Promoter_Hold": 26.7,
         "Promoter_Pledge": 0.0, "Debtor_Days": 62, "PEG": 0.95, "PE_vs_Median": 0.92,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 122.0,
         "EMA_50": 552.0, "EMA_200": 505.0, "RSI_14": 59.0, "ADX_14": 27.1},

        {"Ticker": "RATNAMANI", "Company": "Ratnamani Metals & Tubes", "Category": "Small-Cap", "Sector": "Specialty Steel Tubes",
         "Is_BFSI": False, "Is_Cyclical": True,
         "CMP": 3420.0, "Shares_Cr": 7.01, "Base_Rev_Cr": 5059.0, "Base_EBITDA_Cr": 910.0, "Base_FCFF_Cr": 610.0,
         "Total_Debt_Cr": 180.0, "Cash_Cr": 920.0, "Beta": 0.85, "Cost_of_Debt": 8.0, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 18.0, "Term_Growth": 5.5, "Peer_EV_EBITDA": 24.0, "Peer_PE": 32.0, "EPS": 94.0,
         "ROCE": 27.0, "ROE": 21.5, "OPM": 17.8, "Sales_CAGR_3Y": 21.0, "PAT_CAGR_3Y": 25.0,
         "CFO_EBITDA": 73.0, "Debt_Equity": 0.06, "Int_Coverage": 24.0, "Promoter_Hold": 60.2,
         "Promoter_Pledge": 0.0, "Debtor_Days": 54, "PEG": 1.25, "PE_vs_Median": 1.00,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 430.0,
         "EMA_50": 3390.0, "EMA_200": 3180.0, "RSI_14": 56.5, "ADX_14": 22.8},

        {"Ticker": "UJJIVANSFB", "Company": "Ujjivan Small Finance Bank", "Category": "Small-Cap", "Sector": "BFSI - Banking",
         "Is_BFSI": True, "Is_Cyclical": False,
         "CMP": 44.0, "Shares_Cr": 193.0, "Base_Rev_Cr": 5680.0, "Base_EBITDA_Cr": 1920.0, "Base_FCFF_Cr": 0.0,
         "Total_Debt_Cr": 0.0, "Cash_Cr": 0.0, "Beta": 1.05, "Cost_of_Debt": 7.8, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 16.0, "Term_Growth": 5.0, "Peer_EV_EBITDA": 0.0, "Peer_PE": 10.5, "EPS": 6.4,
         "ROCE": 16.0, "ROE": 22.8, "OPM": 34.0, "Sales_CAGR_3Y": 24.0, "PAT_CAGR_3Y": 32.0,
         "CFO_EBITDA": 80.0, "Debt_Equity": 0.0, "Int_Coverage": 8.0, "Promoter_Hold": 0.0,
         "Promoter_Pledge": 0.0, "Debtor_Days": 0, "PEG": 0.55, "PE_vs_Median": 0.78,
         "ROA": 2.90, "NIM": 8.80, "NNPA": 0.28, "CAR": 24.5, "BVPS": 29.5,
         "EMA_50": 46.5, "EMA_200": 50.2, "RSI_14": 41.0, "ADX_14": 18.0},

        {"Ticker": "TRAPCORP", "Company": "High-Pledge RedFlag Infra (Demo)", "Category": "Small-Cap", "Sector": "EPC Infra",
         "Is_BFSI": False, "Is_Cyclical": True,
         "CMP": 410.0, "Shares_Cr": 12.0, "Base_Rev_Cr": 3200.0, "Base_EBITDA_Cr": 448.0, "Base_FCFF_Cr": 95.0,
         "Total_Debt_Cr": 2400.0, "Cash_Cr": 110.0, "Beta": 1.45, "Cost_of_Debt": 11.5, "Tax_Rate": 25.2,
         "Proj_Growth_5Y": 12.0, "Term_Growth": 4.0, "Peer_EV_EBITDA": 10.0, "Peer_PE": 12.0, "EPS": 28.0,
         "ROCE": 18.0, "ROE": 19.0, "OPM": 14.0, "Sales_CAGR_3Y": 25.0, "PAT_CAGR_3Y": 28.0,
         "CFO_EBITDA": 22.0, "Debt_Equity": 1.65, "Int_Coverage": 1.8, "Promoter_Hold": 48.0,
         "Promoter_Pledge": 34.0, "Debtor_Days": 165, "PEG": 0.70, "PE_vs_Median": 0.65,
         "ROA": 0.0, "NIM": 0.0, "NNPA": 0.0, "CAR": 0.0, "BVPS": 140.0,
         "EMA_50": 395.0, "EMA_200": 445.0, "RSI_14": 36.0, "ADX_14": 31.0},
    ]
    return pd.DataFrame(data)

def load_master_database():
    if os.path.exists(DB_FILENAME):
        try:
            return pd.read_csv(DB_FILENAME)
        except Exception:
            return get_initial_dataset()
    else:
        df_init = get_initial_dataset()
        try:
            df_init.to_csv(DB_FILENAME, index=False)
        except Exception:
            pass
        return df_init

def save_master_database(df):
    try:
        df.to_csv(DB_FILENAME, index=False)
    except Exception:
        pass

if "master_df" not in st.session_state:
    st.session_state.master_df = load_master_database()

# ---------------------------------------------------------
# 4. LIVE NSE TICKER FETCHER (YFINANCE ENGINE)
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
    if mcap_cr >= 106346:
        cat = "Large-Cap"
    elif mcap_cr >= 33664:
        cat = "Mid-Cap"
    else:
        cat = "Small-Cap"

    shares_cr = round(mcap_cr / cmp_val, 2)
    sector = info.get("sector", "Industrial")
    industry = info.get("industry", "")
    is_bfsi = any(k in (sector + " " + industry).upper() for k in ["BANK", "FINANCIAL", "CREDIT", "NBFC"])
    is_cyclical = any(k in (sector + " " + industry).upper() for k in ["CEMENT", "STEEL", "METAL", "CHEMICAL", "COMMODIT", "CONSTRUCTION"])

    rev_cr = float(info.get("totalRevenue", mcap_cr * 0.4 * 1e7)) / 1e7
    ebitda_cr = float(info.get("ebitda", rev_cr * 0.18 * 1e7)) / 1e7
    fcf_raw = info.get("freeCashflow")
    fcff_cr = (float(fcf_raw) / 1e7) if fcf_raw and fcf_raw > 0 else round(ebitda_cr * 0.62, 2)

    debt_cr = float(info.get("totalDebt", 0.0)) / 1e7
    cash_cr = float(info.get("totalCash", 0.0)) / 1e7
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
        "Ticker": clean_sym.replace(".NS", "").replace(".BO", ""),
        "Company": info.get("longName", clean_sym),
        "Category": cat,
        "Sector": "BFSI - Financial" if is_bfsi else sector,
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
        "Proj_Growth_5Y": round(np.clip(rev_g, 8.0, 26.0), 1),
        "Term_Growth": 5.5,
        "Peer_EV_EBITDA": 22.0,
        "Peer_PE": 25.0,
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
# 5. DAMODARAN ROIC-REINVESTMENT FADE VALUATION ENGINE
# ---------------------------------------------------------
def run_3stage_valuation(row, rf_rate=6.8, erp=5.5, custom_g5=None, custom_wacc=None, custom_tg=None, cyclical_haircut_pct=0.0):
    mcap_cr = row["CMP"] * row["Shares_Cr"]
    debt_cr = row["Total_Debt_Cr"]
    total_cap = mcap_cr + debt_cr

    we = 1.0 if row["Is_BFSI"] else (mcap_cr / total_cap if total_cap > 0 else 1.0)
    wd = 0.0 if row["Is_BFSI"] else (debt_cr / total_cap if total_cap > 0 else 0.0)

    ke = rf_rate + row["Beta"] * erp
    kd_post_tax = row["Cost_of_Debt"] * (1.0 - row["Tax_Rate"] / 100.0)
    computed_disc = ke if row["Is_BFSI"] else (we * ke + wd * kd_post_tax)

    disc_rate = custom_wacc if custom_wacc is not None else max(round(computed_disc, 2), 9.0)
    g_stage1 = custom_g5 if custom_g5 is not None else row["Proj_Growth_5Y"]
    tg = custom_tg if custom_tg is not None else row["Term_Growth"]

    if disc_rate <= tg + 1.25:
        tg = round(disc_rate - 1.5, 2)

    r_dec = disc_rate / 100.0
    g1_dec = g_stage1 / 100.0
    tg_dec = tg / 100.0

    growth_schedule = []
    cf_schedule = []
    pv_schedule = []
    metric1_schedule = []

    if not row["Is_BFSI"]:
        haircut_mult = (1.0 - cyclical_haircut_pct / 100.0) if row["Is_Cyclical"] else 1.0
        curr_fcff = row["Base_FCFF_Cr"] * haircut_mult
        curr_rev = row["Base_Rev_Cr"]

        for yr in range(1, 11):
            if yr <= 5:
                fade_step = 0.0
                g_yr = g1_dec
            else:
                fade_step = (yr - 5) / 5.0
                g_yr = g1_dec - fade_step * (g1_dec - tg_dec)

            curr_rev = curr_rev * (1.0 + g_yr)
            # Damodaran Stage-2 Reinvestment Fade: As growth moderates in Y6-Y10, capex intensity drops & FCF conversion expands
            curr_fcff = curr_fcff * (1.0 + g_yr) * (1.0 + (0.04 * fade_step))
            pv_cf = curr_fcff / ((1.0 + r_dec) ** yr)

            growth_schedule.append(round(g_yr * 100, 2))
            metric1_schedule.append(round(curr_rev, 2))
            cf_schedule.append(round(curr_fcff, 2))
            pv_schedule.append(round(pv_cf, 2))

        sum_pv_10y = round(sum(pv_schedule), 2)
        term_cf = cf_schedule[-1] * (1.0 + tg_dec)
        term_val = round(term_cf / (r_dec - tg_dec), 2)
        pv_term_val = round(term_val / ((1.0 + r_dec) ** 10), 2)

        enterprise_val = round(sum_pv_10y + pv_term_val, 2)
        equity_val = max(0.0, round(enterprise_val + row["Cash_Cr"] - row["Total_Debt_Cr"], 2))
        dcf_fair_value = round(equity_val / row["Shares_Cr"], 2)

        rel_ev = row["Base_EBITDA_Cr"] * haircut_mult * row["Peer_EV_EBITDA"]
        rel_eq_ev = max(0.0, (rel_ev + row["Cash_Cr"] - row["Total_Debt_Cr"]) / row["Shares_Cr"])
        rel_pe_val = row["EPS"] * row["Peer_PE"]
        relative_fair_value = round(0.6 * rel_eq_ev + 0.4 * rel_pe_val, 2)
        model_label = "10Y Damodaran ROIC-Fade FCFF DCF"

    else:
        curr_bv = row["BVPS"]
        roe_dec = row["ROE"] / 100.0
        retention_ratio = 0.78

        for yr in range(1, 11):
            if yr <= 5:
                fade_step = 0.0
                g_yr = g1_dec
                yr_roe = roe_dec
            else:
                fade_step = (yr - 5) / 5.0
                g_yr = g1_dec - fade_step * (g1_dec - tg_dec)
                target_roe = max(r_dec + 0.025, roe_dec * 0.85)
                yr_roe = roe_dec - fade_step * (roe_dec - target_roe)

            eps_yr = curr_bv * yr_roe
            excess_ret_ps = (yr_roe - r_dec) * curr_bv
            pv_er = excess_ret_ps / ((1.0 + r_dec) ** yr)
            curr_bv = curr_bv + eps_yr * retention_ratio

            growth_schedule.append(round(yr_roe * 100, 2))
            metric1_schedule.append(round(curr_bv, 2))
            cf_schedule.append(round(excess_ret_ps, 2))
            pv_schedule.append(round(pv_er, 2))

        sum_pv_10y = round(sum(pv_schedule), 2)
        term_er = cf_schedule[-1] * (1.0 + tg_dec)
        term_val = round(term_er / (r_dec - tg_dec), 2)
        pv_term_val = round(term_val / ((1.0 + r_dec) ** 10), 2)

        dcf_fair_value = max(row["BVPS"] * 0.8, round(row["BVPS"] + sum_pv_10y + pv_term_val, 2))
        enterprise_val = round(dcf_fair_value * row["Shares_Cr"], 2)
        equity_val = enterprise_val

        justified_pb = max(1.0, (roe_dec - tg_dec) / max(r_dec - tg_dec, 0.03))
        relative_fair_value = round(0.5 * (row["BVPS"] * justified_pb) + 0.5 * (row["EPS"] * row["Peer_PE"]), 2)
        model_label = "10Y BFSI Excess Return (Residual Income) Model"

    blended_fair_value = round(0.70 * dcf_fair_value + 0.30 * relative_fair_value, 2)
    bear_case_fv = round(blended_fair_value * 0.82, 2)
    bull_case_fv = round(blended_fair_value * 1.20, 2)
    upside_pct = round(((blended_fair_value - row["CMP"]) / row["CMP"]) * 100.0, 1)

    if upside_pct >= 18.0:
        val_tag = "🟢 UNDERVALUED (High Margin of Safety)"
    elif upside_pct >= 5.0:
        val_tag = "🟢 MILDLY UNDERVALUED"
    elif upside_pct >= -10.0:
        val_tag = "🟡 FAIRLY VALUED"
    else:
        val_tag = "🔴 OVERVALUED"

    return {
        "Model_Type": model_label,
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
        "DCF_Intrinsic_Value": dcf_fair_value,
        "Relative_Fair_Value": relative_fair_value,
        "Fair_Value": blended_fair_value,
        "Bear_Case_FV": bear_case_fv,
        "Bull_Case_FV": bull_case_fv,
        "Upside_Pct": upside_pct,
        "Valuation_Status": val_tag
    }

# ---------------------------------------------------------
# 6. DUAL-REGIME SCORING & EVALUATION ENGINE
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
            if row["Debt_Equity"] > 1.8:
                reasons.append(f"High D/E ({row['Debt_Equity']}x)")
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

# ---------------------------------------------------------
# 7. 5-TAB INSTITUTIONAL EXCEL (.XLSX) GENERATOR
# ---------------------------------------------------------
def generate_v3_institutional_excel(stock_row, val_res, weights):
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
    ws1.set_column("A:A", 38)
    ws1.set_column("B:D", 22)
    ws1.merge_range("A1:D1", f"QUANT-APEX v3.0 IC MEMO: {stock_row['Company']} ({stock_row['Ticker']})", title_fmt)

    summary_rows = [
        ("Market-Cap Tier & Regime", f"{stock_row['Category']} | {'BFSI Mode' if stock_row['Is_BFSI'] else 'Corporate Mode'}", tag_fmt),
        ("Composite Alpha Score (/100)", stock_row["Final_Score"], val_fmt),
        ("Fundamental Quality Score (/100)", stock_row["Fundamental_Score"], val_fmt),
        ("Technical Momentum Score (/100)", stock_row["Tech_Score"], val_fmt),
        ("Institutional Action Verdict", stock_row["Verdict"], tag_fmt),
        ("Current Market Price (CMP)", stock_row["CMP"], curr_fmt),
        ("Blended Institutional Fair Value (70% DCF + 30% Rel)", val_res["Fair_Value"], curr_fmt),
        ("Implied Margin of Safety / Upside (%)", val_res["Upside_Pct"] / 100.0, pct_fmt),
        ("Valuation Status", val_res["Valuation_Status"], tag_fmt)
    ]
    for r_i, (k, v, f_style) in enumerate(summary_rows, start=3):
        ws1.write(f"A{r_i}", k, lbl_fmt)
        ws1.write(f"B{r_i}", v, f_style)

    ws1.write("A13", "5-Pillar Fundamental Breakdown", sub_hdr_fmt)
    ws1.write("B13", "Raw Score (/10)", sub_hdr_fmt)
    ws1.write("C13", "Category Weight", sub_hdr_fmt)
    ws1.write("D13", "Weighted Marks", sub_hdr_fmt)

    pillars = [
        ("1. Profitability & Capital Moat", stock_row["P1_Raw"], weights["Profitability"]),
        ("2. Growth & Operating Scalability", stock_row["P2_Raw"], weights["Growth"]),
        ("3. Cash Flow / Asset Quality", stock_row["P3_Raw"], weights["CashFlow_BS"]),
        ("4. Governance & Forensics", stock_row["P4_Raw"], weights["Governance"]),
        ("5. Valuation Comfort & PEG", stock_row["P5_Raw"], weights["Valuation"]),
    ]
    for idx, (p_name, p_raw, p_wt) in enumerate(pillars, start=14):
        ws1.write(f"A{idx}", p_name, lbl_fmt)
        ws1.write(f"B{idx}", p_raw, val_fmt)
        ws1.write(f"C{idx}", p_wt, val_fmt)
        ws1.write_formula(f"D{idx}", f"=(B{idx}/10)*C{idx}", val_fmt, (p_raw / 10.0) * p_wt)

    ws1.write("A19", "Total Fundamental Score (/100)", sub_hdr_fmt)
    ws1.write("B19", "", sub_hdr_fmt)
    ws1.write_formula("C19", "=SUM(C14:C18)", sub_hdr_fmt, 100)
    ws1.write_formula("D19", "=SUM(D14:D18)", curr_fmt, stock_row["Fundamental_Score"])

    ws2 = wb.add_worksheet("10Y_Damodaran_Valuation")
    ws2.set_column("A:A", 38)
    ws2.set_column("B:L", 16)
    ws2.merge_range("A1:L1", f"10-YEAR DAMODARAN ROIC-FADE VALUATION MODEL — {stock_row['Ticker']}", title_fmt)

    ws2.write("A3", "Discount Rate (WACC / Ke %)", lbl_fmt)
    ws2.write("B3", val_res["WACC"] / 100.0, pct_fmt)
    ws2.write("A4", "Stage-1 High Growth Rate (Years 1-5 %)", lbl_fmt)
    ws2.write("B4", val_res["Growth_5Y"] / 100.0, pct_fmt)
    ws2.write("A5", "Perpetual Terminal Growth Rate (g %)", lbl_fmt)
    ws2.write("B5", val_res["Term_Growth"] / 100.0, pct_fmt)

    ws2.write("A7", "10-Year Projection Schedule", sub_hdr_fmt)
    for yr in range(1, 11):
        ws2.write(6, yr, f"Year {yr}", sub_hdr_fmt)

    ws2.write("A8", "Discount Period (t)", lbl_fmt)
    ws2.write("A9", "Stage Growth / ROE Trajectory (%)", lbl_fmt)
    ws2.write("A10", "Projected Revenue (₹ Cr) / BVPS (₹)", lbl_fmt)
    ws2.write("A11", "Projected FCFF (₹ Cr) / Excess Return (₹)", lbl_fmt)
    ws2.write("A12", "Present Value of Cash Flow / ER", lbl_fmt)

    for yr in range(1, 11):
        col_let = chr(ord('A') + yr)
        ws2.write(7, yr, yr, val_fmt)
        ws2.write(8, yr, val_res["Growth_Schedule_10Y"][yr-1] / 100.0, pct_fmt)
        ws2.write(9, yr, val_res["Metric1_Schedule_10Y"][yr-1], val_fmt)
        ws2.write(10, yr, val_res["CF_Schedule_10Y"][yr-1], val_fmt)
        ws2.write_formula(f"{col_let}12", f"={col_let}11/((1+$B$3)^{col_let}8)", val_fmt, val_res["PV_Schedule_10Y"][yr-1])

    ws2.write("A14", "Cumulative PV of 10-Year Explicit Stage", lbl_fmt)
    ws2.write_formula("B14", "=SUM(B12:K12)", val_fmt, val_res["Sum_PV_10Y"])
    ws2.write("A15", "Terminal Value at Year 10", lbl_fmt)
    ws2.write_formula("B15", "=(K11*(1+$B$5))/($B$3-$B$5)", val_fmt, val_res["Terminal_Value"])
    ws2.write("A16", "Present Value of Terminal Value", lbl_fmt)
    ws2.write_formula("B16", "=B15/((1+$B$3)^10)", val_fmt, val_res["PV_Terminal_Value"])
    ws2.write("A17", "Intrinsic DCF / Excess Return Value per Share (₹)", lbl_fmt)
    ws2.write("B17", val_res["DCF_Intrinsic_Value"], curr_fmt)
    ws2.write("A18", "Relative Peer Multiple Fair Value per Share (₹)", lbl_fmt)
    ws2.write("B18", val_res["Relative_Fair_Value"], curr_fmt)
    ws2.write("A19", "BLENDED INSTITUTIONAL FAIR VALUE (70% DCF + 30% Rel)", lbl_fmt)
    ws2.write_formula("B19", "=0.70*B17+0.30*B18", curr_fmt, val_res["Fair_Value"])

    ws3 = wb.add_worksheet("Football_Field_Scenarios")
    ws3.set_column("A:D", 26)
    ws3.merge_range("A1:D1", f"FOOTBALL FIELD VALUATION SCENARIOS — {stock_row['Ticker']}", title_fmt)
    ws3.write("A3", "Valuation Methodology / Scenario", sub_hdr_fmt)
    ws3.write("B3", "Target Fair Value (₹)", sub_hdr_fmt)
    ws3.write("C3", "Current CMP (₹)", sub_hdr_fmt)
    ws3.write("D3", "Implied Upside / Downside (%)", sub_hdr_fmt)

    scenarios = [
        ("Bear Case Target (-18% Stress)", val_res["Bear_Case_FV"]),
        ("10Y Damodaran DCF / Excess Return", val_res["DCF_Intrinsic_Value"]),
        ("Relative Peer Multiple Valuation", val_res["Relative_Fair_Value"]),
        ("Blended Base Case Fair Value", val_res["Fair_Value"]),
        ("Bull Case Target (+20% Blue-Sky)", val_res["Bull_Case_FV"])
    ]
    for r_i, (s_name, s_val) in enumerate(scenarios, start=4):
        ws3.write(f"A{r_i}", s_name, lbl_fmt)
        ws3.write(f"B{r_i}", s_val, curr_fmt)
        ws3.write(f"C{r_i}", stock_row["CMP"], val_fmt)
        ws3.write_formula(f"D{r_i}", f"=(B{r_i}-C{r_i})/C{r_i}", pct_fmt, (s_val - stock_row["CMP"]) / stock_row["CMP"])

    ws4 = wb.add_worksheet("Sensitivity_Matrix_2D")
    ws4.set_column("A:F", 20)
    ws4.merge_range("A1:F1", f"2D SENSITIVITY MATRIX: BLENDED FAIR VALUE (₹) — {stock_row['Ticker']}", title_fmt)

    w_steps = [round(val_res["WACC"] + d, 2) for d in [-1.0, -0.5, 0.0, 0.5, 1.0]]
    g_steps = [round(val_res["Term_Growth"] + d, 2) for d in [-1.0, -0.5, 0.0, 0.5, 1.0]]
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
# 8. SIDEBAR: LIVE NSE FETCHER & PORTFOLIO ALLOCATOR
# ---------------------------------------------------------
st.sidebar.header("⚡ Live NSE Ticker Fetcher")
live_ticker_input = st.sidebar.text_input("Enter NSE Ticker (e.g. BEL.NS, HAL.NS, TRENT.NS):", placeholder="BEL.NS")

if st.sidebar.button("🚀 Fetch Live NSE Data & Save to DB", use_container_width=True):
    if not YF_AVAILABLE:
        st.sidebar.error("Please ensure `yfinance` is installed!")
    elif live_ticker_input.strip():
        with st.sidebar.status(f"Fetching {live_ticker_input.upper()} from NSE & updating DB..."):
            try:
                new_stock = fetch_live_nse_stock(live_ticker_input)
                df_curr = st.session_state.master_df
                df_curr = df_curr[df_curr["Ticker"] != new_stock["Ticker"]]
                updated_df = pd.concat([df_curr, pd.DataFrame([new_stock])], ignore_index=True)
                st.session_state.master_df = updated_df
                save_master_database(updated_df)
                st.sidebar.success(f"✅ Saved {new_stock['Ticker']} ({new_stock['Category']}) @ ₹{new_stock['CMP']}!")
            except Exception as e:
                st.sidebar.error(f"Error fetching ticker: {e}")

st.sidebar.divider()
st.sidebar.header("🛡️ Institutional Risk Controls")
cyclical_haircut = st.sidebar.slider(
    "Cyclical Peak-Margin Haircut (%)",
    min_value=0.0, max_value=25.0, value=10.0, step=2.5,
    help="Normalizes peak-cycle FCFF/EBITDA for Cyclical stocks."
)

# ---------------------------------------------------------
# 9. MAIN UI: MULTI-TAB NAVIGATION (LEADERBOARD VS PORTFOLIO ALLOCATOR)
# ---------------------------------------------------------
tab_rank, tab_alloc = st.tabs(["🏆 Quantitative Ranking & DCF Terminal", "💼 Institutional Portfolio Capital Allocator (₹)"])

with tab_rank:
    st.subheader("1️⃣ Select Market-Cap Tier to Rank Stocks (Hierarchical Order: Highest Alpha Score First)")
    selected_cap = st.radio(
        "Market-Cap Segment (SEBI / AMFI Classification):",
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

    ranked_df = evaluate_stocks(st.session_state.master_df, selected_cap, weights, cyclical_haircut=cyclical_haircut)

    st.subheader(f"🏆 {selected_cap} Institutional Alpha Leaderboard (80% Fundamental + 20% Technical Timing)")
    display_cols = [
        "Rank", "Ticker", "Company", "Sector", "Final_Score", "Fundamental_Score", "Tech_Score",
        "CMP", "Fair_Value", "Upside_Pct", "Valuation_Status", "Verdict"
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

    st.subheader("2️⃣ Institutional 10-Year Valuation Terminal & 5-Tab Excel Generator")

    c_sel, c_s1, c_s2, c_s3 = st.columns([1.3, 1, 1, 1])
    with c_sel:
        selected_ticker = st.selectbox(
            "Select Ranked Stock for Deep-Dive & Excel Export:",
            options=ranked_df["Ticker"].tolist(),
            format_func=lambda x: f"{x} — {ranked_df[ranked_df['Ticker']==x]['Company'].values[0]} ({ranked_df[ranked_df['Ticker']==x]['Rank'].values[0]})"
        )

    stock_row = ranked_df[ranked_df["Ticker"] == selected_ticker].iloc[0].copy()

    with st.expander("🛠️ Institutional Analyst Override & Calibration Desk (Edit Base FCFF, Pledge %, Peer P/E or BFSI Ratios)", expanded=False):
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

        if o5.button("💾 Save & Update Local DB", use_container_width=True):
            idx_mask = st.session_state.master_df["Ticker"] == selected_ticker
            st.session_state.master_df.loc[idx_mask, "Base_FCFF_Cr"] = ov_fcff
            st.session_state.master_df.loc[idx_mask, "Promoter_Pledge"] = ov_pledge
            st.session_state.master_df.loc[idx_mask, "Peer_PE"] = ov_peer_pe
            if stock_row["Is_BFSI"]:
                st.session_state.master_df.loc[idx_mask, "NNPA"] = ov_metric4
            else:
                st.session_state.master_df.loc[idx_mask, "CFO_EBITDA"] = ov_metric4
            save_master_database(st.session_state.master_df)
            st.success("✅ Saved permanently to `quant_apex_db.csv`!")
            st.rerun()

    base_val = run_3stage_valuation(stock_row, cyclical_haircut_pct=cyclical_haircut)

    with c_s1:
        u_g5 = st.slider("Stage-1 High Growth (Y1-Y5 %)", 5.0, 35.0, float(base_val["Growth_5Y"]), 0.5, key=f"g5_{selected_ticker}")
    with c_s2:
        u_wacc = st.slider("Discount Rate (WACC / Ke %)", 8.0, 18.0, float(base_val["WACC"]), 0.25, key=f"wacc_{selected_ticker}")
    with c_s3:
        u_tg = st.slider("Perpetual Terminal Growth (%)", 3.0, 7.5, float(base_val["Term_Growth"]), 0.25, key=f"tg_{selected_ticker}")

    live_val = run_3stage_valuation(stock_row, custom_g5=u_g5, custom_wacc=u_wacc, custom_tg=u_tg, cyclical_haircut_pct=cyclical_haircut)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Valuation Regime", "🏦 BFSI Excess Return" if stock_row["Is_BFSI"] else "🏭 10Y Damodaran Fade")
    m2.metric("Current Price (CMP)", f"₹{stock_row['CMP']:,.1f}")
    m3.metric("10Y Intrinsic DCF/ER", f"₹{live_val['DCF_Intrinsic_Value']:,.1f}")
    m4.metric("Peer Relative Value", f"₹{live_val['Relative_Fair_Value']:,.1f}")
    m5.metric("Blended Fair Value", f"₹{live_val['Fair_Value']:,.1f}", f"{live_val['Upside_Pct']:+.1f}% vs CMP")
    m6.metric("Technical Regime", f"{stock_row['Tech_Score']}/100", f"RSI: {stock_row['RSI_14']} | ADX: {stock_row['ADX_14']}")

    excel_data = generate_v3_institutional_excel(stock_row, live_val, weights)
    st.download_button(
        label=f"📥 Download {selected_ticker} 5-Tab Institutional Research Excel (.xlsx)",
        data=excel_data,
        file_name=f"{selected_ticker}_QUANT_APEX_v3_Institutional_Model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown(f"#### 📅 {selected_ticker} — 10-Year Damodaran ROIC-Fade Projection Schedule")
        schedule_df = pd.DataFrame({
            "Year": [f"Y{i}" for i in range(1, 11)],
            "Stage": ["Stage 1 (High)" if i <= 5 else "Stage 2 (Fade)" for i in range(1, 11)],
            "Growth / ROE (%)": live_val["Growth_Schedule_10Y"],
            "Rev (₹Cr) / BVPS (₹)": live_val["Metric1_Schedule_10Y"],
            "FCFF (₹Cr) / Excess Ret (₹)": live_val["CF_Schedule_10Y"],
            "Discounted PV": live_val["PV_Schedule_10Y"]
        })
        st.dataframe(schedule_df.style.format({
            "Growth / ROE (%)": "{:.1f}%",
            "Rev (₹Cr) / BVPS (₹)": "{:,.1f}",
            "FCFF (₹Cr) / Excess Ret (₹)": "{:,.1f}",
            "Discounted PV": "{:,.1f}"
        }), use_container_width=True, hide_index=True)

    with col_right:
        st.markdown(f"#### 🏈 Institutional Football Field Valuation Range ({selected_ticker})")
        ff_df = pd.DataFrame({
            "Scenario": ["Bear Case (-18%)", "10Y Damodaran DCF", "Peer Relative Multiple", "Blended Fair Value", "Bull Case (+20%)", "Current CMP"],
            "Price (₹)": [live_val["Bear_Case_FV"], live_val["DCF_Intrinsic_Value"], live_val["Relative_Fair_Value"], live_val["Fair_Value"], live_val["Bull_Case_FV"], stock_row["CMP"]]
        })
        fig_ff = px.bar(
            ff_df, x="Price (₹)", y="Scenario", orientation="h",
            text="Price (₹)", color="Scenario",
            height=360
        )
        fig_ff.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig_ff.update_layout(showlegend=False, margin=dict(l=20, r=40, t=20, b=20))
        st.plotly_chart(fig_ff, use_container_width=True)

with tab_alloc:
    st.subheader("💼 Institutional Portfolio Capital Allocator & ₹ Position Sizing Desk")
    st.markdown("Enter your total capital to allocate across selected high-alpha fundamentally clean stocks based on their Composite Score and Margin of Safety.")

    col_cap_in, col_max_w = st.columns(2)
    total_capital = col_cap_in.number_input("Total Investment Capital (₹)", value=500000.0, step=50000.0)
    max_weight_pct = col_max_w.slider("Max Weight per Stock Cap (%)", 10.0, 40.0, 25.0, 5.0)

    all_evaluated = []
    for cap_tier in ["Large-Cap", "Mid-Cap", "Small-Cap"]:
        res_df = evaluate_stocks(st.session_state.master_df, cap_tier, CATEGORY_WEIGHTS[cap_tier], cyclical_haircut=cyclical_haircut)
        all_evaluated.append(res_df)
    universe_df = pd.concat(all_evaluated, ignore_index=True)
    clean_universe = universe_df[universe_df["Forensic_Status"] == "Clean"].sort_values(by="Final_Score", ascending=False)

    selected_tickers = st.multiselect(
        "Select Clean Stocks to Include in Portfolio Basket:",
        options=clean_universe["Ticker"].tolist(),
        default=clean_universe["Ticker"].head(5).tolist()
    )

    if selected_tickers:
        basket_df = clean_universe[clean_universe["Ticker"].isin(selected_tickers)].copy()
        basket_df["Allocation_Factor"] = basket_df["Final_Score"] * np.maximum(1.0, 1.0 + basket_df["Upside_Pct"] / 100.0)
        sum_factor = basket_df["Allocation_Factor"].sum()
        basket_df["Raw_Weight"] = basket_df["Allocation_Factor"] / sum_factor
        basket_df["Weight_Pct"] = np.minimum(basket_df["Raw_Weight"], max_weight_pct / 100.0)
        basket_df["Weight_Pct"] = basket_df["Weight_Pct"] / basket_df["Weight_Pct"].sum()

        basket_df["Allocated_INR"] = basket_df["Weight_Pct"] * total_capital
        basket_df["Shares_To_Buy"] = (basket_df["Allocated_INR"] / basket_df["CMP"]).astype(int)
        basket_df["Actual_Invested_INR"] = basket_df["Shares_To_Buy"] * basket_df["CMP"]

        st.markdown("### 📊 Optimal Institutional Portfolio Allocation Table")
        alloc_display = [
            "Ticker", "Company", "Category", "Final_Score", "CMP", "Fair_Value", "Upside_Pct",
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

        fig_pie = px.pie(
            basket_df, names="Ticker", values="Allocated_INR",
            title="Portfolio Capital Allocation Breakdown (₹)"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Please select at least one stock above to generate the portfolio allocation plan.")
