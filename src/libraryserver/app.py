from dataclasses import asdict
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
import logging
import os

from libraryserver.api.errors import InvalidStateException, NotFoundException
from libraryserver.api.models import Book, User
from libraryserver.auth import user_authenticated
from libraryserver.config import APP_CONFIG
from libraryserver.keys.keymanager import KeyManager
from libraryserver.lookup.lookup import LookupService
from libraryserver.storage.local import LocalBookService, LocalUserService
from libraryserver.storage.firestore_client import Database
from libraryserver.thirdparty.middleware import jwt_authenticated

# Initialize Flask app
app = Flask(__name__)
_ORIGINS = ["http://localhost:4200",
            "https://library-ui-869102415447.us-central1.run.app",
            "https://library.mcswiggen.me"]
CORS(app, resources={r"*": {"origins": _ORIGINS}})

# Initialize Firestore DB
if APP_CONFIG.firestore_apikey_file():
    cred = credentials.Certificate(APP_CONFIG.firestore_apikey_file())
    initialize_app(cred)
else:
    # use application default credentials
    initialize_app()
db = Database(firestore.client())


# Meta-API
@app.route('/v0/check', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def check():
    """
        check() : Validate that the caller is logged in and can access the API.
        Returns the user object for the caller.
    """
    user = User(request.user.id, request.user.get("name"), request.user.get("email"))
    return jsonify(user), 200

# Books API
@app.route('/v0/books/<book_id>', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def getBook(book_id):
    """
        getBook() : Retrieve book by ID (currently, ISBN)
    """
    try:
        book = LocalBookService(db).getBook(book_id)
    except NotFoundException:
        return "Book with ID '%s' not found" % book_id, 404
    else:
        return jsonify(asdict(book)), 200

@app.route('/v0/books', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def listBooks():
    """
        listBooks() : List all books. At most one of 'query' and 'is_out' may
        be specified. If 'query' is specified, returns only books whose title
        or author contains 'query' as a substring. If 'is_out' is specified,
        filters to only books that are (or are not) currently checked out.
        Filters to only books owned by user_id. If user_id is not specified,
        filters to the ID of the calling user.
    """
    if 'query' in request.args and 'is_out' in request.args:
        return "'query' and 'is_out' filters cannot both be specified", 400

    user_id = request.args.get('user_id', default=request.user.id)

    if 'is_out' in request.args:
        is_out = bool(int(request.args['is_out']))
        books = LocalBookService(db).listBooksByStatus(user_id, is_out)
    elif 'query' in request.args:
        q = request.args['query']
        books = LocalBookService(db).listBooks(user_id, q)
    else:
        books = LocalBookService(db).listBooks(user_id)

    return jsonify(list(map(asdict, books))), 200

@app.route('/v0/books', methods=['POST'])
@jwt_authenticated
@user_authenticated(db)
def createBook():
    """
        createBook() : Create a new Book.
    """
    try: 
        json = request.json['book']
        book = Book(None, json['isbn'], request.user.id, json['title'],
                    json['author'], json['category'], json['year'],
                    json['thumbnail'])
    except KeyError:
        return "Missing property", 400
    else:
        LocalBookService(db).createBook(book)
        return "Book created", 200

@app.route('/v0/books/<book_id>/checkout', methods=['POST'])
@jwt_authenticated
@user_authenticated(db)
def checkoutBook(book_id):
    """
        checkoutBook() : Mark this book as checked out by a given user. Book
        must not be currently checked out.
    """
    if 'user_id' not in request.json:
        return "Missing 'user_id' property", 400

    user_id = request.json['user_id']
    # TODO: deal with this not being a real user ID
    user = LocalUserService(db).getUser(user_id)

    try:
        LocalBookService(db).checkoutBook(book_id, user)
    except InvalidStateException:
        return "Book with ISBN %s already out" % book_id, 400
    else:
        return "Checked out", 200

@app.route('/v0/books/<book_id>/return', methods=['POST'])
@jwt_authenticated
@user_authenticated(db)
def returnBook(book_id):
    """
        returnBook() : Mark this book as returned, by whoever checked it out.
        Book must be currently checked out.
    """
    try:
        LocalBookService(db).returnBook(book_id)
    except InvalidStateException:
        return "Book with ISBN %s not checked out" % book_id, 400
    else:
        return "Returned", 200

@app.route('/v0/books/<book_id>/history', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def listBookCheckoutHistory(book_id):
    """
        listBookCheckoutHistory() : List the CHECKOUT and RETURN log events
        for this book. Ordered from earliest to latest.
    """
    logs = LocalBookService(db).listBookCheckoutHistory(book_id)
    return jsonify(list(map(asdict, logs))), 200

# Users API
@app.route('/v0/users/<int:user_id>', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def getUser(user_id):
    """
        getUser() : Retrieve user by ID
    """
    user = LocalUserService(db).getUser(user_id)
    return jsonify(user), 200

@app.route('/v0/users', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def listUsers():
    """
        listUsers() : List all users.
    """
    users = LocalUserService(db).listUsers()

    return jsonify(list(map(asdict, users))), 200

@app.route('/v0/users/<int:user_id>', methods=['PATCH'])
@jwt_authenticated
@user_authenticated(db)
def updateUser(user_id):
    """
        updateUser() : Update mutable account details. Currently, only supports
        updating the `name` property.
    """
    if user_id != int(request.user.id):
        return "Cannot update other users", 403

    try: 
        json = request.json['user']
        name = json['name']
    except KeyError:
        return "Missing property", 400
    else:
        LocalUserService(db).updateUser(user_id, name)
        return "User updated", 200

@app.route('/v0/users/<int:user_id>/history', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def listUserCheckoutHistory(user_id):
    """
        listUserCheckoutHistory() : List the CHECKOUT and RETURN log events
        for this user. Ordered from earliest to latest.
    """
    logs = LocalBookService(db).listUserCheckoutHistory(user_id)
    return jsonify(list(map(asdict, logs))), 200

# Lookup API
@app.route('/v0/lookup/<isbn>', methods=['GET'])
@jwt_authenticated
@user_authenticated(db)
def lookupBookDetails(isbn):
    """
        lookupBookDetails() : Fetch details on this book from Google Books API
    """
    lookup = LookupService(KeyManager())
    try:
        book = lookup.lookupIsbn(isbn)
    except NotFoundException:
        return "No books found with ISBN %s" % isbn, 404
    return jsonify(asdict(book)), 200


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)
