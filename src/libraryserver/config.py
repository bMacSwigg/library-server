import configparser
import os
import requests
import sys


class AppConfig:

    def __init__(self, override_prod=False):
        if override_prod or self._gcp():
            config_set = 'prod'
        else:
            config_set = 'dev'
        self.root = os.path.dirname(__file__)
        config_base = configparser.ConfigParser()
        config_base.read(os.path.join(self.root, 'config.ini'))
        self.config = config_base[config_set]

    def _gcp(self):
        try:
            requests.get("http://metadata.google.internal/computeMetadata/v1/instance/tags")
            return True
        except Exception as e:
            return False

    def owner(self):
        return self.config['Owner']

    def apikey_file(self):
        if not 'ApiKeyPath' in self.config:
            return None
        paths = self.config['ApiKeyPath'].split(',')
        return os.path.join(self.root, *paths)

    def firestore_apikey_file(self):
        if not 'FirestoreApiKeyPath' in self.config:
            return None
        paths = self.config['FirestoreApiKeyPath'].split(',')
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
    
