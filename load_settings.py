from ConfigParser import RawConfigParser


class LocalSettings():

    def __init__(self, config_file='znc_settings.conf'):

        settings = self.load_settings(config_file)

        self.znc_ip = settings['znc_ip_address']
        self.znc_port = int(settings['znc_port_number'])
        self.znc_username = settings['znc_username']
        self.znc_password = settings['znc_password']

        self.register_port = int(settings['registration_port_number'])
        self.channel = settings['default_channel']

    def load_settings(self, config_file_path):

        config = RawConfigParser()
        config.read(config_file_path)

        section = 'ZNC CONFIGURATION OPTIONS'
        options_list = config.options(section)

        config_settings = {}

        for option in options_list:
            config_settings[option] = config.get(section, option)

        return config_settings
