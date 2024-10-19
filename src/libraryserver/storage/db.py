import logging
import sqlite3

from libraryserver.api.models import Action


class Database:

    BOOKS_TABLENAME = 'Books'
    LOGS_TABLENAME = 'ActionLogs'
    USERS_TABLENAME = 'Users'

    def __init__(self, filename):
        self.filename = filename
        self.con = sqlite3.connect(filename)
        self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.close()

    def close(self):
        self.con.close()

    def check(self):
        """Checks if the necessary tables exist."""
        cur = self.con.cursor()
        tables = cur.execute('SELECT name FROM sqlite_schema').fetchall()
        self._findTable(self.BOOKS_TABLENAME, tables)
        self._findTable(self.LOGS_TABLENAME, tables)
        self._findTable(self.USERS_TABLENAME, tables)

    def _findTable(self, tablename, tables):
        if (tablename,) not in tables:
            self.logger.warning('Table %s does not exist' % tablename)

    def getBook(self, isbn):
        cur = self.con.cursor()
        query = ('SELECT * FROM %s WHERE Isbn="%s"' %
                 (self.BOOKS_TABLENAME, isbn))
        return cur.execute(query).fetchone()

    def putBook(self, isbn, title, author, cat, year, img):
        cur = self.con.cursor()
        query = ('INSERT INTO %s VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' %
                 (self.BOOKS_TABLENAME, isbn, title, author, cat, year, img))
        cur.execute(query)
        self.con.commit()

    def listBooks(self, search: str|None = None):
        cur = self.con.cursor()
        query = 'SELECT * FROM %s' % self.BOOKS_TABLENAME
        if search:
            comparison = 'LIKE "%%%s%%"' % search
            query += ' WHERE Title %s OR Author %s' % (comparison, comparison)
        return cur.execute(query).fetchall()

    def putLog(self, isbn: str, action: Action, user_id: int = 0):
        cur = self.con.cursor()
        query = ('INSERT INTO %s VALUES ("%s", datetime("now"), %s, %d)' %
                 (self.LOGS_TABLENAME, isbn, action.value, user_id))
        cur.execute(query)
        self.con.commit()

    def getLatestLog(self, isbn: str):
        cur = self.con.cursor()
        query = ('SELECT * FROM %s WHERE Isbn="%s" ORDER BY Timestamp DESC LIMIT 1' %
                 (self.LOGS_TABLENAME, isbn))
        return cur.execute(query).fetchone() or (isbn, '', Action.UNKNOWN.value, 0)

    def listLogsByIsbn(self, isbn: str):
        cur = self.con.cursor()
        query = ('SELECT * FROM %s WHERE Isbn="%s" ORDER BY Timestamp ASC' %
                 (self.LOGS_TABLENAME, isbn))
        return cur.execute(query).fetchall()

    def listLogsByUser(self, user_id: int):
        cur = self.con.cursor()
        query = ('SELECT * FROM %s WHERE UserId="%s" ORDER BY Timestamp ASC' %
                 (self.LOGS_TABLENAME, user_id))
        return cur.execute(query).fetchall()

    def putUser(self, user_id, name, email):
        cur = self.con.cursor()
        query = ('INSERT INTO %s VALUES (%d, "%s", "%s")' %
                 (self.USERS_TABLENAME, user_id, name, email))
        cur.execute(query)
        self.con.commit()
        
    def getUser(self, user_id):
        cur = self.con.cursor()
        query = ('SELECT * FROM %s WHERE Id=%d' % (self.USERS_TABLENAME, user_id))
        return cur.execute(query).fetchone()

    def listUsers(self):
        cur = self.con.cursor()
        query = 'SELECT * FROM %s' % self.USERS_TABLENAME
        return cur.execute(query).fetchall()
