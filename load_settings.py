from ConfigParser import RawConfigParser


class LocalSettings():

    def __init__(self, config_file='znc_settings.conf'):

        settings = self.load_settings(config_file)

        self.znc_ip = settings['znc_ip_address']
        self.znc_port = int(settings['znc_port_number'])

        self.znc_username = settings['znc_username']
        self.znc_password = settings['znc_password']

        self.username_chars = settings['username_characters']
        self.password_chars = settings['password_characters']

        self.register_port = int(settings['registration_port_number'])
        self.channel = settings['default_channel']
        self.contact_email = settings['contact_email']

        self.client_enabled = bool(settings['custom_irc_client_enabled'])
        self.client_ip = settings['client_ip_address']
        self.client_port = int(settings['client_port'])

    def load_settings(self, config_file_path):

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