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

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from txsockjs.factory import SockJSFactory
from txsockjs.utils import broadcast

from znc_webadmin import ZNCServer
import sys
import ast


class TwistedSockJSConnection(Protocol):
    """TwistedSockJSConnection is a Twisted protocol server object.
    """

    def __init__(self):
        """We start by taking 2 command line arguments: the admin's
        username and password.  The URL is customizable, and can be passed
        with the UN and PWD; otherwise it will default to 107.170.134.161.

        Usage:

            znc_uri = <desired URI for ZNC>
            self.znc_admin = ZNCServer(admin_username, admin_password, znc_uri)

        """

        admin_username = sys.argv[1]
        admin_password = sys.argv[2]

        self.znc_admin = ZNCServer(admin_username, admin_password)

        self.message = ''
        self.status = False

    def connectionMade(self):
        """The function that is called when a SockJS connection is made

        If the factory does not already have a transports attribute, it
        will add it before continuing.
        """

        print 'Connection Opened!'

        if not hasattr(self.factory, "transports"):
            self.factory.transports = set()
        self.factory.transports.add(self.transport)



    def dataReceived(self, data):
        """The function that is called when data is received on the connection

        It will take said data and begin the process of adding a user to ZNC.
        """

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

        if username in self.znc_admin.users:

            message = "ERROR!!!  THIS USERNAME IS ALREADY TAKEN!"
            return False, message

        else:

            message = 'Success!!! You are now registered.'
            return True, message

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

#TODO(kmjungersen, asmacdo) - Add a logging class, to log user creations
#TODO                         to a file with timestamps, which will be
#TODO                         particularly important when deploying this
#TODO                         on the scale of the OSF user base.

if __name__ == '__main__':

    sockjs = SockJSFactory(Factory.forProtocol(TwistedSockJSConnection))

    reactor.listenTCP(4001, sockjs)

    #TODO(kmjungersen, asmacdo) - Add SSL support!!!

    reactor.run()