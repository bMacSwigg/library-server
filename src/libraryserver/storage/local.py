import random

from libraryserver.api.errors import NotFoundException, InvalidStateException
from libraryserver.api.models import Book, User, Action, LogEntry
from libraryserver.api.service import BookService, UserService
from libraryserver.config import APP_CONFIG
from libraryserver.constants import MIN_USER_ID, MAX_USER_ID
from libraryserver.notifs.mailgun_client import Email
from libraryserver.storage.db import Database


class LocalBookService(BookService):

    def __init__(self):
        self.db = Database(APP_CONFIG.db_file())
        self.email = Email()

    def _parseLogs(self, log_vals: tuple) -> LogEntry:
        user_id = log_vals[3] or None
        user = (
            self.db.getUser(user_id)[1]
            if user_id
            else None
        )
        action = Action(log_vals[2])
        return LogEntry(log_vals[0], log_vals[1], action, user_id, user)

    def _bookFromTuple(self, book_vals: tuple, log_vals: tuple) -> Book:
        log = self._parseLogs(log_vals)
        is_out = (log.action == Action.CHECKOUT)
        if is_out:
            checkout_user, checkout_time = log.user_name, log.timestamp
        else:
            (checkout_user, checkout_time) = ('', '')

        return Book(book_vals[0], book_vals[1], book_vals[2],
                    book_vals[3], book_vals[4], book_vals[5],
                    is_out, checkout_user, checkout_time)

    def getBook(self, isbn: str) -> Book:
        book_vals = self.db.getBook(isbn)
        if book_vals is None:
            raise NotFoundException('No book in database with ISBN %s' % isbn)
        log_vals = self.db.getLatestLog(isbn)
        return self._bookFromTuple(book_vals, log_vals)

    def listBooks(self, search: str|None = None) -> list[Book]:
        vals = self.db.listBooks(search)
        # It would probably be more efficient to do this with a JOIN in the DB
        # query. But this is simpler, and the scale of data is too small to matter.
        return [self._bookFromTuple(book_vals, self.db.getLatestLog(book_vals[0]))
                for book_vals in vals]

    # Lists all checked-out or checked-in books
    def listBooksByStatus(self, is_out) -> list[Book]:
        allBooks = self.listBooks()
        return [b for b in allBooks if b.is_out == is_out]

    def createBook(self, book: Book):
        self.db.putBook(book.isbn, book.title, book.author,
                        book.category, book.year, book.thumbnail)
        self.db.putLog(book.isbn, Action.CREATE)

    def checkoutBook(self, isbn: str, user: User):
        prev_log = self.db.getLatestLog(isbn)
        if prev_log[2] == Action.CHECKOUT.value:
            raise InvalidStateException('Book with ISBN %s already out' % isbn)

        self.db.putLog(isbn, Action.CHECKOUT, user.user_id)

        book = self.getBook(isbn)
        self.email.send_checkout_message(book, user)

    def returnBook(self, isbn: str):
        checkout_log = self.db.getLatestLog(isbn)
        if checkout_log[2] != Action.CHECKOUT.value:
            raise InvalidStateException('Book with ISBN %s is not out' % isbn)

        user_id = checkout_log[3]
        self.db.putLog(isbn, Action.RETURN, user_id)

        book = self.getBook(isbn)
        user_vals = self.db.getUser(user_id)
        user = User(user_vals[0], user_vals[1], user_vals[2])
        ret_time = self.db.getLatestLog(isbn)[1]
        self.email.send_return_message(book, user, ret_time)

    def listBookCheckoutHistory(self, isbn: str) -> list[LogEntry]:
        logs = self.db.listLogsByIsbn(isbn)
        logs = map(self._parseLogs, logs)
        logs = filter(lambda l: l.action in [Action.CHECKOUT, Action.RETURN], logs)
        return list(logs)

    def listUserCheckoutHistory(self, user_id: int) -> list[LogEntry]:
        logs = self.db.listLogsByUser(user_id)
        logs = map(self._parseLogs, logs)
        logs = filter(lambda l: l.action in [Action.CHECKOUT, Action.RETURN], logs)
        return list(logs)


class LocalUserService(UserService):

    def __init__(self):
        self.db = Database(APP_CONFIG.db_file())

    def getUser(self, user_id: int) -> User:
        user_vals = self.db.getUser(user_id)
        return User(user_vals[0], user_vals[1], user_vals[2])

    def createUser(self, name: str, email: str) -> User:
        user_id = random.randint(MIN_USER_ID, MAX_USER_ID)
        user = User(user_id, name, email)
        self.db.putUser(user.user_id, user.name, user.email)
        return user

    def listUsers(self) -> list[User]:
        vals = self.db.listUsers()
        return [User(v[0], v[1], v[2]) for v in vals]

