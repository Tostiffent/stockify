from flask import Flask, render_template, request, redirect
from stock_prediction import graph_current_prices, graph_predicted_prices, graph_historical_prices, get_stock_data

app = Flask(__name__)

#serve website (base.html as base and index.html as template)
@app.route("/",methods=["POST", "GET"] )
def index(): 
    return render_template("landing.html")


@app.route("/predict", methods=["POST", "GET"])
def home():
  return render_template("predict.html")


@app.route("/result", methods=["POST", "GET"])
def result():
  ticker_sym = request.args.get("ticker")
  days = request.args.get("days")

  if not ticker_sym or not days:
    return redirect("/predict")

  stock_data = get_stock_data(ticker_sym)

  live_price_graph = graph_current_prices(ticker_sym, stock_data["shortName"])
  predicted_price_graph = graph_predicted_prices(ticker_sym, days)
  historical_graph = graph_historical_prices(ticker_sym)

  if not live_price_graph:
    app.logger.error("graph_current_prices returned None for %s", ticker_sym)
    return "Failed to fetch live price data", 400
  if not predicted_price_graph:
    app.logger.error("graph_predicted_prices returned None for %s", ticker_sym)
    return "Failed to fetch prediction data", 400

  return render_template("result.html",
    tickerSym=ticker_sym,
    noDays=days,
    companyName=stock_data["shortName"],
    marketCap=stock_data["marketCap"],
    country=stock_data["country"],
    volume=stock_data["volume"],
    sector=stock_data["sector"],
    industry=stock_data["industry"],
    currentPrice=stock_data["currentPrice"],
    previousClose=stock_data["previousClose"],
    dayHigh=stock_data["dayHigh"],
    dayLow=stock_data["dayLow"],
    week52High=stock_data["week52High"],
    week52Low=stock_data["week52Low"],
    currency=stock_data["currency"],
    priceChange=stock_data["priceChange"],
    priceChangePct=stock_data["priceChangePct"],
    liveGraphJson=live_price_graph,
    predictedGraphJson=predicted_price_graph,
    historicalGraphJson=historical_graph or "null",
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=False)
