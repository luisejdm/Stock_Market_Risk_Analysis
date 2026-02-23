import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

from visualization import build_spider_chart

# Configuration

API_URL = "http://localhost:8000/evaluate"

INDUSTRY_OPTIONS = {
    'Public Manufacturing (Classic Altman Z-Score)': 1,
    'Non-Manufacturing / Private (Altman 2000 Z-Score)': 2,
    'Emerging Markets (Zeta-Score)': 3,
}

CLASSIFICATION_COLORS = {
    "Distress Zone": "#E84545",
    "Safe Zone":     "#00C896",
    "Grey Zone":     "#F5A623"
}

CLASSIFICATION_BG = {
    "Distress Zone": "rgba(232,69,69,0.12)",
    "Safe Zone":     "rgba(0,200,150,0.12)",
    "Grey Zone":     "rgba(245,166,35,0.12)"
}

DECISION_COLORS = {
    "Approved":              "#00C896",
    "Approved with Caution": "#6494ED",
    "Analysis Required":     "#F5A623",
    "Dismissed":             "#E84545",
}

DECISION_BG = {
    "Approved":              "rgba(0,200,150,0.12)",
    "Approved with Caution": "rgba(100,148,237,0.12)",
    "Analysis Required":     "rgba(245,166,35,0.12)",
    "Dismissed":             "rgba(232,69,69,0.12)",
}

RATIO_LABELS = {
    'x1': 'Working Capital / Total Assets',
    'x2': 'Retained Earnings / Total Assets',
    'x3': 'Earnings Before Interest and Taxes / Total Assets',
    'x4': 'Market Value of Equity / Book Value of Total Liabilities',
    'x5': 'Sales / Total Assets'
}


# Set up the Streamlit app
st.set_page_config(
    page_title="Stock Market Risk Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    /* Base */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
    }

    .stApp {
        background-color: #0D0F14;
    }

    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        letter-spacing: -0.02em;
    }

    .main-title {
        font-family: 'Syne', sans-serif;
        font-size: 3rem;
        font-weight: 800;
        color: #E8EAF0;
        line-height: 1.1;
        margin-bottom: 0.25rem;
    }

    .main-subtitle {
        font-family: 'DM Mono', monospace;
        font-size: 0.85rem;
        color: #6B7280;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 2.5rem;
    }

    .metric-card {
        background: #161A23;
        border: 1px solid #252A36;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
    }

    .metric-ticker {
        font-family: 'Syne', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #E8EAF0;
        margin-bottom: 0.1rem;
    }

    .metric-model {
        font-size: 0.72rem;
        color: #6B7280;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
    }

    .metric-score {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .metric-score-sm {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.4rem;
        margin-top: 1rem;
    }

    .metric-label {
        font-size: 0.68rem;
        color: #6B7280;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }

    .divider {
        border: none;
        border-top: 1px solid #252A36;
        margin: 0.9rem 0;
    }

    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 500;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .decision-badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-top: 0.8rem;
    }

    .ratio-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.45rem 0;
        border-bottom: 1px solid #1E2330;
        font-size: 0.8rem;
    }

    .ratio-row:last-child {
        border-bottom: none;
    }

    .ratio-label {
        color: #9CA3AF;
    }

    .ratio-value {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        color: #E8EAF0;
    }

    .section-header {
        font-family: 'Syne', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #E8EAF0;
        letter-spacing: -0.01em;
        margin: 1.8rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #252A36;
    }

    .error-card {
        background: rgba(232,69,69,0.08);
        border: 1px solid rgba(232,69,69,0.3);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-size: 0.82rem;
        color: #E84545;
        margin-bottom: 0.75rem;
    }

    .stButton > button {
        background: #6494ED;
        color: #fff;
        border: none;
        border-radius: 8px;
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.6rem 1.8rem;
        width: 100%;
        letter-spacing: 0.02em;
        transition: background 0.2s;
    }

    .stButton > button:hover {
        background: #6494ED;
    }

    div[data-testid="stSidebar"] {
        background-color: #0D0F14;
        border-right: 1px solid #1E2330;
    }

    .stSelectbox label, .stTextInput label, .stNumberInput label {
        font-size: 0.78rem !important;
        color: #6B7280 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    input, select, textarea {
        background-color: #161A23 !important;
        border-color: #252A36 !important;
        color: #E8EAF0 !important;
        font-family: 'DM Mono', monospace !important;
    }

    .stDataFrame {
        background: #161A23;
        border-radius: 10px;
    }

    div[data-testid="stExpander"] {
        background: #161A23;
        border: 1px solid #252A36;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def call_api(ticker: str, industry_type: int) -> dict:
    """POST to the FastAPI backend and return the JSON response."""
    response = requests.post(
        API_URL,
        json={"ticker": ticker, "industry_type": industry_type},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()



# ----------------------------------------------------------------------
# Sidebar — inputs
# ----------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="main-title">Financial Risk Analysis Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Altman Z-Score and Merton Model</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-header">Company Input</div>', unsafe_allow_html=True)

    tickers_raw = st.text_input(
        "Tickers (comma-separated)",
        placeholder="AAPL, MSFT, TSLA",
        help="Enter one or more stock ticker symbols separated by commas.",
    )

    industry_raw = st.text_input(
        "Industry Types",
        placeholder="2, 2, 1",
        help="One industry type per ticker, comma-separated. 1 = Manufacturing, 2 = Non-Manufacturing, 3 = Emerging Markets.",
    )

    st.markdown(
        '<div style="font-size:0.72rem;color:#94a3b8;line-height:1.8;margin-top:0rem;">'
        '<b style="color:#64748b;">Allowed values</b><br>'
        '1 — Public Manufacturing<br>'
        '2 — Non-Manufacturing / Private<br>'
        '3 — Emerging Markets'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")
    run = st.button("Run Analysis")

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.72rem;color:#4B5563;line-height:1.6;">'
        '<b style="color:#6B7280;">Altman Z-Score (type 1)</b><br>'
        '<span style="color:#00C896;">■</span> Z > 2.99 — Safe Zone<br>'
        '<span style="color:#F5A623;">■</span> 1.81 ≤ Z ≤ 2.99 — Grey Zone<br>'
        '<span style="color:#E84545;">■</span> Z < 1.81 — Distress Zone'
        '</div>'
        '<div style="font-size:0.72rem;color:#4B5563;line-height:1.6;margin-top:0.6rem;">'
        '<b style="color:#6B7280;">Z\'- / Z\'\'- Score (type 2 & 3)</b><br>'
        '<span style="color:#00C896;">■</span> Z > 2.6 — Safe Zone<br>'
        '<span style="color:#F5A623;">■</span> 1.1 ≤ Z ≤ 2.6 — Grey Zone<br>'
        '<span style="color:#E84545;">■</span> Z < 1.1 — Distress Zone'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:0.72rem;color:#4B5563;line-height:1.6;margin-top:0.8rem;">'
        '<b style="color:#6B7280;">Merton Thresholds</b><br>'
        '<span style="color:#00C896;">■</span> PD < 1% — Safe Zone<br>'
        '<span style="color:#F5A623;">■</span> 1% ≤ PD < 15% — Grey Zone<br>'
        '<span style="color:#E84545;">■</span> PD ≥ 15% — Distress Zone'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:0.72rem;color:#4B5563;line-height:1.6;margin-top:0.8rem;">'
        '<b style="color:#6B7280;">Credit Decision</b><br>'
        '<span style="color:#00C896;">■</span> Both Safe → Approved<br>'
        '<span style="color:#6494ED;">■</span> One Safe → Approved with Caution<br>'
        '<span style="color:#F5A623;">■</span> Both Grey → Analysis Required<br>'
        '<span style="color:#E84545;">■</span> Any Distress → Dismissed'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:0.72rem;color:#4B5563;line-height:1.6;margin-top:0.8rem;">'
        '<b style="color:#6B7280;">Finantial Ratios</b><br>'
        'x1: Working Capital / Total Assets<br>'
        'x2: Retained Earnings / Total Assets<br>'
        'x3: EBIT / Total Assets<br>'
        'x4: Market Value of Equity / Book Value of Total Liabilities<br>'
        'x5: Sales / Total Assets'
        '</div>',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Main area
# ----------------------------------------------------------------------

if not run:
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:center;'
        'height:60vh;flex-direction:column;gap:1rem;">'
        '<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;'
        'color:#252A36;">Enter tickers and run analysis</div>'
        '<div style="font-size:0.82rem;color:#4B5563;">Results will appear here</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Parse tickers
tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
industry_types_raw = [i.strip() for i in industry_raw.split(",") if i.strip()]

if not tickers:
    st.warning("Please enter at least one ticker symbol.")
    st.stop()

if not industry_types_raw:
    st.warning("Please enter at least one industry type.")
    st.stop()

if len(industry_types_raw) != len(tickers):
    st.error(
        f"Mismatch: {len(tickers)} ticker(s) provided but "
        f"{len(industry_types_raw)} industry type(s). "
        f"Please provide one industry type per ticker."
    )
    st.stop()

try:
    industry_types = [int(v) for v in industry_types_raw]
except ValueError:
    st.error("Industry types must be integers: 1, 2, or 3.")
    st.stop()

invalid = [v for v in industry_types if v not in (1, 2, 3)]
if invalid:
    st.error(f"Invalid industry type(s): {invalid}. Must be 1, 2, or 3.")
    st.stop()

# ----------------------------------------------------------------------
# API calls with progress feedback
# ----------------------------------------------------------------------

results = []
errors  = []

progress = st.progress(0, text="Fetching financial data...")

for i, (ticker, industry_type) in enumerate(zip(tickers, industry_types)):
    try:
        data = call_api(ticker, industry_type)
        results.append(data)
    except requests.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        errors.append({"ticker": ticker, "error": detail})
    except Exception as exc:
        errors.append({"ticker": ticker, "error": str(exc)})

    progress.progress((i + 1) / len(tickers), text=f"Processing {ticker}...")

progress.empty()

# ----------------------------------------------------------------------
# Error display
# ----------------------------------------------------------------------

for err in errors:
    st.markdown(
        f'<div class="error-card">'
        f'<b>{err["ticker"]}</b> — {err["error"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

if not results:
    st.stop()


# ----------------------------------------------------------------------
# Individual company cards with ratio breakdown
# ----------------------------------------------------------------------

st.markdown(
    '<div class="section-header">Company Details</div>',
    unsafe_allow_html=True,
)

cols = st.columns(min(len(results), 3))

for idx, r in enumerate(results):
    col = cols[idx % len(cols)]

    altman_color = CLASSIFICATION_COLORS[r["classification"]]
    altman_bg    = CLASSIFICATION_BG[r["classification"]]

    merton       = r["merton"]
    merton_color = CLASSIFICATION_COLORS[merton["classification"]]
    merton_bg    = CLASSIFICATION_BG[merton["classification"]]
    dist_to_def   = merton["distance_to_default"]
    prob_pct     = merton["default_probability"] * 100

    decision     = r["combined_decision"]
    dec_color    = DECISION_COLORS[decision]
    dec_bg       = DECISION_BG[decision]

    ratios = r["ratios"]

    with col:
        st.markdown(
            f'<div class="metric-card">'

            # Ticker + model name
            f'<div class="metric-ticker">{r["ticker"]}</div>'

            f'<hr class="divider">'

            # Altman section
            f'<div class="metric-label">Altman Z-Score</div>'
            f'<div class="metric-score" style="color:{altman_color};">{r["z_score"]:.2f}</div>'
            f'<span class="badge" style="color:{altman_color};background:{altman_bg};">'
            f'{r["classification"]}</span>'

            f'<hr class="divider">'

            # Default distance section
            f'<div class="metric-label">Merton Distance to Default</div>'
            f'<div class="metric-score-sm" style="color:{merton_color};">{dist_to_def:.4f}</div>'
            f'<span class="badge" style="color:{merton_color};background:{merton_bg};">'
            f'{merton["classification"]}</span>'

            f'<hr class="divider">'

            # Default probability section
            f'<div class="metric-label">Merton Default Probability</div>'
            f'<div class="metric-score-sm" style="color:{merton_color};">{prob_pct:.2f}%</div>'
            f'<span class="badge" style="color:{merton_color};background:{merton_bg};">'
            f'{merton["classification"]}</span>'

            f'<hr class="divider">'

            # Combined decision
            f'<div class="metric-label">Credit Decision</div>'
            f'<span class="decision-badge" style="color:{dec_color};background:{dec_bg};">'
            f'{decision}</span>'

            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Ratio breakdown"):
            st.plotly_chart(
                build_spider_chart(ratios, r["ticker"], dec_color, RATIO_LABELS),
                width='stretch',
            )


# ----------------------------------------------------------------------
# Summary table
# ----------------------------------------------------------------------

st.markdown(
    '<div class="section-header">Summary Table</div>',
    unsafe_allow_html=True,
)

table_data = [
    {
        "Ticker":              r["ticker"],
        "Model":               r["model_name"],
        "Z-Score":             f'{r["z_score"]:.4f}',
        "Altman Zone":         r["classification"],
        "Distance to Default": f'{r["merton"]["distance_to_default"]:.4f}',
        "Default Prob (%)":    f'{r["merton"]["default_probability"] * 100:.2f}%',
        "Merton Zone":         r["merton"]["classification"],
        "Decision":            r["combined_decision"],
    }
    for r in results
]

df = pd.DataFrame(table_data)
st.dataframe(df, width='stretch', hide_index=True)