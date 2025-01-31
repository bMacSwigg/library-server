from google.cloud.firestore_v1.base_document import DocumentSnapshot
import random

from libraryserver.api.errors import NotFoundException, InvalidStateException
from libraryserver.api.models import Book, User, Action, LogEntry
from libraryserver.api.service import BookService, UserService
from libraryserver.config import APP_CONFIG
from libraryserver.constants import MIN_USER_ID, MAX_USER_ID
from libraryserver.keys.keymanager import KeyManager
from libraryserver.notifs.mailgun_client import Email
from libraryserver.storage.firestore_client import Database


class LocalBookService(BookService):

    def __init__(self, db: Database):
        self.db = db
        self.email = Email(KeyManager())

    def _parseLogs(self, log_vals: DocumentSnapshot) -> LogEntry:
        user_id = log_vals.get("user_id") or None
        user = (
            self.db.getUser(user_id).get("name")
            if user_id
            else None
        )
        action = Action(log_vals.get("action"))
        return LogEntry(log_vals.get("book_id"), log_vals.get("timestamp"),
                        action, user_id, user)

    def _bookFromDocs(self, book_vals: DocumentSnapshot,
                      log_vals: DocumentSnapshot|None) -> Book:
        if log_vals:
            log = self._parseLogs(log_vals)
        else:
            log = LogEntry(book_vals.id, "", Action.UNKNOWN, None, None)

        is_out = (log.action == Action.CHECKOUT)
        if is_out:
            checkout_user, checkout_time = log.user_name, str(log.timestamp)
        else:
            (checkout_user, checkout_time) = ('', '')

        return Book(book_vals.id, book_vals.get("isbn"), book_vals.get("owner_id"),
                    book_vals.get("title"), book_vals.get("author"),
                    book_vals.get("category"), book_vals.get("year"),
                    book_vals.get("img"), is_out, checkout_user, checkout_time)

    def getBook(self, isbn: str) -> Book:
        book_vals = self.db.getBook(isbn)
        if book_vals is None:
            raise NotFoundException('No book in database with ISBN %s' % isbn)
        log_vals = self.db.getLatestLog(book_vals.id)
        return self._bookFromDocs(book_vals, log_vals)

    def listBooks(self, user_id: int, search: str|None = None) -> list[Book]:
        vals = self.db.listBooks(user_id, search)
        # It would probably be more efficient to do this with a JOIN in the DB
        # query. But this is simpler, and the scale of data is too small to matter.
        return [self._bookFromDocs(book_vals,
                                   self.db.getLatestLog(book_vals.id))
                for book_vals in vals]

    # Lists all checked-out or checked-in books
    def listBooksByStatus(self, user_id: int, is_out: bool) -> list[Book]:
        allBooks = self.listBooks(user_id)
        return [b for b in allBooks if b.is_out == is_out]

    def createBook(self, book: Book) -> str:
        book_id = self.db.putBook(book.isbn, book.owner_id, book.title,
                                  book.author, book.category, book.year,
                                  book.thumbnail)
        self.db.putLog(book_id, Action.CREATE)
        return book_id

    def checkoutBook(self, isbn: str, user: User):
        book_id = self.db.getBook(isbn).id
        prev_log = self.db.getLatestLog(book_id)
        if prev_log and prev_log.get("action") == Action.CHECKOUT.value:
            raise InvalidStateException('Book with ISBN %s already out' % isbn)

        self.db.putLog(book_id, Action.CHECKOUT, int(user.user_id))

        book = self.getBook(isbn)
        self.email.send_checkout_message(book, user)

    def returnBook(self, isbn: str):
        book_id = self.db.getBook(isbn).id
        checkout_log = self.db.getLatestLog(book_id)
        if not checkout_log or checkout_log.get("action") != Action.CHECKOUT.value:
            raise InvalidStateException('Book with ISBN %s is not out' % isbn)

        user_id = checkout_log.get("user_id")
        self.db.putLog(book_id, Action.RETURN, user_id)

        book = self.getBook(isbn)
        user_vals = self.db.getUser(user_id)
        user = User(user_id, user_vals.get("name"), user_vals.get("email"))
        ret_time = self.db.getLatestLog(book_id).get("timestamp")
        self.email.send_return_message(book, user, str(ret_time))

    def listBookCheckoutHistory(self, book_id: str) -> list[LogEntry]:
        logs = self.db.listLogsByBook(book_id)
        logs = map(self._parseLogs, logs)
        logs = filter(lambda l: l.action in [Action.CHECKOUT, Action.RETURN], logs)
        return list(logs)

    def listUserCheckoutHistory(self, user_id: int) -> list[LogEntry]:
        logs = self.db.listLogsByUser(user_id)
        logs = map(self._parseLogs, logs)
        logs = filter(lambda l: l.action in [Action.CHECKOUT, Action.RETURN], logs)
        return list(logs)


class LocalUserService(UserService):

    def __init__(self, db: Database):
        self.db = db

    def getUser(self, user_id: int) -> User:
        user_vals = self.db.getUser(user_id)
        return User(user_id, user_vals.get("name"), user_vals.get("email"))

    def createUser(self, name: str, email: str) -> User:
        user_id = random.randint(MIN_USER_ID, MAX_USER_ID)
        user = User(user_id, name, email)
        self.db.putUser(user.user_id, user.name, user.email)
        return user

    def listUsers(self) -> list[User]:
        vals = self.db.listUsers()
        return [User(int(v.id), v.get("name"), v.get("email")) for v in vals]

    def updateUser(self, user_id: int, name: str):
        self.db.setUserName(user_id, name)

