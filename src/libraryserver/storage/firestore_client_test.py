import os
import unittest
from datetime import datetime, UTC
from firebase_admin import credentials, firestore, initialize_app
import requests

from libraryserver.api.models import Action
from libraryserver.storage.firestore_client import Database
from libraryserver.storage.testbase import BaseTestCase

LOCAL_EMULATOR = "localhost:8287"

class TestDatabase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        # TODO: maybe start emulator here?
        os.environ["FIRESTORE_EMULATOR_HOST"] = LOCAL_EMULATOR
        cred = credentials.Certificate('run-web-efd188ab2632.json')
        initialize_app(cred, {"projectId": "demo-project"})

    def setUp(self):
        self.db = Database(firestore.client())

    def tearDown(self):
        del_url = (
            "http://%s/emulator/v1/projects/demo-project/databases/(default)/documents" %
            LOCAL_EMULATOR
        )
        requests.delete(del_url)

    def test_book_putAndGet(self):
        self.db.putBook('some-isbn', 'Really Cool Book', 'Smart Person', 'Non-fiction', '1998', 'url')
        res = self.db.getBook('some-isbn').to_dict()

        self.assertEqual(res['isbn'], 'some-isbn')
        self.assertEqual(res['title'], 'Really Cool Book')
        self.assertEqual(res['author'], 'Smart Person')
        self.assertEqual(res['category'], 'Non-fiction')
        self.assertEqual(res['year'], '1998')
        self.assertEqual(res['img'], 'url')

    def test_book_getNotFound(self):
        res = self.db.getBook('does-not-exist')
        self.assertIsNone(res)

    def test_book_list(self):
        self.db.putBook('isbn1', 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url')
        self.db.putBook('isbn2', 'Looking for Alaska', 'John Green', 'Fiction', '2005', 'url')

        res = self.db.listBooks()

        self.assertEqual(len(res), 2)
        self.assertQueryDataMatches(
            res,
            [{"isbn": "isbn1",
              "title": "Babel",
              "author": "R.F. Kuang",
              "category": "Fiction",
              "year": "2022",
              "img": "url"},
             {"isbn": "isbn2",
              "title": "Looking for Alaska",
              "author": "John Green",
              "category": "Fiction",
              "year": "2005",
              "img": "url"}])

    def test_book_listWithSearch(self):
        self.db.putBook('isbn1', 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url')
        self.db.putBook('isbn2', 'Looking for Alaska', 'John Green', 'Fiction', '2005', 'url')

        babel_dict = {
            "isbn": "isbn1",
            "title": "Babel",
            "author": "R.F. Kuang",
            "category": "Fiction",
            "year": "2022",
            "img": "url"}
        lfa_dict = {
            "isbn": "isbn2",
            "title": "Looking for Alaska",
            "author": "John Green",
            "category": "Fiction",
            "year": "2005",
            "img": "url"}
        self.assertQueryDataMatches(self.db.listBooks('for'), [lfa_dict])
        self.assertQueryDataMatches(self.db.listBooks('Kuang'), [babel_dict])
        self.assertQueryDataMatches(
            self.db.listBooks('a'),
            [babel_dict, lfa_dict])

    def test_logs_putAndGet(self):
        self.db.putLog('some-isbn', Action.CREATE, 1234)

        res = self.db.getLatestLog('some-isbn').to_dict()

        self.assertEqual(res['isbn'], 'some-isbn')
        self.assertEqual(res['action'], Action.CREATE.value)
        self.assertEqual(res['user_id'], 1234)
        self.assertAboutNow(res['timestamp'])

    def test_logs_getsMostRecent(self):
        self.db.putLog('some-isbn', Action.CREATE, 1234)
        self.db.putLog('some-isbn', Action.CHECKOUT, 5678)

        res = self.db.getLatestLog('some-isbn').to_dict()

        self.assertEqual(res['isbn'], 'some-isbn')
        self.assertEqual(res['action'], Action.CHECKOUT.value)
        self.assertEqual(res['user_id'], 5678)

    def test_logs_getsMatchingIsbn(self):
        self.db.putLog('isbn1', Action.CREATE, 1234)
        self.db.putLog('isbn2', Action.CHECKOUT, 5678)

        res = self.db.getLatestLog('isbn1').to_dict()

        self.assertEqual(res['isbn'], 'isbn1')
        self.assertEqual(res['action'], Action.CREATE.value)
        self.assertEqual(res['user_id'], 1234)

    def test_logs_noneMatching(self):
        res = self.db.getLatestLog('isbn1')

        self.assertIsNone(res)

    def test_logs_listByIsbn(self):
        self.db.putLog('isbn1', Action.CREATE, 1234)
        self.db.putLog('isbn1', Action.CHECKOUT, 5678)
        self.db.putLog('isbn2', Action.CREATE, 9001)

        res = self.db.listLogsByIsbn('isbn1')

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].to_dict()["isbn"], 'isbn1')
        self.assertEqual(res[0].to_dict()["action"], Action.CREATE.value)
        self.assertEqual(res[0].to_dict()["user_id"], 1234)
        self.assertEqual(res[1].to_dict()["isbn"], 'isbn1')
        self.assertEqual(res[1].to_dict()["action"], Action.CHECKOUT.value)
        self.assertEqual(res[1].to_dict()["user_id"], 5678)

    def test_logs_listByUser(self):
        self.db.putLog('isbn1', Action.CHECKOUT, 1234)
        self.db.putLog('isbn2', Action.RETURN, 1234)
        self.db.putLog('isbn3', Action.CHECKOUT, 5678)

        res = self.db.listLogsByUser(1234)

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].to_dict()["isbn"], 'isbn1')
        self.assertEqual(res[0].to_dict()["action"], Action.CHECKOUT.value)
        self.assertEqual(res[0].to_dict()["user_id"], 1234)
        self.assertEqual(res[1].to_dict()["isbn"], 'isbn2')
        self.assertEqual(res[1].to_dict()["action"], Action.RETURN.value)
        self.assertEqual(res[1].to_dict()["user_id"], 1234)

    def test_user_putAndGet(self):
        self.db.putUser(1234, 'John Doe', 'john@example.com')
        res = self.db.getUser(1234)

        self.assertEqual(res.id, "1234")
        self.assertEqual(res.get('name'), 'John Doe')
        self.assertEqual(res.get('email'), 'john@example.com')

    def test_user_list(self):
        self.db.putUser(1234, 'John Doe', 'john@example.com')
        self.db.putUser(5678, 'Jane Doe', 'jane@example.com')

        res = self.db.listUsers()

        self.assertQueryDataMatches(
            res,
            [{"name": 'John Doe',
               "email": 'john@example.com'},
              {"name": 'Jane Doe',
               "email": 'jane@example.com'}])

if __name__ == '__main__':
    unittest.main()
