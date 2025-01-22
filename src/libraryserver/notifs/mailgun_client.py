import json
import logging
import re
import requests

from libraryserver.api.models import Book, User
from libraryserver.keys.keymanager import KeyManager

_EMAIL_FROM = 'Brian\'s Library <library@mcswiggen.me>'
_CHECKOUT_TEMPLATE = 'Checkout Notification'
_RETURN_TEMPLATE = 'Return Notification'
# Could be better, but this is sufficient for now
_VALID_EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


class Email:

    API_KEY_NAME = 'mailgun_sending_key'

    def __init__(self, keymanager: KeyManager = None):
        self.logger = logging.getLogger(__name__)
        
        if keymanager is None:
            self.logger.warning('No API key provided, emails will not be sent')
            self.api_key = ''
            return
        self.api_key = keymanager.getKey(self.API_KEY_NAME)

    def send_checkout_message(self, book: Book, user: User):
        subs = {
            'book': {
                'title': book.title,
                'author': book.author,
                'thumbnail': book.thumbnail
            },
            'user': {
                'name': user.name
            },
            'checkout_time': book.checkout_time
        }
        subject = 'Thanks for borrowing \'%s\'' % book.title
        self.send_message([user.email], subject, _CHECKOUT_TEMPLATE, subs)

    def send_return_message(self, book: Book, user: User, ret_time: str):
        subs = {
            'book': {
                'title': book.title,
                'author': book.author,
                'thumbnail': book.thumbnail
            },
            'user': {
                'name': user.name
            },
            'return_time': ret_time
        }
        subject = 'Thanks for returning \'%s\'' % book.title
        self.send_message([user.email], subject, _RETURN_TEMPLATE, subs)

    def send_message(self, to_emails, subject, template, substitutions):
        to_emails = list(filter(self._validate_email, to_emails))
        if not to_emails:
            self.logger.warning('No valid emails; skipping notification')
            return
        subs = json.dumps(substitutions)
        resp = requests.post(
            'https://api.mailgun.net/v3/mg.mcswiggen.me/messages',
            auth=('api', self.api_key),
  	    data={'from': _EMAIL_FROM,
                'to': to_emails,
  		'subject': subject,
                'template': template,
  		'h:X-Mailgun-Variables': subs})
        print(resp.status_code)
        print(resp.text)

    def send_test_message(self):
        book = Book('isbn', 'Babel', 'R.F. Kuang', '', '',
                'http://books.google.com/books/content?id=rkO-zgEACAAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api',
                True, 'Brian', 'Some time')
        user = User(1, 'Brian McSwiggen', 'brian.mcswiggen@gmail.com')
        self.send_checkout_message(book, user)

    def _validate_email(self, email):
        if re.search(_VALID_EMAIL_PATTERN, email) is None:
            self.logger.warning('"%s" is not a valid email address' % email)
            return False
        return True


class FakeEmail(Email):

    def send_message(self, to_emails, subject, template, substitutions):
        print(to_emails, subject, template, substitutions)

if __name__ == '__main__':
    email = Email()
    email.send_test_message()
