from firebase_admin import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.client import Client
import logging

from libraryserver.api.models import Action


class Database:

    def __init__(self, cli: Client):
        self.books_ref = cli.collection('books')
        self.logs_ref = cli.collection('actionlogs')
        self.users_ref = cli.collection('users')
        self.logger = logging.getLogger(__name__)

    def getBook(self, isbn: str) -> DocumentSnapshot:
        return self.books_ref.where(filter=FieldFilter("isbn", "==", isbn)).get()[0]

    def putBook(self, isbn, title, author, cat, year, img):
        book = self.books_ref.document()
        book.set({
            "isbn": isbn,
            "title": title,
            "author": author,
            "category": cat,
            "year": year,
            "img": img
        })

    def listBooks(self, search: str|None = None) -> list[DocumentSnapshot]:
        books = self.books_ref.get()
        # have to do filtering here, because Firestore doesn't support search
        if search:
            books = [book for book in books if self._matches(book, search)]
        return books

    def _matches(self, book, search: str) -> bool:
        return (
            search.lower() in book.get('title').lower() or
            search.lower() in book.get('author').lower()
        )

    def putLog(self, isbn: str, action: Action, user_id: int = 0):
        log = self.logs_ref.document()
        log.set({
            "isbn": isbn,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "action": action.value,
            "user_id": user_id
        })

    def getLatestLog(self, isbn: str) -> DocumentSnapshot|None:
        log = (
            self.logs_ref
            .where(filter=FieldFilter("isbn", "==", isbn))
            .order_by('timestamp', direction='DESCENDING')
            .get()
        )
        try:
            return log[0]
        except IndexError:
            # Maybe default value instead?
            return None

    def listLogsByIsbn(self, isbn: str) -> list[DocumentSnapshot]:
        return (
            self.logs_ref
            .where(filter=FieldFilter("isbn", "==", isbn))
            .order_by('timestamp', direction='ASCENDING')
            .get()
        )

    def listLogsByUser(self, user_id: int) -> list[DocumentSnapshot]:
        return (
            self.logs_ref
            .where(filter=FieldFilter("user_id", "==", user_id))
            .order_by('timestamp', direction='ASCENDING')
            .get()
        )

    def putUser(self, user_id, name, email):
        user = self.users_ref.document(str(user_id))
        user.set({
            "name": name,
            "email": email
        })
        
    def getUser(self, user_id) -> DocumentSnapshot:
        return self.users_ref.document(str(user_id)).get()

    def listUsers(self) -> list[DocumentSnapshot]:
        return self.users_ref.get()
