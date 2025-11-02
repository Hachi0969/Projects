import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import requests
from datetime import datetime, timedelta

# ---------------------------
# Streamlit page setup
# ---------------------------
st.set_page_config(page_title="Crypto Price Dashboard", layout="wide")
st.title("📊 Crypto Price Dashboard (CoinMarketCap)")

# ---------------------------
# Helper functions
# ---------------------------
def get_cmc_quote(symbol):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": st.secrets["CMC_API_KEY"]}
    params = {"symbol": symbol}
    resp = requests.get(url, headers=headers, params=params).json()
    return resp.get("data", {}).get(symbol, None)

def get_cmc_ohlcv(symbol, interval="daily", days=30):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"
    headers = {"X-CMC_PRO_API_KEY": st.secrets["CMC_API_KEY"]}
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "symbol": symbol,
        "time_start": start.isoformat(),
        "time_end": end.isoformat(),
        "interval": interval
    }
    resp = requests.get(url, headers=headers, params=params).json()
    return resp.get("data", {}).get("quotes", [])

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.header("Please filter here")
symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE"]
selected = st.sidebar.selectbox("Select a crypto", symbols)

timeframe_dict = {"Hourly": "hourly", "Daily": "daily"}
timeframe_label = st.sidebar.radio("Select timeframe", list(timeframe_dict.keys()))
timeframe = timeframe_dict[timeframe_label]

# ---------------------------
# Fetch data
# ---------------------------
quote = get_cmc_quote(selected)
if not quote:
    st.error("Could not fetch data from CoinMarketCap.")
    st.stop()

ohlcv = get_cmc_ohlcv(selected, interval=timeframe, days=30)
if not ohlcv:
    st.error("Could not fetch OHLCV data from CoinMarketCap.")
    st.stop()

# ---------------------------
# Metrics
# ---------------------------
usd_data = quote["quote"]["USD"]
left_col, middle_col, right_col = st.columns(3)
with left_col:
    st.metric("Symbol", selected)
with middle_col:
    st.metric("Current Price (USD)", f"{usd_data['price']:,.2f}")
with right_col:
    st.metric("Market Cap", f"${usd_data['market_cap']:,.0f}")

# ---------------------------
# Prepare OHLCV DataFrame
# ---------------------------
df = pd.DataFrame([{
    "time": pd.to_datetime(item["time_open"]),
    "open": float(item["quote"]["USD"]["open"]),
    "high": float(item["quote"]["USD"]["high"]),
    "low": float(item["quote"]["USD"]["low"]),
    "close": float(item["quote"]["USD"]["close"]),
    "volume": float(item["quote"]["USD"]["volume"])
} for item in ohlcv])

# ---------------------------
# Charts
# ---------------------------
fig_line = px.line(df, x="time", y="close", title=f"{selected} Closing Price ({timeframe_label})")
fig_candle = go.Figure(data=[go.Candlestick(
    x=df["time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"]
)])
fig_candle.update_layout(title=f"{selected} Candlestick Chart ({timeframe_label})")

chart_dict = {"Line Chart": fig_line, "Candlestick Chart": fig_candle}
chart_choice = st.selectbox("Select Chart Type", list(chart_dict.keys()))
st.plotly_chart(chart_dict[chart_choice], use_container_width=True)

# ---------------------------
# Extra: Returns chart
# ---------------------------
df["Returns"] = df["close"].pct_change() * 100
fig_returns = px.bar(df, x="time", y="Returns", title="Daily % Returns")
st.plotly_chart(fig_returns, use_container_width=True)