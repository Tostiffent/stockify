import json
import os
import datetime as dt
import requests
import pandas as pd
import numpy as np
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing, model_selection

valid_tickers = []

with open("valid_tickers.json", "r") as f:
  valid_tickers = json.loads(f.read())

AV_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
AV_BASE = "https://www.alphavantage.co/query"


def _av(params):
  params["apikey"] = AV_KEY
  r = requests.get(AV_BASE, params=params, timeout=10)
  r.raise_for_status()
  return r.json()


def _intraday_df(ticker_sym, interval):
  data = _av({
      "function": "TIME_SERIES_INTRADAY",
      "symbol": ticker_sym,
      "interval": interval,
      "outputsize": "full",
  })
  key = f"Time Series ({interval})"
  ts = data.get(key, {})
  if not ts:
    return pd.DataFrame()
  df = pd.DataFrame.from_dict(ts, orient="index")
  df.index = pd.to_datetime(df.index)
  df = df.sort_index()
  df = df.rename(columns={
      "1. open": "Open",
      "2. high": "High",
      "3. low": "Low",
      "4. close": "Close",
      "5. volume": "Volume",
  })
  return df.astype(float)


def get_stock_data(ticker_sym):
  overview = _av({"function": "OVERVIEW", "symbol": ticker_sym})
  quote = _av({"function": "GLOBAL_QUOTE", "symbol": ticker_sym})
  gq = quote.get("Global Quote", {})
  return {
      "shortName": overview.get("Name", ticker_sym),
      "marketCap": int(overview.get("MarketCapitalization", 0) or 0),
      "country": overview.get("Country", "N/A"),
      "volume": int(gq.get("06. volume", 0) or 0),
      "sector": overview.get("Sector", "N/A"),
      "industry": overview.get("Industry", "N/A"),
  }


def is_valid_ticker(ticker_sym: str):
  return ticker_sym.upper() in valid_tickers


def graph_current_prices(ticker_sym, company_name):
  df = _intraday_df(ticker_sym, "1min")
  if df.empty:
    return None
  today = dt.datetime.today().date()
  df = df[df.index.date == today]
  if df.empty:
    df = _intraday_df(ticker_sym, "1min")

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

  df_ml = _intraday_df(ticker_sym, "60min")
  if df_ml.empty:
    return None

  cutoff = dt.datetime.today() - dt.timedelta(days=90)
  df_ml = df_ml[df_ml.index >= cutoff]

  df_ml = df_ml[['Close']].copy()
  forecast_out = int(no_of_days)
  df_ml['Prediction'] = df_ml[['Close']].shift(-forecast_out)

  X = np.array(df_ml.drop(['Prediction'], axis=1))
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
