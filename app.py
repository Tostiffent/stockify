from flask import Flask, render_template, request
from stock_prediction import graph_current_prices, graph_predicted_prices, get_stock_data
from flask import Flask, render_template, request, redirect

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
  company_name = stock_data["shortName"]
  market_cap = stock_data["marketCap"]
  country = stock_data["country"]
  volume = stock_data["volume"]
  sector = stock_data["sector"]
  industry = stock_data["industry"]

  live_price_graph = graph_current_prices(ticker_sym)
  predicted_price_graph = graph_predicted_prices(ticker_sym, days)

  return render_template("result.html", tickerSym=ticker_sym, companyName=company_name, 
                         noDays=days, marketCap=market_cap, country=country,
                         volume=volume, sector=sector, industry=industry,
                         liveGraphJson=live_price_graph, predictedGraphJson=predicted_price_graph)


if __name__ == "__main__":
  app.run(debug=True)
