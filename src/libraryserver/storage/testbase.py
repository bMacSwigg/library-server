import unittest
from datetime import datetime, UTC

class BaseTestCase(unittest.TestCase):
    
    def assertAboutNow(self, time: str|datetime):
        # Check it's on the right date, since exact timestamps will differ
        now = datetime.now(UTC).date()
        if type(time) == str:
            date = datetime.fromisoformat(time).date()
        else:
            date = time.date()
        self.assertEqual(date, now)

    def assertQueryDataMatches(self, actual, expected):
        a = list(map(lambda res: res.to_dict(), actual))
        self.assertCountEqual(a, expected)
