import configparser
import os
import sys


class AppConfig:

    def __init__(self, override_prod=False):
        if getattr(sys, 'frozen', False) or override_prod:
            config_set = 'prod'
            # for files that live alongside the executable
            self.root = os.path.dirname(sys.executable)
            # for data files bundled into the executable
            self.tmp_root = sys._MEIPASS
        else:
            config_set = 'dev'
            # in development, these are the same
            self.root = os.path.dirname(__file__)
            self.tmp_root = self.root
        config_base = configparser.ConfigParser()
        config_base.read(os.path.join(self.tmp_root, 'config.ini'))
        self.config = config_base[config_set]

    def owner(self):
        return self.config['Owner']

    def db_file(self):
        paths = self.config['DbPath'].split(',')
        return os.path.join(self.root, *paths)

    def mailgun_apikey_file(self):
        if not 'MailgunApiKeyPath' in self.config:
            return None
        paths = self.config['MailgunApiKeyPath'].split(',')
        return os.path.join(self.root, *paths)

    def log_file(self):
        paths = self.config['LogPath'].split(',')
        return os.path.join(self.root, *paths)


APP_CONFIG = AppConfig()
    
