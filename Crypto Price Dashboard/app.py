import pandas as pd
import plotly.express as px
import streamlit as st
import requests
import plotly.graph_objects as go

# ---------------------------
# Streamlit page setup
# ---------------------------
st.set_page_config(page_title="Crypto Price Dashboard", layout="wide")
st.title("📊 Crypto Price Dashboard")

# ---------------------------
# Helper functions
# ---------------------------
def get_ticker(symbol: str):
    """Fetch 24hr ticker stats from Binance public API."""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    resp = requests.get(url, params={"symbol": symbol}).json()
    if "symbol" in resp:
        return resp
    else:
        return None

def get_klines(symbol: str, interval: str, limit: int = 100):
    """Fetch OHLCV candlestick data from Binance public API."""
    url = "https://api.binance.com/api/v3/klines"
    resp = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}).json()
    if isinstance(resp, list):
        return resp
    else:
        return None

def get_cmc_data(symbol: str):
    """Fetch market cap and supply data from CoinMarketCap."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": symbol.replace("USDT", "")}
    headers = {"X-CMC_PRO_API_KEY": "d79fa2cb-f6e4-4ada-87b4-12d093df4d0d"} 
    resp = requests.get(url, headers=headers, params=params).json()
    return resp.get("data", {}).get(symbol.replace("USDT", ""), None)

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.header("Please filter here")
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
selected = st.sidebar.selectbox("Select a crypto pair", symbols)

# ---------------------------
# Fetch data safely
# ---------------------------
ticker = get_ticker(selected)
if ticker is None:
    st.error("Could not fetch ticker data from Binance.")
    st.stop()

coin_data = get_cmc_data(selected)
if coin_data is None:
    st.error("Could not fetch data from CoinMarketCap.")
    st.stop()

# ---------------------------
# Timeframe mapping
# ---------------------------
timeframe_dict = {
    "30 minutes": "30m",
    "1 hour": "1h",
    "4 hours": "4h",
    "12 hours": "12h",
    "1 day": "1d",
    "1 week": "1w",
    "1 month": "1M"
}
timeframe_list = list(timeframe_dict.keys())

# ---------------------------
# Metrics row
# ---------------------------
left_col, right_col = st.columns(2)
with left_col:
    st.metric(label="Coin Pair", value=ticker["symbol"])
with right_col:
    st.metric(label="Current Price (USD)", value=f"{float(ticker['lastPrice']):,.2f} USD")

st.subheader(f"{ticker['symbol']} Price Chart")

# ---------------------------
# Timeframe selector
# ---------------------------
left_col2, right_col2 = st.columns(2)
with right_col2:
    timeframe_selected_label = st.selectbox(
        "Select Timeframe",
        options=timeframe_list,
        index=0
    )
timeframe_selected = timeframe_dict[timeframe_selected_label]

# ---------------------------
# Klines data
# ---------------------------
klines = get_klines(selected, timeframe_selected)
if klines is None:
    st.error("Could not fetch candlestick data from Binance.")
    st.stop()

df = pd.DataFrame(klines, columns=[
    "Open time", "Open", "High", "Low", "Close", "Volume",
    "Close time", "Quote asset volume", "Number of trades",
    "Taker buy base", "Taker buy quote", "Ignore"
])
df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
df[["Open", "High", "Low", "Close"]] = df[["Open", "High", "Low", "Close"]].astype(float)

# ---------------------------
# Charts
# ---------------------------
price_chart_data = df.groupby("Open time")["High"].sum()
fig_by_line_chart = px.line(
    price_chart_data,
    x=price_chart_data.index,
    y=price_chart_data.values,
    labels={"x": "Time", "y": "Price (USD)"}
)
fig_by_line_chart.update_traces(
    hovertemplate="Time: %{x}<br>High Sum: %{y}<extra></extra>"
)

fig_by_candle = go.Figure(data=[go.Candlestick(
    x=df['Open time'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
)])
fig_by_candle.update_layout(
    title="Candlestick Chart",
    xaxis_title="Date",
    yaxis_title="Price",
    template="plotly_dark"
)

chart_dict = {
    "Line Chart": fig_by_line_chart,
    "Candles Chart": fig_by_candle,
}
with left_col2:
    chart_selected_label = st.selectbox("Select Chart Type", options=list(chart_dict.keys()), index=0)
chart_selected = chart_dict[chart_selected_label]
st.plotly_chart(chart_selected, use_container_width=True)

# ---------------------------
# Market cap, supply metrics
# ---------------------------
market_cap = coin_data["quote"]["USD"]["market_cap"]
max_supply = coin_data["max_supply"]
circulating_supply = coin_data["circulating_supply"]

left_col3, middle_col3, right_col3 = st.columns(3)
with left_col3:
    st.metric(label="Market Cap", value=f"${market_cap:,.0f}")
with middle_col3:
    if max_supply is None:
        st.metric(label="Max Supply", value=f"∞ {selected.replace('USDT','')}")
    else:
        st.metric(label="Max Supply", value=f"{max_supply:,.0f} {selected.replace('USDT','')}")
with right_col3:
    st.metric(label="Circulating Supply", value=f"{circulating_supply:,.0f} {selected.replace('USDT','')}")

# ---------------------------
# Extra charts: returns + closing price
# ---------------------------
left_col4, right_col4 = st.columns(2)
with left_col4:
    df["Returns"] = df["Close"].pct_change() * 100
    fig_by_dailyreturn = px.bar(df, x="Open time", y="Returns", title="Daily % Returns")
    st.plotly_chart(fig_by_dailyreturn, use_container_width=True)

with right_col4:
    fig_by_price = go.Figure()
    fig_by_price.add_trace(go.Scatter(x=df['Open time'], y=df['Close'],
                                      name="Closing Price", mode='lines+markers'))
    fig_by_price.update_layout(
        title="Closing Price Over Time",
        xaxis_title="Time",
        yaxis_title="Closing Price (USD)",
        template="plotly_white"
    )
    st.plotly_chart(fig_by_price, use_container_width=True)