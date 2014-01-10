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


stdout_file = open('stdout.txt', 'a')
stderr_file = open('stderr.txt', 'a')

class MysqlConfig(object):
    def __init__(self, name, port, server_id, basedir, datadir, socket=None, **kwargs):
        socket = os.path.join(datadir, "%s.sock" % name) if not socket else socket
        self.mysql = {
                    'port': port,
                    'socket': socket,
                }
        self.mysqld = kwargs
        self.mysqld.update({
                    'port': port,
                    'log_bin': "%s-bin" % name,
                    'server_id': server_id,
                    'basedir': basedir,
                    'datadir': datadir,
                    'log-slave-updates': None,
                    'sync_binlog': 1,
                    'binlog-ignore-db': 'mysql',
                    'replicate-ignore-db': 'mysql,information_schema',
                    'socket': socket,
                })

    def __str__(self):
        mysql_configs = ['[mysql]']
        mysqld_configs = ['[mysqld]']
        for k, v in sorted(self.mysql.items()):
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


def compile():
    """Compile mysql source
    TODO
    """
    print "sudo apt-get install libncurses5 libncurses-dev"
    print "cmake -DCMAKE_INSTALL_PREFIX=~/services/mysql"


def install_new_db(datadir, basedir):
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    mysql_install_db = os.path.join(basedir, 'scripts', 'mysql_install_db')
    cmd = "%s --basedir=%s --datadir=%s --no-defaults" % (mysql_install_db, basedir, datadir)
    print "INSTALL NEW DB at %s" % datadir
    result = execute(cmd)
    return result


def create_mysql_configuration(cnf_file_name, basedir):
    pass


def create_master_master_replication(m1datadir, m2datadir, basedir,
        m1name='m1', m2name='m2', sync_db='sync_db', m1defaults_file=None,
        m2defaults_file=None, m1port=3391, m2port=3392):

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

    def configure():
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
        execute("%s \"%s\"" % (m1_connect, unlock))
        execute("%s \"%s\"" % (m2_connect, unlock))
        execute("%s \"%s\"" % (m1_connect, start_slave))
        execute("%s \"%s\"" % (m2_connect, start_slave))

    m1defaults_file = os.path.join(basedir, "%s.cnf" % m1name) if not m1defaults_file else m1defaults_file
    m2defaults_file = os.path.join(basedir, "%s.cnf" % m2name) if not m2defaults_file else m2defaults_file
    m1_connect = "%s -u root -h 127.0.0.1 -P %s -e" % (os.path.join(basedir, 'bin', 'mysql'), m1port)
    m2_connect = "%s -u root -h 127.0.0.1 -P %s -e" % (os.path.join(basedir, 'bin', 'mysql'), m2port)
    def setup():
        install_new_db(m1datadir, basedir)
        install_new_db(m2datadir, basedir)
        m1config = MysqlConfig(name=m1name, port=m1port, server_id=91, basedir=basedir,
                datadir=m1datadir, auto_increment_offset=1, auto_increment_increment=2,
                binlog_do_db=sync_db, replicate_do_db=sync_db)
        m2config = MysqlConfig(name=m2name, port=m2port, server_id=92, basedir=basedir,
                datadir=m2datadir, auto_increment_offset=2, auto_increment_increment=2,
                binlog_do_db=sync_db, replicate_do_db=sync_db)
        with open(m1defaults_file, 'w') as f:
            f.write(str(m1config))
        with open(m2defaults_file, 'w') as f:
            f.write(str(m2config))

        # start mysql
        start_mysql = "%s --defaults-file=%%s &" % (os.path.join(basedir, 'bin', 'mysqld_safe'))
        execute_in_background(start_mysql % m1defaults_file)
        execute_in_background(start_mysql % m2defaults_file)
        # in case the mysql does not start in time
        time.sleep(3)
    setup()
    configure()


def remove_files_recursively(path):
    execute('rm -rf %s' % path)


def _main(argv):
    parser = argparse.ArgumentParser(description='mysql replicate tool: this tool'
           'assumes you would like to put mysql things in ~/services/mysql'
           'PLEASE CHECK THE DEFAULT SETTING CAREFULLY')
    parser.add_argument('-b', '--basedir', help='default basedir: ~/services/mysql', default=os.path.expanduser('~/services/mysql'))
    parser.add_argument('-d', '--datadir', help='default datadir: ~/mysqldata', default=os.path.expanduser('~/mysqldata'))
    parser.add_argument('-db', '--dbname', help='default db name: sync_db', default='sync_db')
    parser.add_argument('-n', '--name', help='db name: db1', default='db1')
    parser.add_argument('-n2', '--name2', help='db name: db1', default='db2')
    parser.add_argument('-p', '--port', help='db port: 3391', type=int, default=3391)
    parser.add_argument('-p2', '--port2', help='db port: 3392', type=int, default=3392)
    different_actions = parser.add_mutually_exclusive_group()
    different_actions.add_argument('-c', '--create-single-db', help='', action="store_true")
    different_actions.add_argument('-t', '--test', help='', action="store_true")
    different_actions.add_argument('-cmm', '--create-master-master', help='', action="store_true")
    args = parser.parse_args()
    print args
    if args.create_single_db:
        install_new_db(datadir=args.datadir, basedir=args.basedir)
    elif args.create_master_master:
        m1datadir = os.path.join(args.datadir, args.name)
        m2datadir = os.path.join(args.datadir, args.name2)
        remove_files_recursively(m1datadir)
        remove_files_recursively(m2datadir)
        create_master_master_replication(m1datadir, m2datadir,
            basedir=args.basedir, m1name=args.name, m2name=args.name2,
            sync_db=args.dbname, m1port=args.port, m2port=args.port2)
        print "SEE SEE: %s -u root -P %s -h 127.0.0.1" % (os.path.join(args.basedir, 'bin', 'mysql'), args.port)
        print "SEE SEE: %s -u root -P %s -h 127.0.0.1" % (os.path.join(args.basedir, 'bin', 'mysql'), args.port2)
    else:
        compile()


if __name__ == '__main__':
    import sys
    _main(sys.argv)
