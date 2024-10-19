import unittest
from datetime import datetime, UTC

class BaseTestCase(unittest.TestCase):
    
    def assertAboutNow(self, time: str):
        # Check it's on the right date, since exact timestamps will differ
        now = datetime.now(UTC).date()
        logtime = datetime.fromisoformat(time).date()
        self.assertEqual(logtime, now)
