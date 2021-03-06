# -*- coding: utf-8 -*-
"""
    mysql_replicate_tool.py
    ~~~~~~~~~~~~~~

    A tool for setup MySQL replications
"""
import os
import subprocess
import argparse
import time
import socket


stdout_file = open('stdout.txt', 'a')
stderr_file = open('stderr.txt', 'a')


def execute(cmd):
    result = None
    try:
        result = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                shell=True)
    except subprocess.CalledProcessError as e:
        print e
        print e.cmd, e.output
        print cmd
        raise
    return result


def execute_in_background(cmd):
    subprocess.Popen(cmd, shell=True, stdout=stdout_file, stderr=stderr_file)


def install_new_db(datadir, basedir):
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    mysql_install_db = os.path.join(basedir, 'scripts', 'mysql_install_db')
    cmd = "%s --basedir=%s --datadir=%s --no-defaults" % (mysql_install_db, basedir, datadir)
    print "INSTALL NEW DB at %s" % datadir
    result = execute(cmd)
    return result


class MysqlConfig(object):
    def __init__(self, name, port, basedir, datadir, server_id=None, socket_file=None, defaults_file=None, **kwargs):
        server_id = "127001%i" % port if not server_id else server_id
        self.name = name
        self.port = port
        self.basedir = basedir
        self.datadir = datadir
        socket_file = os.path.join(datadir, "%s.sock" % name) if not socket_file else socket_file
        self.defaults_file = os.path.join(basedir, "%s.cnf" % name) if not defaults_file else defaults_file
        self.client = {
                    'host': '127.0.0.1',
                    'port': port,
                    'socket': socket_file,
                }
        self.mysqld = kwargs
        self.mysqld.update({
                    'bind-address': '0.0.0.0',
                    'port': port,
                    'log_bin': "%s-bin" % name,
                    'server_id': server_id,
                    'basedir': basedir,
                    'datadir': datadir,
                    #: you could also OFF it. You have to enable it when using master-master-slave.
                    #: And, if your master corrupt and slaves do not catch up with master, you should only raise the slave enable the log-slave-updates
                    'log-slave-updates': None,
                    'sync-binlog': '0',
                    'binlog-format': 'STATEMENT',
                    'binlog-ignore-db': 'performance_schema',
                    'socket': socket_file,
                    'character-set-server': 'utf8',
                    'character-set-client': 'utf8',
                    'default-storage-engine': 'InnoDB',
                    'innodb_file_per_table': None,
                    'collation_server': 'utf8_general_ci',
                    'max_connections': 2000,
                    'max_user_connections': 1980,
                    'slow-query-log': None,
                    'long_query_time': 3,
                    'relay-log': "%s-relay-bin" % name,
                    'relay-log-index': "%s-relay-bin.index" % name,
                    'report-host': "%s-%s" % (socket.gethostname(), name),
                    'expire_logs_days': 28,
                    'skip-name-resolve': None,
                })

    def __str__(self):
        mysql_configs = ['[client]']
        mysqld_configs = ['[mysqld]']
        for k, v in sorted(self.client.items()):
            if v:
                mysql_configs.append("%s = %s" % (k, v))
            else:
                mysql_configs.append(k)

        for k, v in sorted(self.mysqld.items()):
            if v:
                mysqld_configs.append("%s = %s" % (k, v))
            else:
                mysqld_configs.append(k)

        return "%s\n\n%s" % ('\n'.join(mysql_configs), '\n'.join(mysqld_configs))

    def execute(self, operation):
        """execute console operation like: mysql ... -e 'operation'"""
        op = "%s --defaults-file=%s -u root -e \"%s\"" %\
            (os.path.join(self.basedir, 'bin', 'mysql'), self.defaults_file, operation)
        return execute(op)

    def get_defaults_filepath(self):
        return self.defaults_file

    def install_new_db(self):
        return install_new_db(self.datadir, self.basedir)

    def start_mysql_instance(self, wait_mysqld_start=3):
        with open(self.defaults_file, 'w') as f:
            f.write(str(self))

        # start mysql
        start_mysql = "%s --defaults-file=%s &" % (os.path.join(self.basedir, 'bin', 'mysqld_safe'), self.defaults_file)
        execute_in_background(start_mysql)
        res = "STARTING: %s" % start_mysql
        print res
        # in case the mysql does not start in time
        time.sleep(wait_mysqld_start)
        return res

    def setup_new_mysql(self):
        self.install_new_db()
        self.start_mysql_instance()
        if self.mysqld.get('replicate_do_db'):
            self.execute('create database %s' % self.mysqld.get('replicate_do_db'))
            print "Database: %s created" % self.mysqld.get('replicate_do_db')
        res = "SEE SEE:\n%s -u root -P %s -h 127.0.0.1\n%s -u root -P %s -h 127.0.0.1 shutdown"\
            % (os.path.join(self.basedir, 'bin', 'mysql'), self.port,
            os.path.join(self.basedir, 'bin', 'mysqladmin'), self.port)
        return res


def compile():
    """Compile mysql source
    TODO
    """
    print "http://dev.mysql.com/doc/refman/5.6/en/source-configuration-options.html"
    print "sudo apt-get install libncurses5 libncurses-dev"
    print "cmake -DCMAKE_INSTALL_PREFIX=~/services/mysql -DDEFAULT_CHARSET=utf8 -DDEFAULT_COLLATION=utf8_general_ci -DENABLED_LOCAL_INFILE=1 -DWITH_INNOBASE_STORAGE_ENGINE=1"


def create_mysql_configuration(cnf_file_name, basedir):
    pass


def parse_file_position(status):
    try:
        status_line = status.split('\n')[1]
        columns = status_line.split('\t')
    except IndexError as e:
        print status
        raise e
    log_file = columns[0].strip()
    log_position = columns[1].strip()
    return log_file, log_position


def create_master_slave_replication(mdatadir, sdatadir, basedir,
        mname='master1', sname='slave1', replicate_do_db='sync_db', mdefaults_file=None,
        sdefaults_file=None, mport=3391, sport=3392):
    """
    Password is hardcoded: replpass
    """
    master = MysqlConfig(name=mname, port=mport, basedir=basedir,
            datadir=mdatadir, defaults_file=mdefaults_file,
            replicate_do_db=replicate_do_db)
    slave = MysqlConfig(name=sname, port=sport, basedir=basedir,
            datadir=sdatadir, defaults_file=sdefaults_file,
            replicate_do_db=replicate_do_db)
    print master.setup_new_mysql()
    print slave.setup_new_mysql()

    grant_repl = "grant replication slave on *.* to \'repl\'@127.0.0.1 identified by \'replpass\'; flush privileges"
    #: (TODO) this kind of read lock is vainless
    flush_table = "flush tables with read lock"
    master.execute(grant_repl)
    master.execute(flush_table)
    master_status = master.execute("show master status")
    log_file, log_position = parse_file_position(master_status)

    change_master = "change master to master_host='127.0.0.1',\
        master_port=%s, master_user='repl', master_password='replpass',\
        master_log_file='%s', master_log_pos=%s;" % (mport, log_file, log_position)
    slave.execute(change_master)
    master.execute("unlock tables")
    slave.execute("start slave")


def create_master_master_replication(m1datadir, m2datadir, basedir,
        m1name='m1', m2name='m2', replicate_do_db='sync_db', m1defaults_file=None,
        m2defaults_file=None, m1port=3391, m2port=3392):


    def configure(basedir):
        m1_connect = "%s -u root -h 127.0.0.1 -P %s -e" % (os.path.join(basedir, 'bin', 'mysql'), m1port)
        m2_connect = "%s -u root -h 127.0.0.1 -P %s -e" % (os.path.join(basedir, 'bin', 'mysql'), m2port)

        grant_repl = "grant replication slave on *.* to \'repl\'@127.0.0.1 identified by \'replpass\'; flush privileges"
        flush_table = "flush tables with read lock"
        show_master_status = "show master status"
        execute("%s \"%s\"" % (m1_connect, grant_repl))
        execute("%s \"%s\"" % (m2_connect, grant_repl))
        execute("%s \"%s\"" % (m1_connect, flush_table))
        execute("%s \"%s\"" % (m2_connect, flush_table))

        result = execute("%s \"%s\"" % (m1_connect, show_master_status))
        m1log_file, m1log_pos = parse_file_position(result)
        result = execute("%s \"%s\"" % (m2_connect, show_master_status))
        m2log_file, m2log_pos = parse_file_position(result)
        # TODO: plain text is insecure.
        change_master_to_m1 = "change master to master_host='127.0.0.1',\
            master_port=%s, master_user='repl', master_password='replpass',\
            master_log_file='%s', master_log_pos=%s;" % (m1port, m1log_file, m1log_pos)
        change_master_to_m2 = "change master to master_host='127.0.0.1',\
            master_port=%s, master_user='repl', master_password='replpass',\
            master_log_file='%s', master_log_pos=%s;" % (m2port, m2log_file, m2log_pos)
        execute("%s \"%s\"" % (m1_connect, change_master_to_m2))
        execute("%s \"%s\"" % (m2_connect, change_master_to_m1))

        unlock = "unlock tables"
        start_slave = 'start slave'
        # lock should be released once it has determined the initial status of the other server
        # it would be fine even the server has not started slave
        m1config.execute(unlock)
        m2config.execute(unlock)
        m1config.execute(start_slave)
        m2config.execute(start_slave)

    m1config = MysqlConfig(name=m1name, port=m1port, basedir=basedir,
            datadir=m1datadir, defaults_file=m1defaults_file,
            auto_increment_offset=1, auto_increment_increment=2,
            replicate_do_db=replicate_do_db)
    m2config = MysqlConfig(name=m2name, port=m2port, basedir=basedir,
            datadir=m2datadir, defaults_file=m2defaults_file,
            auto_increment_offset=2, auto_increment_increment=2,
            replicate_do_db=replicate_do_db)
    visit_m1 = m1config.setup_new_mysql()
    visit_m2 = m2config.setup_new_mysql()

    configure(basedir)
    return '\n'.join([visit_m1, visit_m2])


def remove_files_recursively(path):
    execute('rm -rf %s' % path)


def _main(argv):
    parser = argparse.ArgumentParser(description="""
        mysql replicate tool: this tool assumes you would like to put mysql things in ~/services/mysql
        PLEASE CHECK THE DEFAULT SETTING CAREFULLY""")
    parser.add_argument('-b', '--basedir', help='default basedir: ~/services/mysql', default=os.path.expanduser('~/services/mysql'))
    parser.add_argument('-d', '--datadir', help='default datadir: ~/mysqldata', default=os.path.expanduser('~/mysqldata'))
    parser.add_argument('-db', '--replicate-db', help='default replicate db name: sync_db', default='sync_db')
    parser.add_argument('-n', '--name', help='db name: db1', default='db1')
    parser.add_argument('-n2', '--name2', help='db name: db2', default='db2')
    parser.add_argument('-p', '--port', help='db port: 3391', type=int, default=3391)
    parser.add_argument('-p2', '--port2', help='db port: 3392', type=int, default=3392)
    different_actions = parser.add_mutually_exclusive_group()
    different_actions.add_argument('-s', '--setup-new-mysql', help='setup a new mysql instance', action="store_true")
    different_actions.add_argument('-t', '--test', help='', action="store_true")
    different_actions.add_argument('-cmm', '--create-master-master', help='create a master master replication', action="store_true")
    different_actions.add_argument('-cms', '--create-master-slave', help='create a master slave replication', action="store_true")
    args = parser.parse_args()
    print args
    if args.setup_new_mysql:
        config = MysqlConfig(name=args.name, port=args.port, basedir=args.basedir,
                datadir=os.path.join(args.datadir, args.name),
                replicate_do_db=args.replicate_db)
        res = config.setup_new_mysql()
        print res
    elif args.create_master_master:
        m1datadir = os.path.join(args.datadir, args.name)
        m2datadir = os.path.join(args.datadir, args.name2)
        remove_files_recursively(m1datadir)
        remove_files_recursively(m2datadir)
        res = create_master_master_replication(m1datadir, m2datadir,
            basedir=args.basedir, m1name=args.name, m2name=args.name2,
            replicate_do_db=args.replicate_db, m1port=args.port, m2port=args.port2)
        print res
    elif args.create_master_slave:
        mdatadir = os.path.join(args.datadir, args.name)
        sdatadir = os.path.join(args.datadir, args.name2)
        remove_files_recursively(mdatadir)
        remove_files_recursively(sdatadir)
        res = create_master_slave_replication(mdatadir, sdatadir,
            basedir=args.basedir, mname=args.name, sname=args.name2,
            replicate_do_db=args.replicate_db, mport=args.port, sport=args.port2)
        print res
    else:
        compile()


if __name__ == '__main__':
    import sys
    _main(sys.argv)
