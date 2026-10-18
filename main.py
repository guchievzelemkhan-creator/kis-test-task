from Flask import flask
app = flask(__name__)

@app.route("/")
def home():
    pass