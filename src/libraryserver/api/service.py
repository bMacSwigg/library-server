from abc import ABC, abstractmethod

from libraryserver.api.models import Book, User, LogEntry

class BookService(ABC):

    @abstractmethod
    def getBook(self, isbn: str) -> Book:
        pass

    @abstractmethod
    def listBooks(self, search: str|None = None) -> list[Book]:
        pass

    @abstractmethod
    def listBooksByStatus(self, is_out) -> list[Book]:
        """
        Lists all checked-out or checked-in books.
        """
        pass

    @abstractmethod
    def createBook(self, book: Book):
        pass

    @abstractmethod
    def checkoutBook(self, isbn: str, user: User):
        pass

    @abstractmethod
    def returnBook(self, isbn: str):
        pass

    @abstractmethod
    def listBookCheckoutHistory(self, isbn: str) -> list[LogEntry]:
        pass

    @abstractmethod
    def listUserCheckoutHistory(self, user_id: int) -> list[LogEntry]:
        pass


class UserService(ABC):

    @abstractmethod
    def getUser(self, user_id: int) -> User:
        pass

    @abstractmethod
    def createUser(self, name: str, email: str) -> User:
        pass

    @abstractmethod
    def listUsers(self) -> list[User]:
        pass

