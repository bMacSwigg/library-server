import os
import unittest
from datetime import datetime, UTC
import time

from libraryserver.api.models import Action
from libraryserver.storage.db import Database
from libraryserver.storage.testbase import BaseTestCase

class TestDatabase(BaseTestCase):

    TEST_DATABASE = ':memory:'
    LOGGER_NAME = 'libraryserver.storage.db'

    def setUp(self):
        self.db = Database(self.TEST_DATABASE)
        schema_path = os.path.join(os.path.split(__file__)[0], 'books.schema')
        with open(schema_path, 'r') as file:
            schema = file.read()
            self.db.con.cursor().executescript(schema)

    def tearDown(self):
        self.db.close()

    def test_check_tablesExist(self):
        with self.assertNoLogs(self.LOGGER_NAME, level='WARNING') as lc:
            self.db.check()

    def test_check_tablesMissing(self):
        self.db.con.cursor().execute('DROP TABLE Books')
        self.db.con.cursor().execute('DROP TABLE ActionLogs')
        self.db.con.cursor().execute('DROP TABLE Users')
        with self.assertLogs(self.LOGGER_NAME, level='WARNING') as lc:
            self.db.check()
            self.assertEqual(lc.output,
                             ['WARNING:libraryserver.storage.db:Table Books does not exist',
                              'WARNING:libraryserver.storage.db:Table ActionLogs does not exist',
                              'WARNING:libraryserver.storage.db:Table Users does not exist'])

    def test_book_putAndGet(self):
        self.db.putBook('some-isbn', 'Really Cool Book', 'Smart Person', 'Non-fiction', '1998', 'url')
        res = self.db.getBook('some-isbn')

        self.assertEqual(res, ('some-isbn', 'Really Cool Book', 'Smart Person', 'Non-fiction', '1998', 'url'))

    def test_book_list(self):
        self.db.putBook('isbn1', 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url')
        self.db.putBook('isbn2', 'Looking for Alaska', 'John Green', 'Fiction', '2005', 'url')

        res = self.db.listBooks()

        self.assertEqual(res,
                         [('isbn1', 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url'),
                          ('isbn2', 'Looking for Alaska', 'John Green', 'Fiction', '2005', 'url')])

    def test_book_listWithSearch(self):
        self.db.putBook('isbn1', 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url')
        self.db.putBook('isbn2', 'Looking for Alaska', 'John Green', 'Fiction', '2005', 'url')

        self.assertEqual(self.db.listBooks('for'),
                         [('isbn2', 'Looking for Alaska', 'John Green', 'Fiction', '2005', 'url')])
        self.assertEqual(self.db.listBooks('Kuang'),
                         [('isbn1', 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url')])
        self.assertEqual(self.db.listBooks('a'),
                         [('isbn1', 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url'),
                          ('isbn2', 'Looking for Alaska', 'John Green', 'Fiction', '2005', 'url')])

    def test_logs_putAndGet(self):
        self.db.putLog('some-isbn', Action.CREATE, 1234)

        res = self.db.getLatestLog('some-isbn')

        self.assertEqual(res[0], 'some-isbn')
        self.assertEqual(res[2], Action.CREATE.value)
        self.assertEqual(res[3], 1234)
        self.assertAboutNow(res[1])

    def test_logs_getsMostRecent(self):
        self.db.putLog('some-isbn', Action.CREATE, 1234)
        time.sleep(1)  # Hack to keep the timestamps from colliding
        self.db.putLog('some-isbn', Action.CHECKOUT, 5678)

        res = self.db.getLatestLog('some-isbn')

        self.assertEqual(res[0], 'some-isbn')
        self.assertEqual(res[2], Action.CHECKOUT.value)
        self.assertEqual(res[3], 5678)

    def test_logs_getsMatchingIsbn(self):
        self.db.putLog('isbn1', Action.CREATE, 1234)
        self.db.putLog('isbn2', Action.CHECKOUT, 5678)

        res = self.db.getLatestLog('isbn1')

        self.assertEqual(res[0], 'isbn1')
        self.assertEqual(res[2], Action.CREATE.value)
        self.assertEqual(res[3], 1234)

    def test_logs_noneMatching(self):
        res = self.db.getLatestLog('isbn1')

        self.assertEqual(res, ('isbn1', '', 0, 0))

    def test_logs_listByIsbn(self):
        self.db.putLog('isbn1', Action.CREATE, 1234)
        time.sleep(1)  # Hack to keep the timestamps from colliding
        self.db.putLog('isbn1', Action.CHECKOUT, 5678)
        self.db.putLog('isbn2', Action.CREATE, 9001)

        res = self.db.listLogsByIsbn('isbn1')

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], 'isbn1')
        self.assertEqual(res[0][2], Action.CREATE.value)
        self.assertEqual(res[0][3], 1234)
        self.assertEqual(res[1][0], 'isbn1')
        self.assertEqual(res[1][2], Action.CHECKOUT.value)
        self.assertEqual(res[1][3], 5678)

    def test_logs_listByUser(self):
        self.db.putLog('isbn1', Action.CHECKOUT, 1234)
        time.sleep(1)  # Hack to keep the timestamps from colliding
        self.db.putLog('isbn2', Action.RETURN, 1234)
        self.db.putLog('isbn3', Action.CHECKOUT, 5678)

        res = self.db.listLogsByUser(1234)

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], 'isbn1')
        self.assertEqual(res[0][2], Action.CHECKOUT.value)
        self.assertEqual(res[0][3], 1234)
        self.assertEqual(res[1][0], 'isbn2')
        self.assertEqual(res[1][2], Action.RETURN.value)
        self.assertEqual(res[1][3], 1234)

    def test_user_putAndGet(self):
        self.db.putUser(1234, 'John Doe', 'john@example.com')
        res = self.db.getUser(1234)

        self.assertEqual(res, (1234, 'John Doe', 'john@example.com'))

    def test_user_list(self):
        self.db.putUser(1234, 'John Doe', 'john@example.com')
        self.db.putUser(5678, 'Jane Doe', 'jane@example.com')

        res = self.db.listUsers()

        self.assertEqual(res,
                         [(1234, 'John Doe', 'john@example.com'),
                          (5678, 'Jane Doe', 'jane@example.com')])



if __name__ == '__main__':
    unittest.main()
