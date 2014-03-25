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


def dict_to_where(d):
    """convert dict to mysql clause where"""
    args = d.values()
    where = "WHERE %s" % ' and '.join(['`%s`=%%s' % i for i in d.keys()])
    return where, args


def dict_to_values(array_or_dict):
    """convert dict to mysql clause values
    Args:
        array_or_dict

    Raise:
        AssertionError: input items' keys must be identical, no more, no less
    """
    if isinstance(array_or_dict, dict):
        array_or_dict = [array_or_dict]
    args = []
    assumed_keys = set()
    for d in array_or_dict:
        if assumed_keys:
            try:
                assert assumed_keys == set(d.keys())
            except AssertionError as e:
                raise e("insert items' keys are not identical")
        else:
            assumed_keys = set(d.keys())
        args.extend([d[i] for i in assumed_keys])

    fields = ', '.join(["`%s`" % i for i in assumed_keys])
    placeholder = "(%s)" % ', '.join(['%s'] * len(d))
    placeholders = ', '.join([placeholder] * len(array_or_dict))
    values = "(%s) VALUES %s" % (fields, placeholders)
    return values, args


def dict_to_set(d):
    """convert dict to mysql clause set"""
    args = d.values()
    set_ = "SET %s" % ", ".join(['`%s`=%%s' % i for i in d.keys()])
    return set_, args


def create_pool(creator=MySQLdb, configs=MYSQL_MASTER_PARAMS):
    dbpool = PooledDB(creator=creator, **configs)
    return dbpool


class MysqldbWrapper(object):
    def __init__(self, pool=None, **kwargs):
        if not pool:
            pool = create_pool(configs=kwargs)
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

    def fetch(self, query, args=None):
        result = []
        try:
            cursor = self.create_cursor()
            cursor.execute(query=query, args=args)
            columns = [i[0] for i in cursor.description]
            for i in cursor.fetchall():
                item = dict(zip(columns, i))
                result.append(item)
        except MySQLdb.ProgrammingError as e:
            raise e
        finally:
            cursor.close()
        return result

    def execute(self, query, args=None, commit=True, select_identity=False):
        """
        Returns:
            int, affected row numbers or generated id for new item
        """
        conn = self.get_usable_connection()
        result = None
        try:
            cursor = conn.cursor()
            result = cursor.execute(query, args=args)
            if commit:
                conn.commit()
            if select_identity:
                cursor.execute('select @@identity')
                result = cursor.fetchone()[0]
        except Exception as e:
            raise e
        finally:
            cursor.close()
            return result

    def executemany(self, query, args=None):
        pass


class MysqldbDao(MysqldbWrapper):
    def select(self, select, args=None):
        return self.fetch(query=select, args=args)

    def insert(self, table, value_dict, replace=False):
        """
        Args:
            table: table name
            value_dict: {} or [{}], the item(s) to be inserted in dict form
        """
        values_clause, args = dict_to_values(value_dict)
        action = 'REPLACE' if replace else 'INSERT'
        insert = "%s INTO `%s` %s" % (action, table, values_clause)
        return self.execute(query=insert, args=args, select_identity=True)

    def update(self, table, update_dict, where_dict=None):
        set_clause, args = dict_to_set(update_dict)
        if where_dict:
            where_clause, where_args = dict_to_where(where_dict)
            update = "UPDATE `%s` %s %s" % (table, set_clause, where_clause)
            args.extend(where_args)
        else:
            update = "UPDATE `%s` %s" % (table, where_clause)
        return self.execute(query=update, args=args)

    def replace(self, table, value_dict):
        return self.insert(table=table, value_dict=value_dict, replace=True)


test_pool = create_pool()
test = MysqldbDao(**MYSQL_MASTER_PARAMS)

def _main(argv):
    def retry_test():
        import time
        while True:
            print test.create_cursor(), "sleeping 1s...", int(time.time())
            time.sleep(1)

    print test.select('select * from a')
    d = {'id': 4}
    print test.insert('a', [d, {'id': 1}])
    print test.select('select * from a')
    print test.update('a', {'id': 2}, {'id': 4})
    print test.select('select * from a')


if __name__ == '__main__':
    import sys
    _main(sys.argv)
