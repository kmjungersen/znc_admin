from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
@app.route('/register')
def register(name=None):

    return render_template('templates/index.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)