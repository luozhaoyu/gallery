# -*- coding: utf-8 -*-
"""
    check_haproxy.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import argparse
import urllib2
import os
import sys

from bottle import route, run, template


def get_haproxy_stats(haproxy_csv_url, user=None, password=None):
    # create a password manager
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

    # Add the username and password.
    # If we knew the realm, we could use it instead of None.
    password_mgr.add_password(None, haproxy_csv_url, user, password)

    handler = urllib2.HTTPBasicAuthHandler(password_mgr)

    # create "opener" (OpenerDirector instance)
    opener = urllib2.build_opener(handler)

    # use the opener to fetch a URL
    rawdata = opener.open(haproxy_csv_url).readlines()
    header = rawdata[0].strip('#').strip()
    info = []
    for i in rawdata[1:]:
        d = dict(zip(header.split(','), i.strip().split(',')))
        del d['']
        info.append(d)
    return info


def get_front_back_stats(info):
    stats = {}
    for i in info:
        if i['svname'].lower() in ['backend', 'frontend']:
            stats[i['svname'].lower()] = {
                'rate': i['rate'],
                'scur': i['scur'],
                'wretr': i['wretr'],
            }
    return stats


@route('/')
def index():
    info = get_haproxy_stats(os.environ['url'], os.environ['user'], os.environ['password'])
    stats = get_front_back_stats(info)
    jiankongbao = '\n'.join([
        "front_rate:%s" % stats['frontend']['rate'],
        "back_rate:%s" % stats['backend']['rate'],
        "front_scur:%s" % stats['frontend']['scur'],
        "back_scur:%s" % stats['backend']['scur'],
        ])
    return template('<pre>{{jiankongbao}}</pre>', jiankongbao=jiankongbao)


def _main(argv):
    parser = argparse.ArgumentParser(description='check your system memory')
    parser.add_argument('-w', '--warning', help='warning threshold', nargs=1, required=False, type=int)
    parser.add_argument('-c', '--critical', help='critical threshold', nargs=1, required=False, type=int)
    parser.add_argument('-r', '--run', help='run as a server', action='store_true')
    parser.add_argument('-P', '--port', help='port: 12390', type=int, default=12390)
    parser.add_argument('--host', help='listen host: 0.0.0.0', default='0.0.0.0')
    parser.add_argument('-u', '--user', help='user', default=None)
    parser.add_argument('-p', '--password', help='password', default=None)
    parser.add_argument('-U', '--url', help='haproxy csv output url like: http://127.0.0.1/stats;csv;norefresh')
    args = parser.parse_args()
    os.environ['url'] = args.url
    os.environ['user'] = args.user
    os.environ['password'] = args.password

    if args.run:
        run(host=args.host, port=args.port)
    else:
        info = get_haproxy_stats(args.url, args.user, args.password)
        stats = get_front_back_stats(info)
        front_rate = int(stats['frontend']['rate'])
        front_scur = int(stats['frontend']['scur'])
        back_rate = int(stats['backend']['rate'])
        back_scur = int(stats['backend']['scur'])
        print "front_rate: %s\tfront_scur: %s\tback_rate: %s\tback_scur: %s" %\
            (front_rate, front_scur, back_rate, back_scur)
        if front_rate > args.critical[0]:
            sys.exit(2)
        elif front_rate > args.warning[0]:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
