# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

""" ZNC WEB REGISTRATION APPLICATION
    --------------------------------

    This file houses the registration server, which takes information
    from the client registration Flask app and processes it accordingly.



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
import ConfigParser
import sys
import ast
import re
from time import sleep

# Import settings
from load_settings import LocalSettings

# CONFIG_FILE is the file pointer of our configuration file
CONFIG_FILE = 'znc_settings.conf'
settings = LocalSettings(CONFIG_FILE)

#TODO(kmjungersen) - add option for verbose output?


class SockJSProtocol(Protocol):
    """ SockJSProtocol is a Twisted protocol server object.  It handles
        the SockJS interaction with the web-app.

    """

    def __init__(self):
        """To start the ZNC server, you will need a username, password,
        and URI of the znc webadmin with which to connect.  These values are
        stored and can be modified in 'znc_settings.conf'

        """

        # self.message = ''
        # self.status = False

    def connectionMade(self):
        """The function that is called when a SockJS connection is made

        If the factory does not already have a transports attribute, it
        will add it before continuing.

        """

        print 'SockJS - Connection Opened!'

        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)

    def dataReceived(self, data):
        """The function that is called when data is received on the connection

        It will take that data and begin the process of adding a user to ZNC.

        """

        data = data.encode('utf-8')

        self.add_user(data)

    def connectionLost(self, reason=''):
        """The function that is called when something severs the connection
        """

        print 'Connection lost...'

    def parse_user_info(self, info):
        """This function will take the data passed over the SockJS connection
        and convert it to a dict.  The data it is receiving is a string
        of a dict.

        Args:
            info: the data passed over the connection, which includes
                    the desired username and password in the form of
                    a string

        Returns:
            desired_username: the username to be registered
            desired_password: the password for said user

        """

        # The literal conversion of a string to a dict
        user_info = ast.literal_eval(info)

        desired_username = user_info['username']

        desired_password = user_info['password']

        return desired_username, desired_password

    # def validate_username(self, username):
    #     """TODO
    #
    #     """
    #




        # users = self.get_user_list()
        #
        # if username in users:
        #
        #     message = "This username has already been registered. " \
        #               "Please choose another or contact your admin"
        #     return False, message
        #
        # else:
        #
        #     message = 'Success! You are now registered.'
        #     return True, message

    # def get_user_list(self):
    #
    #     self.send_irc_command('PRIVMSG *controlpanel listusers')
    #
    #     while self.Receiving_Message:
    #         pass
    #
    #     raw_user_list = irc_factory.user_list
    #     print raw_user_list
    #     users = []
    #
    #     for i, line in enumerate(raw_user_list):
    #
    #         if not line.startswith('+') and 'Username' not in line:
    #             user = line.split('|', 1)[0]
    #
    #             # RegEx Substitution to remove any trailing whitespace
    #             user = re.sub('()\s+', '', user)
    #
    #             users.append(user)
    #
    #     IRCProtocol.raw_user_list = []
    #
    #     return users

    def add_user(self, data):
        """This function will start the process of adding a new ZNC user.

        It begins by retrieving a username and password from the socket via
        `parse_user_info()`, and then validates the desired username. If
        successful, it will add the user to ZNC, and then relay the
        success/failure status and message back to the client.

        Args:
            data: the raw data sent from the registration page client-side
                    to the server via a SockJS connection

        """

        username, password = self.parse_user_info(data)

        add_user_command = 'PRIVMSG *controlpanel adduser ' + \
                            username + ' ' + password

        self.send_irc_command(add_user_command)

        while irc_factory.receiving_message:
            pass

        message = ''

        if irc_factory.username_available:

            message = 'Success!  \n' \
                      'The user [' + username + '] is now registered with ZNC.'

        else:

            message = 'ERROR!  This username is already taken.  ' \
                      'Please try another!'

        print message

        broadcast(message, self.factory.transports)

        print 'New user added: [' + username + ']'

        irc_factory.username_available = False

    def send_irc_command(self, command):

        self.factory.sendLine(command)


class SockJSFactory(Factory):

    protocol = SockJSProtocol

    def __init__(self, irc_protocol):
        self.irc = irc_protocol
        # self.msg = irc_protocol.msg
        # self.join = irc_protocol.join
        self.sendLine = irc_protocol.sendLine

    # def send_line(self, line):
    #     self.irc.sendLine(line)


class IRCProtocol(irc.IRCClient):

    nickname = settings.znc_username
    password = settings.znc_password

    def __init__(self):
        self.raw_user_list = []

    def connectionMade(self):
        print 'IRC - Connection Made!'
        irc.IRCClient.connectionMade(self)
        self.factory.the_client = self
        # self.raw_user_list = []

    def signedOn(self):
        print 'IRC - Signed On'
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel.
        """

        print 'IRC - Joined a Channel: ', channel
        self.msg(channel, 'ZNC-Reg-Bot Joined!')

    def privmsg(self, user, channel, message):
        """This will get called when the bot receives a message.

        """

        # irc_factory.receiving_message = True

        user = user.split('!', 1)[0]
        print '========' + message

        # Checks to see if user messages the bot directly OR mentions
        # the bot's handle
        if channel == self.nickname\
                or message.startswith(self.nickname + ':'):

            # self.automated_response(user, channel)
            pass

        if user == '*controlpanel'\
                and message.startswith('Error: User [')\
                and message.endswith('] already exists!'):
            print 'FALSE!!!'
            irc_factory.username_available = False

        else:
            print 'TRUE!!!!'
            irc_factory.username_available = True

        irc_factory.receiving_message = False


    def automated_response(self, user, channel):

        out_message = "I am a znc-registration bot.  For more " \
                          "information, please contact "\
                          + settings.contact_email

        print 'IRC - Sending message: ' + out_message

        self.msg(user, out_message)


class IRCFactory(protocol.ClientFactory):

    def __init__(self):
        self.channel = settings.channel
        # self.p = self.buildProtocol()
        # self.user_list = []
        self.username_available = False
        self.receiving_message = False


    def buildProtocol(self, addr):
        p = IRCProtocol()
        p.factory = self
        return p

    def msg(self, msg):
        print 'IRC/SockJS - Sending message to channel: ', self.channel, msg
        self.the_client.msg(self.channel, msg)

    def sendLine(self, line):
        print 'IRC/SockJS - Sending line: ' + line
        receiving_message = True
        self.receiving_message = True
        self.the_client.sendLine(line)


if __name__ == '__main__':

    log.startLogging(sys.stdout)

    if not settings.channel.startswith('#'):
        channel = '#' + settings.channel

    # Start building the factories
    irc_factory = IRCFactory()

    relay_factory = SockJSFactory(irc_factory)

    sockjs_factory = TXSockJSFactory(relay_factory)

    # Connects the IRC side of the bot
    reactor.connectTCP(settings.znc_ip, settings.znc_port, irc_factory)

    # Connects the SockJS side of the bot
    port = int(settings.register_port)
    reactor.listenTCP(port, sockjs_factory)

    #TODO(kmjungersen) - add SSL support

    reactor.run()