import unittest

from libraryserver.keys.keymanager import KeyManager

class TestKeyManager(unittest.TestCase):

    def test_local(self):
        km = KeyManager(keyfile='keys-test.json')

        self.assertEqual(km.getKey('mailgun_api_key'), 'test-mailgun')
        self.assertEqual(km.getKey('books_api_key'), 'test-books')
        self.assertIsNone(km.getKey('other-name'))


if __name__ == '__main__':
    unittest.main()
