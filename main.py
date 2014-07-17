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

# System Imports
import sys
import ast

# Import Settings
from load_settings import LocalSettings

# Import Docopt
from docopt import docopt

# CONFIG_FILE is the file pointer of our configuration file
CONFIG_FILE = 'znc_settings.conf'
settings = LocalSettings(CONFIG_FILE)


class UserAdmin():
    """ UserAdmin is an object that can be used by both the SockJS
    and IRC protocols to pass user information and perform actions between
    the two.  A single instance of this is used and can

    """

    def __init__(self):
        self.username = ''
        self.success_message = 'User [{}] added!'
        self.failure_message = 'Error: User [{}] already exists!'
        self.add_user_command = 'PRIVMSG *controlpanel adduser {0} {1}'

        self.user_action = {}

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

        self.new_user(username, password)

    def new_user(self, username, password):
        """ This function is called every time we need to create a new user.
        It simply sends the appropriate command to IRC.

        :param username: the username to be registered
        :param password: the password for the new user

        """

        self.username = username

        command = self.add_user_command.format(username, password)

        irc_factory.send_line(command)

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

        send_client_response(status_message)

        log_message(status_message)

        self.username = ''

    @staticmethod
    def parse_user_info(information):
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


# Declare an instance of UserAdmin for use on both the SockJS and IRC
# sides of the bot
USER_ACTION = UserAdmin()


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


class SockJSFactory(Factory):
    """ A SockJS Factory, which uses SockJSProtocol as the protocol.  This
    class inherits from the `Factory` parent class of Twisted/ TXSockJS.

    """

    protocol = SockJSProtocol

    def __init__(self):

        self.protocol = SockJSProtocol

    def send(self, message):
        """ This function simply sends a message via SockJS back to the client.
        It is defined outside of the protocol class so that it can be accessed
        outside of the instance of this factory class.

        :param message: the message to send back to the client

        """

        broadcast(message, self.transports)


class IRCProtocol(irc.IRCClient):
    """ This is the IRC Client Protocol class, which handles all interaction
    with IRC.  The nickname and password it uses to log in are derived from
    the config file.  This is necessary so the bot can log into ZNC as an
    admin, enabling the bot to actually perform user actions.

    """

    nickname = settings.znc_username
    password = settings.znc_password

    def __init__(self):
        """ Defines the 'control_panel' with which the bot will interact.
        Control_panel handles everything related to the addition/deletion
        of users.

        """
        self.control_panel = '*controlpanel'

    def connectionMade(self):
        """ This function is called when the bot successfully makes a new
        connection with IRC.

        """

        log_message('IRC - Connection Made!')

        irc.IRCClient.connectionMade(self)
        self.factory.the_client = self

    def signedOn(self):
        """ This function is called when the bot is successfully signed on to
        IRC.

        """

        log_message('IRC - Signed On')

        self.join(self.factory.channel)

    def joined(self, channel):
        """ This function is called when the bot joins the specified channel.

        :param channel: the channel that the bot has just joined

        """

        log_message('IRC - Joined a Channel: ' + channel)

        self.msg(channel, 'ZNC-Reg-Bot Joined!')

    def privmsg(self, user, channel, message):
        """ This function is called when the bot receives a message.  This is
        where we can interpret feedback from the ZNC control_panel.

        We do so by performing a logical evaluation to see if (a) the message
        is a response from control_panel or (b) if someone has sent the bot a
        private message.  It will ignore everything else.

        :param user: the user that sent the message
        :param channel: the channel that message was sent on
        :param message: the message sent on the specified channel by the
                        specified user
        """

        user = user.split('!', 1)[0]

        if user == self.control_panel:

            # Parse the information received back from control_panel
            USER_ACTION.parse_irc_feedback(message)

        elif channel == self.nickname:

            self.automated_response(user)

    def automated_response(self, user):
        """ This function allows us to return an automated response to a user.
        This is called when a user private-messages the bot, and includes a
        contact email address (configured in the config file).

        :param user: the user to send the message to

        """

        message = "I am a znc-registration bot.  For more " \
                  "information, please contact "\
                  + settings.contact_email

        log_message('IRC - Sending message: ' + message)

        self.msg(user, message)


class IRCFactory(protocol.ClientFactory):
    """ IRCFactory is a Twisted ClientFactory object.  It wraps the IRCClient
    protocol object, and enables us to interact with IRC functions outside of
    the object itself.

    """

    def __init__(self):

        self.channel = settings.channel

    def buildProtocol(self, address):
        """ This function is called when building the reactor, and it builds
        the IRC Protocol.

        :param address: The address to build the protocol with

        :return irc_protocol: an instance of the IRCProtocol object

        """

        irc_protocol = IRCProtocol()
        irc_protocol.factory = self

        return irc_protocol

    def message(self, message):
        """ This is the messaging function of IRC, which we've defined in the
        factory (seemingly redundantly) because then it can be used outside
        of the factory instance.  If verbose output is enabled, it will log
        this message to the terminal.

        :param message: the message to send to IRC

        """

        log_message('IRC/SockJS - Sending message to channel: ' +
                    self.channel + message)

        self.the_client.msg(self.channel, message)

    def send_line(self, line):
        """ This the sendLine function of IRC, which (much like `msg`) is
        defined (seemingly redundantly) here so it can be used outside of the
        factory instance.  This function will NOT log the line to the terminal
        because sensitive information (i.e. - passwords) are being passed
        through this function.

        :param line: the command line to send to IRC

        """

        self.the_client.sendLine(line)


def log_message(message):
    """ This function simply logs a message to the terminal output if 
    verbose output was selected when running the script initially.  Twisted
    has built in logging functionality, so if verbose output was enabled that
    will be too.  It will prepend a time stamp and some server information to
    the beginning of all messages printed through this function.

    :param message: the message to be logged

    """

    if verbose_output_enabled:

        print message


def send_client_response(return_message):
    """ This function simply sends the appropriate status message back
    to the user via SockJS.

    :param return_message: the message to be returned to the user

    """

    relay_factory.send(return_message)


if __name__ == '__main__':

    options = docopt(__doc__)

    if options['--verbose']:

        verbose_output_enabled = True

        log.startLogging(sys.stdout)

    else:

        verbose_output_enabled = False

        print 'Server started!'

    if not settings.channel.startswith('#'):
        join_channel = '#' + settings.channel

    # Start building the factories
    irc_factory = IRCFactory()

    relay_factory = SockJSFactory()

    sockjs_factory = TXSockJSFactory(relay_factory)

    # Connects the IRC side of the bot
    reactor.connectTCP(settings.znc_ip, settings.znc_port, irc_factory)

    # Connects the SockJS side of the bot
    port = int(settings.register_port)
    reactor.listenTCP(port, sockjs_factory)

    #TODO(kmjungersen) - add SSL support

    # Start the Twisted Reactor
    reactor.run()