import unittest

from libraryserver.notifs.mailgun_client import Email

class TestMailgunClient(unittest.TestCase):

    def setUp(self):
        self.email = Email(keyfile=None)  # ensure we don't send any actual emails

    def test_validate_email(self):
        self.assertTrue(self.email._validate_email('jon.doe123@gmail.com'))
        self.assertTrue(self.email._validate_email('USER@alumni.princeton.edu'))
        self.assertFalse(self.email._validate_email('email'))
        self.assertFalse(self.email._validate_email('@gmail.com'))
        self.assertFalse(self.email._validate_email('foo@bar'))
                        

if __name__ == '__main__':
    unittest.main()
