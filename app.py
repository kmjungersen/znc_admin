"""
ZNC WEB REGISTRATION APPLICATION
--------------------------------

App.py houses the Flask app that serves the registration page.  The
settings for this our housed in a config file and then loaded into the app.
Client-side configuration is also loaded here and passed using JSON.

"""

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import redirect

from load_settings import LocalSettings

CONFIG_FILE = 'znc_settings.conf'
settings = LocalSettings(CONFIG_FILE)

app = Flask(__name__)


@app.route('/')
def home():
    """ The default address for the web app, which links users to the
    registration page, our own KiwiIRC Client, and the ZNC web administration
    page

    :return render_template(): a rendered web page from an html file

    """

    return render_template('index.html')


@app.route('/Register/')
def register():
    """ This function serves the 'register' page, on which users input the
    username and password they wish to use for IRC.

    :return render_template(): a rendered web page from an html file

    """

    return render_template('register.html')


@app.route('/IRC_client/')
def load_irc_client():
    """ This function redirects to the IRC client page, which will either point
    to a self-hosted IRC client or a publicly hosted one.

    :return redirect(): a redirect command to a specific URL

    """

    if settings.client_enabled:

        irc_client_url = 'http://' + settings.client_ip + ':' +\
            str(settings.client_port) + '/'

    else:

        irc_client_url = 'https://kiwiirc.com'

    return redirect(irc_client_url)


@app.route('/ZNC_web_admin/')
def load_znc_admin():
    """ This function redirects to the ZNC web interface.

    :return redirect(): a redirect command to a specific URL

    """

    #TODO(kmjungersen) - change this back

    znc_url = 'http://' + settings.znc_ip + ':' + \
              str(settings.znc_port) + '/'

    return redirect(znc_url)


@app.route('/register/config/')
def config():
    """ The function called at this route retrieves settings from a
    configuration class

    :return config_settings: a JSON file with all settings that are needed
                             client-side

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