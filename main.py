# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
ZNC WEB REGISTRATION APPLICATION
---------------------------------

This file houses the registration server, which takes information
from the client registration Flask app and processes it accordingly.

    Usage:
        main.py [-v]

    Options:
        -h --help       Show this screen
        -v --verbose    Show verbose output in the server terminal

"""

# Twisted Imports
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from twisted.python import log

#Twisted SockJS Imports
from txsockjs.factory import SockJSFactory as TXSockJSFactory
from txsockjs.utils import broadcast

# system imports
import sys
import ast

# Import settings
from load_settings import LocalSettings

# Import docopt
from docopt import docopt

# CONFIG_FILE is the file pointer of our configuration file
CONFIG_FILE = 'znc_settings.conf'
settings = LocalSettings(CONFIG_FILE)

#TODO(kmjungersen) - add option for verbose output?


class UserObject():
    """ UserObject is an object that can be used by both the SockJS
    and IRC protocols to pass user information and perform actions between
    the two.  A single instance of this is used and can

    """

    def __init__(self):
        self.username = ''
        self.success_message = 'User [{}] added!'
        self.failure_message = 'Error: User [{}] already exists!'
        self.add_user_command = 'PRIVMSG *controlpanel adduser {0} {1}'

    def new_user(self, username, password):
        """ This function is called every time we need to create a new user.
        It simply sends the appropriate command to IRC.

        :param username: the username to be registered
        :param password: the password for the new user

        """

        self.username = username

        command = self.add_user_command.format(username, password)

        irc_factory.sendLine(command)

    def parse_irc_feedback(self, feedback):
        """ This function takes the feedback from ZNC (via IRC) and parses
        it to determine the status of the registration.  It then
        returns the appropriate success/failure message to the client.

        :param feedback: the string of feedback received from ZNC

        """

        status_message = ''

        if feedback == self.success_message.format(self.username):

            status_message = 'Success!  ' + feedback

        elif feedback == self.failure_message.format(self.username):

            status_message = feedback

        self.send_client_response(status_message)

        log_message(status_message)

    def send_client_response(self, return_message):
        """ This function simply sends the appropriate status message back
        to the user via SockJS.

        :param return_message: the message to be returned to the user

        """

        relay_factory.send(return_message)

# Declare an instance of UserObject for use on both the SockJS and IRC
# sides of the bot
USER_ACTION = UserObject()


class SockJSProtocol(Protocol):
    """ SockJSProtocol is a Twisted protocol server object.  It handles
    all SockJS interaction with the client-side registration.

    """

    def __init__(self):
        """ To start the ZNC server, you will need a username, password,
        and URI of the znc webadmin with which to connect.  These values are
        stored and can be modified in the config file defined above.

        """

    def connectionMade(self):
        """ The function that is called when a SockJS connection is made

        If the factory does not already have a transports attribute, it
        will add it before continuing.

        """

        log_message('SockJS - Connection Opened!')

        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)

    def dataReceived(self, raw_data):
        """ This function is called when data is received on the connection.

        It will take that data and begin the process of adding a user to ZNC.

        """

        raw_data = raw_data.encode('utf-8')

        self.add_user(raw_data)

    def connectionLost(self, reason=''):
        """ The function that is called when something severs the connection

        """

        log_message('Connection lost...')

    def parse_user_info(self, information):
        """ This function will take the data passed over the SockJS connection
        and convert it to a dict.  The data it is receiving is a string
        of a dict.

        :param information: the data passed over the connection, which includes
                            the desired username and password in the form of
                            a string

        :return: desired_username: the username to be registered
        :return: desired_password: the password for said user

        """

        # The literal conversion of a string to a dict
        user_info = ast.literal_eval(information)

        desired_username = user_info['username']

        desired_password = user_info['password']

        return desired_username, desired_password

    def add_user(self, data):
        """ This function will start the process of adding a new ZNC user.

        It begins by retrieving a username and password from the socket via
        `parse_user_info()`, and then validates the desired username. If
        successful, it will add the user to ZNC, and then relay the
        success/failure status and message back to the client.

        :param data: the raw data sent from the registration page client-side
                     to the server via a SockJS connection

        """

        username, password = self.parse_user_info(data)

        USER_ACTION.new_user(username, password)


class SockJSFactory(Factory):
    """ A SockJS Factory, using SockJSProtocol as the protocol

    """

    protocol = SockJSProtocol

    def __init__(self):
        self.protocol = SockJSProtocol

    def send(self, message):

        broadcast(message, self.transports)


class IRCProtocol(irc.IRCClient):

    nickname = settings.znc_username
    password = settings.znc_password

    def __init__(self):
        self.raw_user_list = []
        self.control_panel = '*controlpanel'

    def connectionMade(self):
        log_message('IRC - Connection Made!')
        irc.IRCClient.connectionMade(self)
        self.factory.the_client = self
        # self.raw_user_list = []

    def signedOn(self):
        log_message('IRC - Signed On')
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel.
        """

        log_message('IRC - Joined a Channel: ' + channel)
        self.msg(channel, 'ZNC-Reg-Bot Joined!')

    def privmsg(self, user, channel, message):
        """ Triggered when the bot receives a message.

        :param user: the user that sent the message
        :param channel
        """

        user = user.split('!', 1)[0]

        if user == self.control_panel:

            USER_ACTION.parse_irc_feedback(message)

        elif channel == self.nickname:

            self.automated_response(user)

    def automated_response(self, user):

        message = "I am a znc-registration bot.  For more " \
                  "information, please contact "\
                  + settings.contact_email

        log_message('IRC - Sending message: ' + message)

        self.msg(user, message)


class IRCFactory(protocol.ClientFactory):

    def __init__(self):

        self.channel = settings.channel

    def buildProtocol(self, addr):

        p = IRCProtocol()
        p.factory = self
        return p

    def msg(self, msg):

        log_message('IRC/SockJS - Sending message to channel: ' +
                    self.channel + msg)
        self.the_client.msg(self.channel, msg)

    def sendLine(self, line):

        self.the_client.sendLine(line)


def log_message(message):
    """ This function simply logs a message to the terminal output if 
    verbose output was selected when running the script
    
    """

    if verbose_output_enabled:

        print message

if __name__ == '__main__':

    options = docopt(__doc__)

    if options['--verbose'] == True:

        verbose_output_enabled = True

        log.startLogging(sys.stdout)

    if not settings.channel.startswith('#'):
        join_channel = '#' + settings.channel

    # Start building the factories

    # create_user = UserObject()

    irc_factory = IRCFactory()

    relay_factory = SockJSFactory()

    sockjs_factory = TXSockJSFactory(relay_factory)

    # Connects the IRC side of the bot
    reactor.connectTCP(settings.znc_ip, settings.znc_port, irc_factory)

    # Connects the SockJS side of the bot
    port = int(settings.register_port)
    reactor.listenTCP(port, sockjs_factory)

    #TODO(kmjungersen) - add SSL support

    options = docopt(__doc__)

    verbose_output_enabled = False

    if options['--verbose'] == True:
        
        verbose_output_enabled = True

    else:

        print 'Server started!'

    reactor.run()