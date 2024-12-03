import json
from urllib.request import urlopen

from libraryserver.api.errors import NotFoundException
from libraryserver.api.models import Book
from libraryserver.keys.keymanager import KeyManager


class LookupService:

    API_KEY_NAME = 'books_api_key'
    GOOGLE_BOOKS_ENDPOINT = 'https://www.googleapis.com/books/v1/volumes?q=isbn:%s&key=%s'

    def __init__(self, keymanager: KeyManager):
        self.api_key = keymanager.getKey(self.API_KEY_NAME)

    def lookupIsbn(self, isbn: str) -> Book:
        url = self.GOOGLE_BOOKS_ENDPOINT % (isbn, self.api_key)
        res = json.load(urlopen(url))
        if not 'items' in res or res['totalItems'] == 0:
            raise NotFoundException('No books found with ISBN %s' % isbn)
        vals = res['items'][0]['volumeInfo']
        title = vals['title'] if 'title' in vals else ''
        authors = vals['authors'] if 'authors' in vals else []
        author = ', '.join(authors)
        if 'mainCategory' in vals:
            category = vals['mainCategory']
        elif 'categories' in vals and len(vals['categories']) > 0:
            category = vals['categories'][0]
        else:
            category = ''
        year = vals['publishedDate'][:4] if 'publishedDate' in vals else ''
        if 'imageLinks' in vals and 'thumbnail' in vals['imageLinks']:
            thumbnail = vals['imageLinks']['thumbnail']
        else:
            thumbnail = ''
        return Book('', isbn, 0, title, author, category, year, thumbnail)
