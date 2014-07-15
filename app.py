""" ZNC WEB REGISTRATION APPLICATION
    --------------------------------

App.py houses the Flask app that serves the registration page.  The
settings for this our housed in a config file and then loaded into the app.
Client-side configuration is also loaded here and passed using JSON.

"""

from flask import Flask
from flask import render_template
from flask import jsonify

from mako.lookup import TemplateLookup
from load_settings import LocalSettings

CONFIG_FILE = 'znc_settings.conf'
settings = LocalSettings(CONFIG_FILE)

mako_lookup = TemplateLookup(directories=['templates'])

app = Flask(__name__)


def render_mako(tpl, **kwargs):
    """ This function renders the home page from a mako file in the
    'templates' directory.

    """
    return mako_lookup.get_template(tpl).render(**kwargs)

@app.route('/')
def home():
    """ The default address for the web app, which links users to the
    registration page, our own KiwiIRC Client, and the ZNC web administration
    page

    """

    znc_url = 'https://' + settings.znc_ip + ':' + \
          str(settings.znc_port) + '/'

    if settings.client_enabled:

        irc_client_url = 'http://' + settings.client_ip + ':' +\
            str(settings.client_port) + '/'

    else:

        irc_client_url = 'https://kiwiirc.com'

    return render_mako("index.mako", kiwi_url=irc_client_url, znc_url=znc_url)

@app.route('/register/')
def register():
    """ This function serves the 'register' page, on which users input the
    username and password they wish to use for IRC.

    Returns:
        template: a rendered webpage from an html file

    """

    template = render_template('register.html')

    return template

@app.route('/register/config/')
def config():
    """ The function called at this route retrieves settings from a
    configuration class

    """

    config_settings = jsonify(URI=settings.znc_ip,
                   USERNAME_CHARACTERS=settings.username_chars,
                   PASSWORD_CHARACTERS=settings.password_chars,
                   REGISTER_PORT=settings.register_port,
                   )

    return config_settings

if __name__ == '__main__':
    # Run the app
    app.run(settings.register_ip, debug=True)