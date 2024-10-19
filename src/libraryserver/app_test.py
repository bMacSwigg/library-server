import json
import os
import time
import unittest

from libraryserver.storage.db import Database
from libraryserver.storage.db import __file__ as schema_root
from libraryserver.config import APP_CONFIG
from libraryserver.app import app

# sqlite doesn't seem to do a good job of wiping in-memory DBs
DB_NAME = __name__ + str(int(time.time()))
DB_FILE = "file:%s?mode=memory&cache=shared" % DB_NAME
print("using DB file '%s'" % DB_FILE)

class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        APP_CONFIG.db_file = lambda: DB_FILE
        cls.db = Database(APP_CONFIG.db_file())
        schema_path = os.path.join(os.path.dirname(schema_root), 'books.schema')
        with open(schema_path, 'r') as file:
            cls.schema = file.read()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.db.con.cursor().executescript(self.schema)

    def tearDown(self):
        self.db.con.cursor().execute('DROP TABLE Books')
        self.db.con.cursor().execute('DROP TABLE Users')
        self.db.con.cursor().execute('DROP TABLE ActionLogs')

    # Books API
    def test_getBook_exists(self):
        self.db.putBook('1234', 'A Book', 'Somebody', 'cat', 'year', 'img')

        res = self.client.get("/books/1234")

        data = json.loads(res.data.decode('UTF-8'))
        self.assertEqual(data['title'], 'A Book')
        self.assertEqual(data['author'], 'Somebody')

    def test_getBook_doesNotExist(self):
        res = self.client.get("/books/1234")

        self.assertEqual(res.status_code, 404)

    def test_listBooks_noQuery(self):
        self.db.putBook('1234', 'A Book', 'Somebody', 'cat', 'year', 'img')
        self.db.putBook('5678', 'Sequel', 'Somebody', 'cat', 'year', 'img')

        res = self.client.get("/books")

        data = json.loads(res.data.decode('UTF-8'))
        self.assertEqual(len(data), 2)

    def test_listBooks_query(self):
        self.db.putBook('1234', 'A Book', 'Somebody', 'cat', 'year', 'img')
        self.db.putBook('5678', 'Sequel', 'Somebody', 'cat', 'year', 'img')

        res = self.client.get("/books?query=sequel")

        data = json.loads(res.data.decode('UTF-8'))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Sequel')

    # Users API
    def test_listUserCheckoutHistory(self):
        self.db.putBook('1234', 'A Book', 'Somebody', 'cat', 'year', 'img')
        self.db.putBook('5678', 'Sequel', 'Somebody', 'cat', 'year', 'img')
        self.db.putUser(9999, 'user', 'fake-email')
        self.db.putUser(1111, 'other', 'other-email')

        self.client.post("/books/1234/checkout", json={'user_id': 9999})
        time.sleep(1)
        self.client.post("/books/1234/return")
        self.client.post("/books/5678/checkout", json={'user_id': 1111})

        res = self.client.get("/users/9999/history")

        data = json.loads(res.data.decode('UTF-8'))
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['isbn'], '1234')
        self.assertEqual(data[0]['action'], 2)  # Action.CHECKOUT
        self.assertEqual(data[0]['user_id'], 9999)
        self.assertEqual(data[0]['user_name'], 'user')
        self.assertEqual(data[1]['isbn'], '1234')
        self.assertEqual(data[1]['action'], 3)  # Action.RETURN
        self.assertEqual(data[1]['user_id'], 9999)
        self.assertEqual(data[1]['user_name'], 'user')


if __name__ == '__main__':
    unittest.main()
