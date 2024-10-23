from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

@dataclass(frozen=True)
class Book:
    book_id: str  # Unique primary ID of this book. Should not be set on creation
    isbn: str  # ISBN of this book
    owner_id: int  # user_id of the User whose library this book is in
    title: str  # Full title of this book
    author: str  # Full name of the author
    category: str  # Type of book, e.g. "Fiction"
    year: str  # Publication year
    thumbnail: str  # URL to a cover thumbnail (~128px width)
    is_out: bool = False  # True if the book is currently checked out
    checkout_user: str = ''  # The user who checked it out (only set if is_out)
    checkout_time: str = ''  # Timestamp of checkout (only set if is_out)

@dataclass(frozen=True)
class User:
    user_id: int  # Unique pseudorandom ID of this user
    name: str  # Full name
    email: str  # Email address for notifications

class Action(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    CHECKOUT = 2
    RETURN = 3

@dataclass(frozen=True)
class LogEntry:
    book_id: str  # ID of the book that this activity was for
    timestamp: datetime  # Time of this activity
    action: Action  # What the activity was
    user_id: int|None  # The User that performed this action, if any
    user_name: str|None  # The name of the user (if any), for convenience
