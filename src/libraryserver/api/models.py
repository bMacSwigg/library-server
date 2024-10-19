from dataclasses import dataclass
from enum import IntEnum

@dataclass(frozen=True)
class Book:
    isbn: str  # ISBN of this book, also serves as primary ID
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
    isbn: str  # ISBN of the book that this activity was for
    timestamp: str  # Time of this activity
    action: Action  # What the activity was
    user_id: int|None  # The User that performed this action, if any
    user_name: str|None  # The name of the user (if any), for convenience
