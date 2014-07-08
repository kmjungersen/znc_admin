from flask import Flask
from flask import render_template
from flask import jsonify
from local import URI, USERNAME_CHARACTERS, PASSWORD_CHARACTERS,\
    ZNC_WEBADMIN_PORT, KIWI_CLIENT_PORT, REGISTER_PORT
from mako.template import Template
from mako.lookup import TemplateLookup

mako_lookup = TemplateLookup(directories=['templates'])


def render_mako(tpl, **kwargs):
    return mako_lookup.get_template(tpl).render(**kwargs)

kiwi_url = 'http://'+URI+':'+KIWI_CLIENT_PORT+'/'
znc_url = 'https://'+URI+':'+ZNC_WEBADMIN_PORT+'/'

app = Flask(__name__)


@app.route('/')
def home():

    return render_mako("index.mako", kiwi_url=kiwi_url, znc_url=znc_url)

@app.route('/register/')
def register():

    return render_template("register.html")

@app.route('/register/config/')
def config():

    return jsonify(
        URI=URI,
        USERNAME_CHARACTERS=USERNAME_CHARACTERS,
        PASSWORD_CHARACTERS=PASSWORD_CHARACTERS,
        REGISTER_PORT=REGISTER_PORT)

if __name__ == '__main__':
    app.run("0.0.0.0", debug=True)