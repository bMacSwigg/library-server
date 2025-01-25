import os
import sys
import unittest

from libraryserver.config import AppConfig


class TestConfig(unittest.TestCase):

    def test_owner_dev(self):
        ac = AppConfig()
        self.assertEqual(ac.owner(), 'Brian')

    def test_owner_prod(self):
        ac = AppConfig(override_prod=True)
        self.assertEqual(ac.owner(), 'Brian')

    def test_firestorekey_dev(self):
        ac = AppConfig()
        expected_subpath = os.path.normpath('library-server/src/libraryserver/storage/run-web-efd188ab2632.json')
        self.assertIn(expected_subpath, ac.firestore_apikey_file())

    def test_firestorekey_prod(self):
        ac = AppConfig(override_prod=True)
        self.assertIsNone(ac.firestore_apikey_file())

    def test_logfile_dev(self):
        ac = AppConfig()
        expected_subpath = os.path.normpath('library-server/src/libraryserver/library.log')
        self.assertIn(expected_subpath, ac.log_file())

    def test_logfile_prod(self):
        ac = AppConfig(override_prod=True)
        self.assertIn('library.log', ac.log_file())


if __name__ == '__main__':
    unittest.main()
