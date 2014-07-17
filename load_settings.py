"""
ZNC WEB REGISTRATION APPLICATION
---------------------------------

Load Settings Module

"""

from ConfigParser import RawConfigParser


class LocalSettings():
    """ This class houses all settings for the ZNC web registration app.

    Using `ConfigParser,` we can easily parse a configuration file to load
    all customizable options for the app.

    """

    def __init__(self, config_file='znc_settings.conf'):
        """ After declaring an instance of this class, settings from the
        config file can easily be accessed as attribute of that instance.


        :param config_file: the path for the config file the user wishes to use

        """

        settings = self.load_settings(config_file)

        self.znc_ip = settings['znc_ip_address']
        self.znc_port = int(settings['znc_port_number'])

        self.znc_username = settings['znc_username']
        self.znc_password = settings['znc_password']

        # self.channel = settings['default_channel']
        self.user_to_clone = settings['user_to_clone']

        self.username_chars = settings['username_characters']
        self.password_chars = settings['password_characters']

        self.register_ip = settings['registration_ip_address']
        self.register_port = int(settings['registration_port_number'])

        self.contact_email = settings['contact_email']

        self.client_enabled = bool(settings['custom_irc_client_enabled'])
        self.client_ip = settings['client_ip_address']
        self.client_port = int(settings['client_port'])

    @staticmethod
    def load_settings(config_file_path):
        """ This function creates the RawConfigParser object that parses
        settings from the config file.  It then takes those settings and
        creates a dict of the options which can then be made into attributes.

        :param config_file_path: the file path of the config file

        :return config_settings: a dict with all parsed settings from the file

        """

        config_settings = {}

        config = RawConfigParser()
        config.read(config_file_path)

        section_list = ['ZNC CONFIGURATION OPTIONS',
                        'WEB REGISTRATION CONSOLE OPTIONS',
                        'IRC CLIENT OPTIONS',
                        ]

        for section in section_list:

            options_list = config.options(section)

            for option in options_list:

                config_settings[option] = config.get(section, option)

        return config_settings