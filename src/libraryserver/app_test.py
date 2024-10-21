from firebase_admin import credentials, firestore, initialize_app
import json
import os
import requests
import unittest

# must be done before project imports
# TODO: maybe start emulator here?
LOCAL_EMULATOR = "localhost:8287"
os.environ["FIRESTORE_EMULATOR_HOST"] = LOCAL_EMULATOR

from libraryserver.storage.firestore_client import Database
from libraryserver.app import app

class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.db = Database(firestore.client())

    def tearDown(self):
        del_url = (
            "http://%s/emulator/v1/projects/run-web/databases/(default)/documents" %
            LOCAL_EMULATOR
        )
        requests.delete(del_url)

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
