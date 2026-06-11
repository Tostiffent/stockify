import json
import datetime as dt
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing, model_selection

valid_tickers = []

with open("valid_tickers.json", "r") as f:
  valid_tickers = json.loads(f.read())

_YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
}


def _history(ticker_sym, period, interval):
  df = yf.Ticker(ticker_sym).history(period=period, interval=interval)
  if df.index.tz is not None:
    df.index = df.index.tz_localize(None)
  return df


def get_stock_data(ticker_sym):
  name = ticker_sym
  market_cap = 0
  volume = 0
  country = "N/A"
  sector = "N/A"
  industry = "N/A"
  current_price = 0
  previous_close = 0
  day_high = 0
  day_low = 0
  week52_high = 0
  week52_low = 0
  currency = "USD"

  try:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_sym}?range=1d&interval=1d"
    r = requests.get(url, headers=_YF_HEADERS, timeout=5)
    meta = r.json()["chart"]["result"][0]["meta"]
    name = meta.get("longName") or meta.get("shortName") or ticker_sym
    volume = meta.get("regularMarketVolume", 0)
    current_price = meta.get("regularMarketPrice", 0)
    previous_close = meta.get("chartPreviousClose", 0)
    day_high = meta.get("regularMarketDayHigh", 0)
    day_low = meta.get("regularMarketDayLow", 0)
    week52_high = meta.get("fiftyTwoWeekHigh", 0)
    week52_low = meta.get("fiftyTwoWeekLow", 0)
    currency = meta.get("currency", "USD")
  except Exception:
    pass

  try:
    fi = yf.Ticker(ticker_sym).fast_info
    market_cap = int(fi.market_cap or 0)
    if not volume:
      volume = int(fi.last_volume or 0)
    if not current_price:
      current_price = fi.last_price or 0
    if not previous_close:
      previous_close = fi.previous_close or 0
    if not day_high:
      day_high = fi.day_high or 0
    if not day_low:
      day_low = fi.day_low or 0
    if not week52_high:
      week52_high = fi.year_high or 0
    if not week52_low:
      week52_low = fi.year_low or 0
  except Exception:
    pass

  try:
    info = yf.Ticker(ticker_sym).info
    country = info.get("country", "N/A")
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    if name == ticker_sym:
      name = info.get("shortName", ticker_sym)
    if not market_cap:
      market_cap = info.get("marketCap", 0)
  except Exception:
    pass

  price_change = round(current_price - previous_close, 2) if current_price and previous_close else 0
  price_change_pct = round((price_change / previous_close) * 100, 2) if previous_close else 0

  return {
      "shortName": name,
      "marketCap": market_cap,
      "country": country,
      "volume": volume,
      "sector": sector,
      "industry": industry,
      "currentPrice": current_price,
      "previousClose": previous_close,
      "dayHigh": day_high,
      "dayLow": day_low,
      "week52High": week52_high,
      "week52Low": week52_low,
      "currency": currency,
      "priceChange": price_change,
      "priceChangePct": price_change_pct,
  }


def is_valid_ticker(ticker_sym: str):
  return ticker_sym.upper() in valid_tickers


def graph_current_prices(ticker_sym, company_name):
  df = _history(ticker_sym, "1d", "1m")
  if df.empty:
    return None

  fig = go.Figure()
  fig.add_trace(go.Candlestick(
      x=df.index,
      open=df['Open'],
      high=df['High'],
      low=df['Low'],
      close=df['Close'],
      name='market data',
  ))
  fig.update_layout(
      title='{} Current stock prices'.format(company_name if company_name else ticker_sym.upper()),
      yaxis_title='Price (USD)',
  )
  fig.update_xaxes(
      rangeslider_visible=True,
      rangeselector=dict(
          buttons=list([
              dict(count=15, label="15m", step="minute", stepmode="backward"),
              dict(count=45, label="45m", step="minute", stepmode="backward"),
              dict(count=1, label="HTD", step="hour", stepmode="todate"),
              dict(count=3, label="3h", step="hour", stepmode="backward"),
              dict(step="all"),
          ])
      ),
  )
  fig.update_layout(
      paper_bgcolor="#14151b", plot_bgcolor="#14151b", font_color="white",
      xaxis_rangeselector_font_color='black',
      xaxis_rangeselector_activecolor='yellow',
      xaxis_rangeselector_bgcolor='white',
  )
  return json.dumps(fig, cls=PlotlyJSONEncoder)


def graph_predicted_prices(ticker_sym, no_of_days) -> str | None:
  no_of_days = int(no_of_days)
  if (not is_valid_ticker(ticker_sym)) or no_of_days < 0 or no_of_days > 365:
    return None

  df_ml = _history(ticker_sym, '3mo', '1h')
  if df_ml.empty:
    return None

  df_ml = df_ml[['Close', 'Volume']].copy()

  df_ml['ma5']  = df_ml['Close'].rolling(5).mean()
  df_ml['ma20'] = df_ml['Close'].rolling(20).mean()
  df_ml['mom']  = df_ml['Close'].pct_change(5)
  df_ml['vol_norm'] = df_ml['Volume'] / df_ml['Volume'].rolling(20).mean()
  df_ml.dropna(inplace=True)

  forecast_out = int(no_of_days)
  df_ml['Prediction'] = df_ml['Close'].shift(-forecast_out)
  df_ml.dropna(inplace=True)

  features = ['Close', 'ma5', 'ma20', 'mom', 'vol_norm']
  X = np.array(df_ml[features])
  X = preprocessing.scale(X)
  X_forecast = X[-forecast_out:]
  X = X[:-forecast_out]
  y = np.array(df_ml['Prediction'])
  y = y[:-forecast_out]

  X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=0.2)
  clf = LinearRegression()
  clf.fit(X_train, y_train)

  forecast_prediction = clf.predict(X_forecast)
  forecast = forecast_prediction.tolist()

  pred_dict = {"Date": [], "Prediction": []}
  for i in range(len(forecast)):
    pred_dict["Date"].append(dt.datetime.today() + dt.timedelta(days=i))
    pred_dict["Prediction"].append(forecast[i])

  pred_df = pd.DataFrame(pred_dict)
  fig = go.Figure([go.Scatter(x=pred_df['Date'], y=pred_df['Prediction'])])
  fig.update_xaxes(rangeslider_visible=True)
  fig.update_traces(line_color='#f5dd42')
  fig.update_layout(
      paper_bgcolor="#14151b", plot_bgcolor="#14151b",
      font_color="white", yaxis_title='Price (USD)',
  )
  return json.dumps(fig, cls=PlotlyJSONEncoder)


def graph_historical_prices(ticker_sym):
  df = _history(ticker_sym, '3mo', '1d')
  if df.empty:
    return None

  fig = go.Figure()
  fig.add_trace(go.Scatter(
      x=df.index, y=df['Close'],
      name='Close', line=dict(color='#00bfff', width=2),
      fill='tozeroy', fillcolor='rgba(0,191,255,0.07)',
  ))
  fig.update_layout(
      title=f'{ticker_sym.upper()} — Last 3 Months',
      yaxis_title='Price (USD)',
      paper_bgcolor="#14151b", plot_bgcolor="#14151b",
      font_color="white", showlegend=False,
      margin=dict(t=40, b=20),
  )
  fig.update_xaxes(rangeslider_visible=False, gridcolor='#2a2b33')
  fig.update_yaxes(gridcolor='#2a2b33')
  return json.dumps(fig, cls=PlotlyJSONEncoder)
