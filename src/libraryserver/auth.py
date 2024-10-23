from collections.abc import Callable
import firebase_admin
from firebase_admin import auth
from flask import request, Response
from functools import wraps
from typing import TypeVar

from libraryserver.storage.firestore_client import Database


a = TypeVar("a")

def user_authenticated(db: Database):
    """Takes a user ID token (provided by @jwt_authenticated) and associates
    it with the matching user entry in the database.

    If there is no user entry with this UID, but there is one with a matching
    email address, then this adds it to that user entry.
    """

    def decorator(func: Callable[..., int]) -> Callable[..., int]:

        @wraps(func)
        def decorated_function(*args: a, **kwargs: a) -> a:
            uid = request.uid
            user = db.getUserByTokenUid(uid)

            if user is None:
                email = auth.get_user(uid).email
                user = db.getUserByEmail(email)
                if user is None:
                    return Response(status=403, response=f"No user with email {email}")
                db.setUserTokenUid(user.id, uid)

            request.user = user
            return func(*args, **kwargs)

        return decorated_function

    return decorator
