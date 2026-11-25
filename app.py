import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timezone
from urllib.parse import quote

st.set_page_config(page_title="MarketPulse AI", page_icon="📈", layout="wide")

PH_TICKERS = {
    "BDO Unibank": "BDO.PS", "Bank of the Philippine Islands": "BPI.PS",
    "Ayala Corporation": "AC.PS", "SM Investments": "SM.PS",
    "SM Prime": "SMPH.PS", "PLDT": "TEL.PS", "Globe Telecom": "GLO.PS",
    "Jollibee Foods": "JFC.PS", "International Container Terminal": "ICT.PS",
    "Ayala Land": "ALI.PS", "ACEN": "ACEN.PS"
}
US_TICKERS = {
    "Apple": "AAPL", "Microsoft": "MSFT", "Nvidia": "NVDA",
    "Amazon": "AMZN", "Alphabet": "GOOGL", "Meta": "META",
    "Tesla": "TSLA", "JPMorgan": "JPM", "Exxon Mobil": "XOM",
    "Walmart": "WMT", "Boeing": "BA", "Coca-Cola": "KO"
}
INDICATORS = {
    "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow Jones": "^DJI",
    "PSEi": "PSEI.PS", "Gold": "GC=F", "Crude Oil": "CL=F",
    "US Dollar Index": "DX-Y.NYB", "USD/PHP": "PHP=X",
    "US 10Y Treasury": "^TNX"
}

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background:#101c2b;padding:14px;border-radius:12px;border:1px solid #24364b;}
.small-note {color:#91a4b8;font-size:0.85rem;}
</style>
""", unsafe_allow_html=True)

st.title("📈 MarketPulse AI")
st.caption("Philippines + United States • Economic signals, event radar and stock risk monitor")
st.info("This is an early-warning research tool, not a price-prediction system or investment advice. Market data may be delayed or unavailable depending on Yahoo Finance coverage.")

with st.sidebar:
    st.header("Controls")
    market = st.multiselect("Markets", ["Philippines", "United States"], default=["Philippines", "United States"])
    period = st.selectbox("Chart / signal lookback", ["1mo", "3mo", "6mo", "1y"], index=1)
    refresh = st.button("↻ Refresh data", use_container_width=True)
    st.divider()
    st.caption("Data sources: Yahoo Finance via yfinance; GDELT public news database.")
    st.caption("For production use, add licensed market/news feeds and a hosted backend.")

@st.cache_data(ttl=300, show_spinner=False)
def get_history(symbol, period):
    try:
        df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def get_events():
    # GDELT public DOC API; broad business/economy coverage in English.
    queries = [
        ("Global economy", '(economy OR inflation OR recession OR central bank OR interest rates)'),
        ("Geopolitics & trade", '(trade OR tariff OR sanctions OR conflict OR war OR shipping)'),
        ("Philippines", '(Philippines OR Manila OR Bangko Sentral) AND (economy OR market OR business OR inflation)'),
        ("United States", '(United States OR Federal Reserve OR Wall Street) AND (economy OR market OR jobs OR inflation)')
    ]
    rows = []
    for label, query in queries:
        try:
            url = "https://api.gdeltproject.org/api/v2/doc/doc"
            params = {"query": query, "mode": "ArtList", "format": "json",
                      "maxrecords": 12, "sort": "HybridRel"}
            data = requests.get(url, params=params, timeout=15,
                                headers={"User-Agent":"MarketPulseAI/1.0"}).json()
            for item in data.get("articles", []):
                rows.append({
                    "Scope": label,
                    "Headline": item.get("title", "Untitled"),
                    "Source": item.get("domain", ""),
                    "Published": item.get("seendate", ""),
                    "URL": item.get("url", "")
                })
        except Exception:
            continue
    if not rows:
        return pd.DataFrame(columns=["Scope","Headline","Source","Published","URL"])
    df = pd.DataFrame(rows).drop_duplicates(subset=["URL"])
    return df

def signal_for(symbol, period):
    df = get_history(symbol, period)
    if df.empty or len(df) < 8:
        return None
    close = df["Close"].dropna()
    last = float(close.iloc[-1])
    d1 = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
    d5 = float((close.iloc[-1] / close.iloc[-6] - 1) * 100) if len(close) >= 6 else np.nan
    vol = float(close.pct_change().dropna().tail(20).std() * np.sqrt(252) * 100)
    # Explainable alert score: unusual recent movement + volatility. Not a forecast.
    score = min(100, abs(d5) * 4 + vol * 0.45)
    direction = "Positive momentum" if d5 > 1 else "Negative momentum" if d5 < -1 else "Mixed / flat"
    risk = "High" if score >= 35 else "Elevated" if score >= 20 else "Normal"
    return {"Ticker": symbol, "Last": last, "1D %": d1, "5D %": d5,
            "Ann. volatility %": vol, "Alert score": score,
            "Momentum": direction, "Risk": risk}

if refresh:
    st.cache_data.clear()

# Macro / index cards
st.subheader("Market & economy pulse")
symbols = list(INDICATORS.items())
cols = st.columns(5)
for i, (name, sym) in enumerate(symbols):
    if name == "PSEi" and "Philippines" not in market:
        continue
    if name != "PSEi" and name not in ["USD/PHP"] and "United States" not in market:
        continue
    hist = get_history(sym, "5d")
    with cols[i % 5]:
        if not hist.empty and len(hist) >= 2:
            val = float(hist["Close"].iloc[-1])
            change = float((hist["Close"].iloc[-1] / hist["Close"].iloc[-2] - 1) * 100)
            st.metric(name, f"{val:,.2f}", f"{change:+.2f}%")
        else:
            st.metric(name, "N/A", "No feed")

st.divider()
left, right = st.columns([1.1, 1])

with left:
    st.subheader("Event radar")
    with st.spinner("Checking recent headlines..."):
        events = get_events()
    if events.empty:
        st.warning("News feed did not return results. Try refreshing later.")
    else:
        scope = st.multiselect("Filter event coverage", events["Scope"].unique().tolist(),
                               default=events["Scope"].unique().tolist())
        shown = events[events["Scope"].isin(scope)].head(24)
        for _, row in shown.iterrows():
            headline = str(row["Headline"])
            st.markdown(f"**[{headline}]({row['URL']})**")
            st.caption(f"{row['Scope']} · {row['Source']} · {row['Published']}")
            st.write("")

with right:
    st.subheader("What to watch")
    st.markdown("""
    **Common transmission channels**
    - Higher oil prices can pressure airlines, transport and fuel-intensive businesses.
    - Higher interest rates can weigh on highly indebted firms and rate-sensitive property stocks.
    - A stronger US dollar can raise imported-cost pressure for some Philippine companies.
    - Supply-chain disruption can affect exporters, shipping and manufacturers.

    Headlines are not automatically treated as causal signals. Confirm the facts and check company exposure before acting.
    """)
    st.subheader("Quick market context")
    st.write(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (your device time)")

st.divider()
st.subheader("Stock risk & momentum scanner")
universe = {}
if "Philippines" in market:
    universe.update({f"{n} (PH)": t for n, t in PH_TICKERS.items()})
if "United States" in market:
    universe.update({f"{n} (US)": t for n, t in US_TICKERS.items()})

rows = []
progress = st.progress(0)
items = list(universe.items())
for idx, (name, ticker) in enumerate(items):
    result = signal_for(ticker, period)
    if result:
        result["Company"] = name
        rows.append(result)
    progress.progress((idx + 1) / max(1, len(items)))
progress.empty()

if rows:
    table = pd.DataFrame(rows)
    table = table[["Company","Ticker","Last","1D %","5D %","Ann. volatility %","Alert score","Momentum","Risk"]]
    table = table.sort_values("Alert score", ascending=False)
    search = st.text_input("Search company or ticker")
    if search:
        table = table[table.apply(lambda r: search.lower() in str(r["Company"]).lower()
                                  or search.lower() in str(r["Ticker"]).lower(), axis=1)]
    st.dataframe(
        table.style.format({"Last":"{:,.2f}","1D %":"{:+.2f}","5D %":"{:+.2f}",
                            "Ann. volatility %":"{:.1f}","Alert score":"{:.0f}"}),
        use_container_width=True, hide_index=True
    )
    st.caption("Alert score ranks recent movement and realized volatility. It does not estimate the probability that a stock will rise or fall.")
else:
    st.warning("No stock history was returned. Check your internet connection or try again later.")

st.divider()
st.subheader("How to interpret the scanner")
c1, c2, c3 = st.columns(3)
c1.metric("Normal", "0–19", "Lower recent alert activity")
c2.metric("Elevated", "20–34", "Review news and exposure")
c3.metric("High", "35+", "Large movement / volatility; investigate")

st.caption("Not financial advice. Data availability, ticker mappings and timestamps may be imperfect. Verify all information with your broker and official company disclosures.")
