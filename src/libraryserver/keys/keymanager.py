import json
import logging
from google.cloud import secretmanager

from libraryserver.config import APP_CONFIG

class KeyManager:
    """Fetches API keys, either from GCP (in production) or a local file (in dev)
    """

    KEY_TEMPLATE = "projects/869102415447/secrets/%s/versions/latest"

    def __init__(self, keyfile=APP_CONFIG.apikey_file()):
        self.logger = logging.getLogger(__name__)
        self.local = (keyfile is not None)
        self.keymap = {}

        if not self.local:
            self.secret_client = secretmanager.SecretManagerServiceClient()
            return

        try:
            with open(keyfile, 'r') as file:
                self.keymap = json.load(file)
        except FileNotFoundError as e:
            self.logger.error('Could not load API key', exc_info=e)
                    
    def getKey(self, name):
        if name in self.keymap:
            return self.keymap[name]

        if self.local:
            # all local keys loaded at startup
            return None
        else:
            key = self.secret_client.access_secret_version(
                request={"name": (KEY_TEMPLATE % name)}
            )
            return key.payload.data.decode("UTF-8")
    
        
