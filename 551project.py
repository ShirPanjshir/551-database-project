from flask import Flask
from flask import render_template
from flask import jsonify

app = Flask(__name__)

crimes = [{"date": 112923, "event": 340790, "case": 2306474, "offense": "assault", "location": "1100 Block of 37th PL"
           , "disposition": "cleared arrest"},
          {"date": 113023, "event": 340791, "case": 2306475, "offense": "theft", "location": "1200 Block of 37th PL"
              , "disposition": "open"},
          {"date": 113023, "event": 340792, "offense": "larceny", "location": "1100 Block of 37th PL"
              , "disposition": "open"},
          {"date": 113123, "event": 340793, "case": 2306476, "offense": "assault", "location": "1500 Block of 37th PL"
              , "disposition": "cleared arrest"},
          ]


@app.route("/")
def hello_world():
    return render_template('home.html', crimes=crimes)

@app.route("/api/crimes")
def list_crimes():
    return jsonify(crimes)

if __name__ == "__main__":
    app.run()