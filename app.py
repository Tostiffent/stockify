from flask import Flask, render_template, request, url_for

app = Flask(__name__)

#serve website (base.html as base and index.html as template)
@app.route("/",methods=["POST", "GET"] )
def index(): 
    return render_template("base.html")

@app.route("/result",methods=["POST", "GET"] )
def result(): 
    return render_template("result.html")


if __name__ == "__main__":
    app.run(debug=True)


