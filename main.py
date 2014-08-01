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
from twisted.internet import reactor, protocol, ssl
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

# This creates a LocalSettings instance, through which all settings from the config file can be accessed
settings = LocalSettings()


class UserAdmin():
    """ UserAdmin is an object that can be used by both the SockJS
    and IRC protocols to pass user information and perform actions between
    the two.  A single instance of this is used and can handle all user
    actions.

    """

    def __init__(self):
        self.username = ''
        self.password = ''
        self.success_message = 'User [{}] added!'
        self.failure_message = 'Error: User not added! [User already exists]'

        self.command_dict = {
            'add_user': 'adduser <username> <password>',
            'set_value': 'set <variable> <username> <value>',
            'clone_user': 'cloneuser <user_to_clone> <username>',
            'change_password': 'set password <username> <password>',
            'set_network_value':
                        'setnetwork <variable> <username> <network> <value>',
        }

        self.variable_list = [
            'nick',
            'altnick',
            'ident',
            'realname',
        ]

        # TODO(kmjungersen) - add support for all commands

    def add_user_from_raw_data(self, data):
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
        It simply sends the appropriate command to IRC, which clones an
        existing template user.

        :param username: the username to be registered
        :param password: the password for the new user

        """

        self.username = username
        self.password = password

        # Clones User
        command = self.render_command('clone_user',
                                      username=username,
                                      password=password,
                                      )

        send_irc_command(command)

    def finish_creating_user(self, status_message, valid_user):
        """ This function is called after feedback has been received from IRC
        on whether or not the new user can be added.  If they can, it will
        continue to alter their settings (such as username and password).  If
        not, it will only return the status message to the client.

        :param status_message: the message that will be returned to the client
        :param valid_user: a Bool describing whether or not the username
                            is available

        """
        if valid_user:

            self.alter_user_settings()

        send_client_response(status_message)

        log_message(status_message)

        self.username = ''
        self.password = ''

    def alter_user_settings(self):
        """ This function changes the necessary user settings, particularly
        the password, nick, altnick, ident, and realname.

        """

        # Change Password
        command = self.render_command('change_password',
                                      username=self.username,
                                      password=self.password,
                                      )

        send_irc_command(command)

        # Change other info
        for item in self.variable_list:

            command = self.render_command('set_value',
                                          username=self.username,
                                          password=self.password,
                                          variable=item,
                                          value=self.username,
                                          )

            send_irc_command(command)

        command = self.render_command('set_network_value',
                                      variable='altnick',
                                      username=self.username,
                                      network='Freenode',
                                      value=self.username,
                                      )

        send_irc_command(command)

    def render_command(self, operation, username='', password='', variable='',
                       value='', network=''):
        """ This function renders the appropriate command to send to ZNC.  It
        will pull the correct template command from `self.command_dict` based
        on the operation value passed here.  Then it will use any optional
        arguments passed into the function and replace all template values
        before returning the complete command.

        :param operation: the operation to be completed
        :param username: the desired new username (default = '')
        :param password: the desired new password (default = '')
        :param variable: the ZNC variable to be changed (default = '')
        :param value: the desired value for the ZNC variable being changed
                        (default = '')

        :return command: the formatted command, which can then be sent to ZNC

        """
        replacements = {
            '<user_to_clone>': settings.user_to_clone,
            '<username>': username,
            '<password>': password,
            '<variable>': variable,
            '<value>': value,
            '<network>': network,
        }

        command = self.command_dict[operation]

        for key, value in replacements.iteritems():

            command = command.replace(key, value)

        return command

    def parse_irc_feedback(self, feedback):
        """ This function takes the feedback from ZNC (via IRC) and parses
        it to determine the status of the registration.  It then
        returns the appropriate success/failure message to the client.

        :param feedback: the string of feedback received from ZNC

        """

        status_message = ''
        valid_user = False

        if feedback == self.success_message.format(self.username):

            status_message = 'Success!  ' + feedback
            valid_user = True

        elif feedback == self.failure_message.format(self.username):

            status_message = feedback
            valid_user = False

        self.finish_creating_user(status_message, valid_user)

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

        USER_ACTION.add_user_from_raw_data(raw_data)

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

        irc.IRCClient.connectionMade(self)
        self.factory.the_client = self

        log_message('IRC - Connection Made!')

    def signedOn(self):
        """ This function is called when the bot is successfully signed on to
        IRC.

        """

    def joined(self, channel):
        """ This function is called when the bot joins the specified channel.

        :param channel: the channel that the bot has just joined

        """

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

        # log_message('IRC - Sending message: ' + message)

        self.msg(user, message)


class IRCFactory(protocol.ClientFactory):
    """ IRCFactory is a Twisted ClientFactory object.  It wraps the IRCClient
    protocol object, and enables us to interact with IRC functions outside of
    the object itself.

    """

    def __init__(self):
        """ (Class has no attributes)

        """

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


def send_irc_command(command, prefix='PRIVMSG *controlpanel '):
    """ This function simply sends a specified command to IRC.

    :param command: a command to send to IRC/ZNC
    :param prefix: The prefix to add to the command, which defaults to the
                    prefix necessary for doing most user actions with ZNC

    """

    irc_command = prefix + command

    irc_factory.send_line(irc_command)


if __name__ == '__main__':

    options = docopt(__doc__)

    if options['--verbose']:

        verbose_output_enabled = True

        log.startLogging(sys.stdout)

    else:

        verbose_output_enabled = False

        print 'Server started!'

    # Start building the factories
    irc_factory = IRCFactory()

    relay_factory = SockJSFactory()

    sockjs_factory = TXSockJSFactory(relay_factory)

    # Connects the IRC side of the bot using SSL
    reactor.connectSSL(settings.znc_ip, settings.znc_port, irc_factory,
                       ssl.ClientContextFactory())

    # Connects the SockJS side of the bot
    port = int(settings.register_port)
    reactor.listenTCP(port, sockjs_factory)

    # Start the Twisted Reactor
    reactor.run()