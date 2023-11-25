import json
from sys import stderr
import pandas as pd
import yfinance as yf
import numpy as np
import datetime as dt
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing, model_selection

valid_tickers = []

with open("valid_tickers.json", "r") as f:
  valid_tickers = json.loads(f.read())


def get_stock_data(ticker_sym):
  data = yf.Ticker(ticker_sym)
  return data.info


def is_valid_ticker(ticker_sym: str):
  if ticker_sym.upper() in valid_tickers:
    return True
  return False


def graph_current_prices(ticker_sym, company_name):
  df: pd.DataFrame = yf.download(tickers=ticker_sym, period="1d", interval="1m")
  fig = go.Figure()
  fig.add_trace(go.Candlestick(x=df.index,
                               open=df['Open'],
                               high=df['High'],
                               low=df['Low'],
                               close=df['Close'], name='market data'))
  fig.update_layout(
      title='{} Current stock prices'.format(company_name if company_name else ticker_sym.upper()),
      yaxis_title='Price (USD)')
  fig.update_xaxes(
      rangeslider_visible=True,
      rangeselector=dict(
          buttons=list([
              dict(count=15, label="15m", step="minute", stepmode="backward"),
              dict(count=45, label="45m", step="minute", stepmode="backward"),
              dict(count=1, label="HTD", step="hour", stepmode="todate"),
              dict(count=3, label="3h", step="hour", stepmode="backward"),
              dict(step="all")
          ])
      )
  )
  fig.update_layout(paper_bgcolor="#14151b", plot_bgcolor="#14151b", font_color="white", 
                    xaxis_rangeselector_font_color='black',xaxis_rangeselector_activecolor='yellow',
                    xaxis_rangeselector_bgcolor='white',)

  return json.dumps(fig, cls=PlotlyJSONEncoder)


def graph_predicted_prices(ticker_sym, no_of_days) -> str | None:
  no_of_days = int(no_of_days)
  if (not is_valid_ticker(ticker_sym)) or no_of_days < 0 or no_of_days > 365:
    return None

  try:
    df_ml: pd.DataFrame = yf.download(tickers=ticker_sym, period='1mo', interval='1h')
    print(df_ml.shape)

  except Exception as e:
    print(e, file=stderr)

  # Fetching ticker values from Yahoo Finance API
  df_ml = df_ml[['Adj Close']]
  forecast_out = int(no_of_days)
  df_ml['Prediction'] = df_ml[['Adj Close']].shift(-forecast_out)
  # Splitting data for Test and Train
  X = np.array(df_ml.drop(['Prediction'], axis=1))
  X = preprocessing.scale(X)
  X_forecast = X[-forecast_out:]
  X = X[:-forecast_out]
  y = np.array(df_ml['Prediction'])
  y = y[:-forecast_out]
  X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=0.2)
  # Applying Linear Regression
  clf = LinearRegression()
  clf.fit(X_train, y_train)

  # Prediction Score R ^ 2
  confidence = clf.score(X_test, y_test)
  print(f"Confidence : {confidence * 100} %")

  # Predicting for 'n' days stock data
  forecast_prediction = clf.predict(X_forecast)
  forecast = forecast_prediction.tolist()

  # graph
  pred_dict = {"Date": [], "Prediction": []}
  for i in range(0, len(forecast)):
    pred_dict["Date"].append(dt.datetime.today() + dt.timedelta(days=i))
    pred_dict["Prediction"].append(forecast[i])

  pred_df = pd.DataFrame(pred_dict)
  fig = go.Figure([go.Scatter(x=pred_df['Date'], y=pred_df['Prediction'])])
  fig.update_xaxes(rangeslider_visible=True)
  fig.update_traces(line_color='#f5dd42')
  fig.update_layout(paper_bgcolor="#14151b", plot_bgcolor="#14151b",
                    font_color="white", yaxis_title='Price (USD)')

  return json.dumps(fig, cls=PlotlyJSONEncoder)
