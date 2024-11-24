from firebase_admin import credentials, firestore, initialize_app
import os
import requests
import unittest

from libraryserver.api.errors import InvalidStateException, NotFoundException
from libraryserver.api.models import Book, User, Action
from libraryserver.constants import MIN_USER_ID, MAX_USER_ID
from libraryserver.notifs.mailgun_client import FakeEmail
from libraryserver.storage.firestore_client import Database
from libraryserver.storage.local import LocalBookService, LocalUserService
from libraryserver.storage.testbase import BaseTestCase

LOCAL_EMULATOR = "localhost:8287"

# Start the emulator with `gcloud emulators firestore start --host-port=localhost:8287`
# TODO: maybe start emulator here?
os.environ["FIRESTORE_EMULATOR_HOST"] = LOCAL_EMULATOR
cred = credentials.Certificate('run-web-efd188ab2632.json')
initialize_app(cred, {"projectId": "demo-project"})

class TestBookService(BaseTestCase):

    def setUp(self):
        self.db = Database(firestore.client())
        self.books = LocalBookService(self.db)
        self.books.email = FakeEmail()
        self.users = LocalUserService(self.db)

    def tearDown(self):
        del_url = (
            "http://%s/emulator/v1/projects/demo-project/databases/(default)/documents" %
            LOCAL_EMULATOR
        )
        requests.delete(del_url)

    def test_getBook_exists(self):
        self.db.putBook('isbn1', 1, 'title', 'author', 'cat', 'year', 'img')

        book = self.books.getBook('isbn1')

        self.assertNotEqual(book.book_id, "")
        self.assertEqual(book.isbn, 'isbn1')
        self.assertEqual(book.owner_id, 1)
        self.assertEqual(book.title, 'title')
        self.assertEqual(book.author, 'author')
        self.assertEqual(book.category, 'cat')
        self.assertEqual(book.year, 'year')
        self.assertEqual(book.thumbnail, 'img')

    def test_getBook_setsDefaultLogVals(self):
        self.db.putBook('isbn1', 1, 'title', 'author', 'cat', 'year', 'img')

        book = self.books.getBook('isbn1')

        self.assertEqual(book.is_out, False)
        self.assertEqual(book.checkout_user, '')
        self.assertEqual(book.checkout_time, '')

    def test_getBook_setsCheckoutLogVals(self):
        book_id = self.db.putBook('isbn1', 1, 'title', 'author', 'cat', 'year', 'img')
        self.db.putUser(1234, 'somebody', 'test@example.com')
        self.db.putLog(book_id, Action.CHECKOUT, 1234)

        book = self.books.getBook('isbn1')

        self.assertEqual(book.is_out, True)
        self.assertEqual(book.checkout_user, 'somebody')
        self.assertAboutNow(book.checkout_time)

    def test_getBook_setsReturnLogVals(self):
        book_id = self.db.putBook('isbn1', 1, 'title', 'author', 'cat', 'year', 'img')
        self.db.putLog(book_id, Action.RETURN)

        book = self.books.getBook('isbn1')

        self.assertEqual(book.is_out, False)
        self.assertEqual(book.checkout_user, '')
        self.assertEqual(book.checkout_time, '')

    def test_getBook_setsCreateLogVals(self):
        book_id = self.db.putBook('isbn1', 1, 'title', 'author', 'cat', 'year', 'img')
        self.db.putLog(book_id, Action.CREATE)

        book = self.books.getBook('isbn1')

        self.assertEqual(book.is_out, False)
        self.assertEqual(book.checkout_user, '')
        self.assertEqual(book.checkout_time, '')

    def test_getBook_doesNotExist(self):
        with self.assertRaises(NotFoundException):
            self.books.getBook('isbn1')

    def test_listBooks(self):
        b1 = self.db.putBook('isbn1', 1234, 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url')
        b2 = self.db.putBook('isbn2', 1234, 'Looking For Alaska', 'John Green', 'Fiction', '2005', 'url')
        self.db.putBook('isbn3', 5678, 'Foo', 'Bar', 'Fiction', '2005', 'url')

        books = self.books.listBooks(1234)
        books.sort(key=lambda b: b.isbn)

        self.assertEqual(books[0].book_id, b1)
        self.assertEqual(books[0].isbn, 'isbn1')
        self.assertEqual(books[0].owner_id, 1234)
        self.assertEqual(books[0].title, 'Babel')
        self.assertEqual(books[0].author, 'R.F. Kuang')
        self.assertEqual(books[0].category, 'Fiction')
        self.assertEqual(books[0].year, '2022')
        self.assertEqual(books[0].thumbnail, 'url')
        self.assertEqual(books[1].book_id, b2)
        self.assertEqual(books[1].isbn, 'isbn2')
        self.assertEqual(books[1].owner_id, 1234)
        self.assertEqual(books[1].title, 'Looking For Alaska')
        self.assertEqual(books[1].author, 'John Green')
        self.assertEqual(books[1].category, 'Fiction')
        self.assertEqual(books[1].year, '2005')
        self.assertEqual(books[1].thumbnail, 'url')

    def test_listBooks_setsLogValues(self):
        self.db.putUser(1234, 'somebody', 'test@example.com')
        b1 = self.db.putBook('isbn1', 1, '', '', '', '', '')
        b2 = self.db.putBook('isbn2', 1, '', '', '', '', '')
        self.db.putLog(b1, Action.CREATE)
        self.db.putLog(b2, Action.CREATE)
        self.db.putLog(b1, Action.CHECKOUT, 1234)

        books = self.books.listBooks(1)
        books.sort(key=lambda b: b.isbn)

        self.assertEqual(books[0].isbn, 'isbn1')
        self.assertEqual(books[0].is_out, True)
        self.assertEqual(books[0].checkout_user, 'somebody')
        self.assertAboutNow(books[0].checkout_time)
        self.assertEqual(books[1].isbn, 'isbn2')
        self.assertEqual(books[1].is_out, False)
        self.assertEqual(books[1].checkout_user, '')
        self.assertEqual(books[1].checkout_time, '')

    def test_listBooks_withSearch(self):
        self.db.putBook('isbn1', 1, 'Babel', 'R.F. Kuang', 'Fiction', '2022', 'url')
        self.db.putBook('isbn2', 1, 'Looking For Alaska', 'John Green', 'Fiction', '2005', 'url')

        books = self.books.listBooks(1, 'looking')

        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].isbn, 'isbn2')
        self.assertEqual(books[0].title, 'Looking For Alaska')

    def test_listBooksByStatus_checkedOut(self):
        self.db.putUser(1234, 'somebody', 'test@example.com')
        b_in = self.db.putBook('isbn-in', 1, '', '', '', '', '')
        b_out = self.db.putBook('isbn-out', 1, '', '', '', '', '')
        self.db.putLog(b_in, Action.CREATE)
        self.db.putLog(b_out, Action.CHECKOUT, 1234)

        books = self.books.listBooksByStatus(1, True)

        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].isbn, 'isbn-out')

    def test_listBooksByStatus_checkedIn(self):
        self.db.putUser(1234, 'somebody', 'test@example.com')
        b_in = self.db.putBook('isbn-in', 1, '', '', '', '', '')
        b_out = self.db.putBook('isbn-out', 1, '', '', '', '', '')
        self.db.putLog(b_in, Action.CREATE)
        self.db.putLog(b_out, Action.CHECKOUT, 1234)

        books = self.books.listBooksByStatus(1, False)

        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].isbn, 'isbn-in')
        
    def test_createBook(self):
        book = Book(None, 'isbn1', 1, 'Paul', 'Andrea Lawler', 'Fiction', '2017', 'url')

        self.books.createBook(book)
        res = self.books.getBook('isbn1')

        self.assertEqualExceptId(res, book)

    def test_checkoutBook(self):
        book = Book(None, 'isbn1', 1, '', '', '', '', '')
        self.books.createBook(book)
        user = User(1234, 'user', 'user@example.com')
        self.db.putUser(user.user_id, user.name, user.email)
        self.books.checkoutBook('isbn1', user)

        res = self.books.getBook('isbn1')

        self.assertEqual(res.is_out, True)
        self.assertEqual(res.checkout_user, 'user')
        self.assertAboutNow(res.checkout_time)

    def test_checkoutBook_alreadyOut(self):
        book = Book(None, 'isbn1', 1, '', '', '', '', '')
        self.books.createBook(book)
        user = User(1234, 'user', 'user@example.com')
        self.db.putUser(user.user_id, user.name, user.email)
        self.books.checkoutBook('isbn1', user)

        with self.assertRaises(InvalidStateException):
            self.books.checkoutBook('isbn1', user)

    def test_checkoutBook_sendsEmail(self):
        # TODO
        return

    def test_returnBook(self):
        book = Book(None, 'isbn1', 1, '', '', '', '', '')
        self.books.createBook(book)
        user = User(1234, 'user', 'user@example.com')
        self.db.putUser(user.user_id, user.name, user.email)
        self.books.checkoutBook('isbn1', user)
        self.books.returnBook('isbn1')

        res = self.books.getBook('isbn1')
        log = self.db.getLatestLog(res.book_id)

        self.assertEqual(res.is_out, False)
        self.assertEqual(res.checkout_user, '')
        self.assertEqual(res.checkout_time, '')
        self.assertAboutNow(log.get("timestamp"))
        self.assertEqual(log.get("action"), Action.RETURN.value)
        self.assertEqual(log.get("user_id"), 1234)

    def test_returnBook_notOut(self):
        book = Book(None, 'isbn1', 1, '', '', '', '', '')
        self.books.createBook(book)

        with self.assertRaises(InvalidStateException):
            self.books.returnBook('isbn1')

    def test_returnBook_sendsEmail(self):
        # TODO
        return

    def test_listBookCheckoutHistory(self):
        b1 = self.books.createBook(Book(None, 'isbn1', 1, '', '', '', '', ''))
        self.books.createBook(Book(None, 'isbn2', 2, '', '', '', '', ''))
        user = User(1234, 'user', 'user@example.com')
        self.db.putUser(user.user_id, user.name, user.email)
        self.books.checkoutBook('isbn1', user)
        self.books.returnBook('isbn1')
        self.books.checkoutBook('isbn2', user)

        res = self.books.listBookCheckoutHistory(b1)

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].book_id, b1)
        self.assertAboutNow(res[0].timestamp)
        self.assertEqual(res[0].action, Action.CHECKOUT)
        self.assertEqual(res[0].user_id, 1234)
        self.assertEqual(res[0].user_name, 'user')
        self.assertEqual(res[1].book_id, b1)
        self.assertAboutNow(res[1].timestamp)
        self.assertEqual(res[1].action, Action.RETURN)
        self.assertEqual(res[1].user_id, 1234)
        self.assertEqual(res[1].user_name, 'user')

    def test_listUserCheckoutHistory(self):
        b1 = self.books.createBook(Book(None, 'isbn1', 1, '', '', '', '', ''))
        self.books.createBook(Book(None, 'isbn2', 2, '', '', '', '', ''))
        user = self.users.createUser('user', 'user@example.com')
        other = self.users.createUser('other', 'other@example.com')
        self.books.checkoutBook('isbn1', user)
        self.books.returnBook('isbn1')
        self.books.checkoutBook('isbn2', other)

        res = self.books.listUserCheckoutHistory(user.user_id)

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].book_id, b1)
        self.assertAboutNow(res[0].timestamp)
        self.assertEqual(res[0].action, Action.CHECKOUT)
        self.assertEqual(res[0].user_id, user.user_id)
        self.assertEqual(res[0].user_name, 'user')
        self.assertEqual(res[1].book_id, b1)
        self.assertAboutNow(res[1].timestamp)
        self.assertEqual(res[1].action, Action.RETURN)
        self.assertEqual(res[1].user_id, user.user_id)
        self.assertEqual(res[1].user_name, 'user')

class TestUserService(BaseTestCase):

    def setUp(self):
        self.db = Database(firestore.client())
        self.users = LocalUserService(self.db)

    def tearDown(self):
        del_url = (
            "http://%s/emulator/v1/projects/demo-project/databases/(default)/documents" %
            LOCAL_EMULATOR
        )
        requests.delete(del_url)

    def test_getUser(self):
        self.db.putUser(1234, 'Brian', 'me@example.com')

        res = self.users.getUser(1234)

        self.assertEqual(res.user_id, 1234)
        self.assertEqual(res.name, 'Brian')
        self.assertEqual(res.email, 'me@example.com')

    def test_createUser(self):
        user = self.users.createUser('Brian', 'me@example.com')
        res = self.users.getUser(user.user_id)

        self.assertEqual(res, user)
        self.assertEqual(user.name, 'Brian')
        self.assertEqual(user.email, 'me@example.com')
        self.assertGreaterEqual(user.user_id, MIN_USER_ID)
        self.assertLessEqual(user.user_id, MAX_USER_ID)

    def test_listUsers(self):
        self.db.putUser(1234, 'Brian', 'me@example.com')
        self.db.putUser(5678, 'Other', 'someone@example.com')

        res = self.users.listUsers()

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].user_id, 1234)
        self.assertEqual(res[0].name, 'Brian')
        self.assertEqual(res[0].email, 'me@example.com')
        self.assertEqual(res[1].user_id, 5678)
        self.assertEqual(res[1].name, 'Other')
        self.assertEqual(res[1].email, 'someone@example.com')

    def test_updateUser(self):
        self.db.putUser(1234, 'Brian', 'me@example.com')

        self.users.updateUser(1234, 'Charlie')
        res = self.users.getUser(1234)

        self.assertEqual(res.name, 'Charlie')


if __name__ == '__main__':
    unittest.main()
