import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import requests
import plotly.graph_objects as go
import os

from binance.client import Client

api_key = os.environ.get("BINANCE_API_KEY", "")
api_secret = os.environ.get("BINANCE_API_SECRET", "")

client = Client(api_key, api_secret)


st.set_page_config(page_title="Crypto Price Dashboard", layout="wide")
st.title("📊Crypto Price Dashboard")

#side bar
st.sidebar.header("Please filter here")
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
selected = st.sidebar.selectbox("Select a crypto pair", symbols)

ticker = client.get_ticker(symbol=selected)

url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
params = {"symbol": selected.replace("USDT","")}
headers = {"X-CMC_PRO_API_KEY": "d79fa2cb-f6e4-4ada-87b4-12d093df4d0d"}
data = requests.get(url, headers=headers, params=params).json()

coin_data = data["data"][selected.replace("USDT","")]

timeframe_dict = {
    "30 minutes" : Client.KLINE_INTERVAL_30MINUTE,
    "1 hour" : Client.KLINE_INTERVAL_1HOUR,
    "4 hours" : Client.KLINE_INTERVAL_4HOUR,
    "12 hours" : Client.KLINE_INTERVAL_12HOUR,
    "1 day": Client.KLINE_INTERVAL_1DAY, 
    "1 week": Client.KLINE_INTERVAL_1WEEK, 
    "1 month": Client.KLINE_INTERVAL_1MONTH
}

timeframe_list = list(timeframe_dict.keys())

left_col, right_col = st.columns(2)

with left_col:
    st.metric(label="Coin Pair", value=f"{ticker['symbol']}")

with right_col:
    st.metric(label="Current Price (USD)", value = f"{float(ticker['lastPrice']):,.2f} USD")


st.subheader(f"{ticker["symbol"]} Price Cart")

left_col2, right_col2 = st.columns(2)

with right_col2:
    timeframe_selected_label = st.selectbox(
        "Select Timeframe",
        options=timeframe_list,
        index=0
    )

timeframe_selected = timeframe_dict[timeframe_selected_label]

klines = client.get_klines(symbol = selected, interval= timeframe_selected, limit=100)
df = pd.DataFrame(klines, columns=[
    "Open time", "Open", "High", "Low", "Close", "Volume",
    "Close time", "Quote asset volume", "Number of trades",
    "Taker buy base", "Taker buy quote", "Ignore"
])
df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
df[["Open", "High", "Low", "Close"]] = df[["Open", "High", "Low", "Close"]].astype(float)


price_chart_data = df.groupby("Open time") ["High"].sum()
fig_by_line_chart = px.line(
    price_chart_data,
    x=price_chart_data.index , 
    y=price_chart_data.values,
    labels={"x":"Time", "y":"Price (USD)"})

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
    "Line Chart" : fig_by_line_chart,
    "Candles Chart" : fig_by_candle,
}
chart_list = list(chart_dict.keys())

with left_col2:
    chart_selected_label = st.selectbox(
        "Select Chart Type",
        options= chart_list,
        index=0
    )

chart_selected = chart_dict[chart_selected_label]

st.plotly_chart(chart_selected, use_container_width=True)


market_cap = coin_data["quote"]["USD"]["market_cap"]
max_supply = coin_data["max_supply"]
circulating_supply = coin_data["circulating_supply"]

left_col3, middle_col3, right_col3 = st.columns(3)

with left_col3:
    st.metric(label="Market Cap", value=f"${market_cap:,.0f}")

with middle_col3:
    if max_supply is None:
        st.metric(label="Max Supply", value=f"∞ {selected.replace("USDT","")}")
    else:
        st.metric(label="Max Supply", value=f"{max_supply:,.0f} {selected.replace("USDT","")}")

with right_col3:
    st.metric(label="Circulating Supply", value=f"{circulating_supply:,.0f} {selected.replace("USDT","")}")

# ---------------------------
left_col4, right_col4 = st.columns(2)

with left_col4:
    df["Returns"] = df["Close"].pct_change() * 100
    fig_by_dailyreturn = px.bar(df, x="Open time", y="Returns", title="Daily % Returns")

left_col4.plotly_chart(fig_by_dailyreturn, use_container_width=True)

with right_col4:
    fig_by_price = go.Figure()
    fig_by_price.add_trace(go.Scatter(x=df['Open time'], y=df['Close'], name="Closing Price", mode='lines+markers'))
    fig_by_price.update_layout(
    title="Closing Price Over Time",
    xaxis_title="Time",
    yaxis_title="Closing Price (USD)",
    template="plotly_white"
    )

right_col4.plotly_chart(fig_by_price, use_container_width=True)
