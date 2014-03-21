# -*- coding: utf-8 -*-
"""
    mysqldb_wrapper.py
    ~~~~~~~~~~~~~~

    simple wrapper for mysqldb and dbutils
"""
import MySQLdb
from DBUtils.PooledDB import PooledDB

#from config import MYSQL_MASTER_PARAMS
MYSQL_MASTER_PARAMS = {
    'host': '127.0.0.1',
    'user': 'root',
    #'passwd': None,
    'db': 'sync_db',
    'charset': 'utf8',
    'port': 3391,
    'connect_timeout': 10,
}


def create_pool(creator=MySQLdb, configs=MYSQL_MASTER_PARAMS):
    dbpool = PooledDB(creator=creator, **configs)
    return dbpool


class MysqldbWrapper(object):
    def __init__(self, pool):
        self._pool = pool

    def get_new_connection(self):
        """
        Returns:
            mysqldb connection
            False, can't establish connection
        """
        conn = self._pool.connection()
        try:
            conn.ping()
        except MySQLdb.OperationalError as e:
            print e, "Abort connect."
            conn.close()
            conn = False
        finally:
            return conn

    def get_usable_connection(self):
        """get/create an usable connection

        In fact, this is singleton model. It would issue a reconnect if current connection can't ping through

        Returns:
            mysqldb connection
            False, can't establish connection
        """
        if not hasattr(self, 'connection') or not self.connection:
            self.connection = self.get_new_connection()
        else:
            try:
                self.connection.ping()
            except MySQLdb.OperationalError as e:
                print e, "Retrying..."
                self.connection.close()
                self.connection = self.get_new_connection()
                if self.connection:
                    print "Reconnect successfully."
                else:
                    print "Fail in retring. Abort."
        return self.connection

    def create_cursor(self):
        conn = self.get_usable_connection()
        if conn:
            cursor = conn.cursor()
            return cursor
        else:
            return False

    def select(self, select, args=None):
        result = []
        try:
            cursor = self.create_cursor()
            #cursor.execute('set names utf8')
            cursor.execute(select, args=args)
            columns = [i[0] for i in cursor.description]
            for i in cursor.fetchall():
                item = {}
                for j in range(0, len(i)):
                    item[columns[j]] = i[j]
                result.append(item)
        except MySQLdb.ProgrammingError:
            info = '%s\t%s' % (select, args)
            if hasattr(self, 'logger'):
                self.logger.error(info)
            else:
                print "ERROR\t", info
        finally:
            cursor.close()
        return result

    def execute(self, query, args=None):
        """
        Returns:
            int, affected row numbers
        """
        try:
            cursor = self.create_cursor()
            result = cursor.execute(query, args=args)
        except Exception as e:
            raise e
        finally:
            cursor.close()
            return result

    def executemany(self, query, args=None):
        pass


test_pool = create_pool()
test = MysqldbWrapper(test_pool)

def _main(argv):
    import time
    while True:
        print test.create_cursor(), "sleeping 1s...", int(time.time())
        time.sleep(1)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
