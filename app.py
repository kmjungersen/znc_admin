from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def home():

    return render_template("home.html")

@app.route('/register/')
def register():

    return render_template("register.html")

if __name__ == '__main__':
    app.run("0.0.0.0", debug=True)
