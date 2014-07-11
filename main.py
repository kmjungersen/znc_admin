# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""SockJS Twisted Server

This server will wait for incoming connections on Localhost:4000,
take the user information sent to it, and then validate the username
with ZNC.

If the username has not been taken already, it will add the new user.

Due to security issues, and also for the sake of modularity, this script
has been made so that it can work with any ZNC server.  You can also
modify the IP address where your ZNC server is running.  See below.

To run the script:
    $ main.py <admin username> <admin password>

and in a separate terminal window to run the Flask app:
    $ app.py

"""

# Twisted Imports
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from twisted.python import log

#Twisted SockJS Imports
from txsockjs.factory import SockJSFactory as TXSockJSFactory
from txsockjs.utils import broadcast

#TODO - remove this
from znc_webadmin import ZNCServer

# system imports
import sys
import ast

from local import REGISTER_PORT


class SockJSProtocol(Protocol):
    """TwistedSockJSConnection is a Twisted protocol server object.
    """

    def __init__(self):
        """to start the ZNC server, you will need a username, password,
        and URI of the webadmin with which to connect.
        By default, as long as you have correctly configured local.py,
        it will automatically input these by default. Otherwise, you
        can change the below code to:

        self.znc_admin = ZNCServer(<your usermane>, <your password>,\
                                   <the uri of the target webadmin>)"""

        # self.znc_admin = ZNCServer()

        self.message = ''
        self.status = False

        # self.config_settings = {}
        #
        # config_file = 'znc_settings.conf'
        #
        # self.load_settings(config_file)

        # self.ZNC_IP_ADDRESS = ''
        # self.ZNC_PORT_NUMBER = 0000
        # self.REGISTRATION_PORT_NUMBER = 0000
        # self.ZNC_USERNAME = ''
        # self.ZNC_PASSWORD = ''


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

        It will take said data and begin the process of adding a user to ZNC.
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
                    the desired username and password

        Returns:
            desired_username: the username to be registered
            desired_password: the password for said user

        """

        user_info = ast.literal_eval(info)

        desired_username = user_info['username']

        desired_password = user_info['password']

        return desired_username, desired_password

    # def validate_username(self, username):
    #     """This function will check the list of users in ZNC and determine
    #     if the user's desired username is available.
    #
    #     Args:
    #         username: the username which the user wishes to use
    #
    #     Returns:
    #         status: a boolean describing whether or not the user may use
    #                 their desired username
    #         message: The success/error message that will be posted
    #                 to the user's registration page.
    #
    #     """
    #
    #     if username in self.znc_admin.users:
    #
    #         message = "This username has already been registered. Please choose another or contact your admin"
    #         return False, message
    #
    #     else:
    #
    #         message = 'Success! You are now registered.'
    #         return True, message

    def validate_username(self, username):
        """This function will check the list of users in ZNC and determine
        if the user's desired username is available.

        Args:
            username: the username which the user wishes to use

        Returns:
            status: a boolean describing whether or not the user may use
                    their desired username
            message: The success/error message that will be posted
                    to the user's registration page.

        """

        users = self.get_user_list()

        if username in users:

            message = "This username has already been registered. " \
                      "Please choose another or contact your admin"
            return False, message

        else:

            message = 'Success! You are now registered.'
            return True, message

    def get_user_list(self):

        users = []

        return users




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

        self.status, self.message = self.validate_username(username)

        if self.status:

            print 'Added a new user!  "' + username + '" is now registered.'

            self.znc_admin.add_user(username, password)

        broadcast(self.message, self.factory.transports)


class SockJSFactory(Factory):

    protocol = SockJSProtocol

    def __init__(self, irc_protocol):
        # self.irc = irc_protocol
        # self.msg = irc_protocol.msg
        # self.join = irc_protocol.join
        self.sendLine = irc_protocol.sendLine


class IRCInteraction(irc.IRCClient):

    nickname = znc_username
    password = znc_password

    def connectionMade(self):
        print 'IRC - Connection Made!'
        irc.IRCClient.connectionMade(self)
        self.factory.the_client = self

    def signedOn(self):
        print 'IRC - Signed On'
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        print 'IRC - Joined a Channel:: ', channel
        self.msg(channel, 'joined!')

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        elif msg.startswith(self.nickname + ":"):
            # msg = "%s: I am a log bot" % user
            print 'IRC - Sending message: msg'

            self.msg(channel, msg)
            self.sendLine(msg)
            return

    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'


class IRCFactory(protocol.ClientFactory):

    def __init__(self):
        self.channel = channel

    def buildProtocol(self, addr):
        p = IRCInteraction()
        p.factory = self
        return p

    def msg(self, msg):
        print 'IRC/SockJS - Sending message to channel: ', self.channel, msg
        self.the_client.msg(self.channel, msg)

    def sendLine(self, line):
        print 'IRC/SockJS - Sending line: ' + line
        self.the_client.sendLine(line)

# class SockJSProtocol(Protocol):
#
#     def __init__(self):
#         # self.msg = msg_fn
#         # self.message = ''
#         pass
#
#     def connectionMade(self):
#         print 'SockJS connected!'
#
#         if not hasattr(self.factory, "transports"):
#             self.factory.transports = set()
#         self.factory.transports.add(self.transport)
#
#     def dataReceived(self, data):
#         data = data.encode('utf-8')
#
#         if data.startswith('/'):
#             split_data = data.split(' ', 1)
#             function = split_data[0]
#             parameters = split_data[1]
#
#             if function == '/adduser':
#                 desired_username = split_data.split(' ', 1)
#                 # self.factory.join(data)
#                 self.factory.join(channel)
#
#             elif data.startswith('/me '):
#                 action = data.replace('/me ', '')
#                 self.factory.sendLine()
#
#             else:
#                 self.factory.sendLine()
#
#         self.factory.msg(data)




def load_settings(config_file_path):

    settings = {}

    with open(config_file_path) as infile:
        for line in infile:
            if not line.startswith('#') or line.startswith(' '):

                info = line.split('=', 1)

                variable = info[0]
                value = info[1]

                settings[variable] = value

    return settings


if __name__ == '__main__':

    log.startLogging(sys.stdout)

    config_file = 'znc_settings.conf'

    config_settings = load_settings(config_file)

    znc_ip = config_settings['ZNC_IP_ADDRESS']
    znc_port = int(config_settings['ZNC_PORT_NUMBER'])
    znc_username = config_settings['ZNC_USERNAME']
    znc_password = config_settings['ZNC_PASSWORD']

    register_port = int(config_settings['REGISTER_PORT'])
    channel = config_settings['DEFAULT_CHANNEL']



    if not channel.startswith('#'):
        channel = '#' + channel

    # Start building the factories
    irc_factory = IRCFactory()

    relay_factory = SockJSFactory(irc_factory)

    sockjs_factory = TXSockJSFactory(relay_factory)

    # Connects the IRC side of the bot
    reactor.connectTCP("irc.freenode.net", 6667, irc_factory)



    # Connects the SockJS side of the bot
    reactor.listenTCP(int(register_port), sockjs_factory)

    #TODO(kmjungersen) - add SSL support

    reactor.run()