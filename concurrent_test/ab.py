# -*- coding: utf-8 -*-
"""
    ab.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import os
import subprocess
import argparse


def execute(concurrency, requests, intensity):
    result = None
    try:
        result = subprocess.check_output(
                ['ab', '-c', '%i' % concurrency, '-n', '%i' % requests, '10.5.0.43:18990/test/cpu?n=%i' % intensity],
                #['ab', '-c', '100', '-n', '100', 'http://10.5.0.43:18990/'],
                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print e
        print e.cmd, e.output
        raise
    return result


def parse_ab_result(result):
    statistics = {}
    for line in result.splitlines():
        if line.find(':') != -1:
            try:
                k, v = line.split(':')
            except ValueError as e:
                print e, line
            statistics[k.strip()] = v.strip()
            continue
        if line.find('%') != -1:
            try:
                k, v = line.split('%')
            except ValueError as e:
                print e, line
            statistics[k.strip()] = v.strip()
            continue
    return statistics


def output(outfile, statistics):
    fields = ["Document Path", "Concurrency Level", "Complete requests",
            "Failed requests", "Write errors", "Non-2xx responses",
            "Requests per second", "Time taken for tests",
            "50", "66", "75", "80", "90", "95", "98"]
    if isinstance(statistics, dict):
        statistics = [statistics]

    open(outfile, 'w').close()
    with open(outfile, 'a') as f:
        f.write("\t".join(fields) + "\n")
        for s in statistics:
            f.write("\t".join([s.get(field, '-') for field in fields]) + "\n")


def _main(argv):
    parser = argparse.ArgumentParser(description='apache benchmark wrapper')
    parser.add_argument('-n', '--requests', help='requests', type=int, default=100)
    parser.add_argument('-i', '--intensity', help='server side intensity', type=int, default=10)
    parser.add_argument('-o', '--output', help='output file', default='output.csv')
    different_actions = parser.add_mutually_exclusive_group()
    different_actions.add_argument('-c', '--concurrency', help='concurrency', type=int, default=100)
    different_actions.add_argument('-s', '--standard-test', help='execute standard test', action="store_true")
    args = parser.parse_args()
    print args
    if args.standard_test:
        statistics = []
        for c in (100, 1000, 2000, 5000, 10000):
            for n in (c, c * 10):
                for i in (1, 2, 10):
                    print 'performing', c, n, i
                    try:
                        r = execute(c, n, i)
                    except subprocess.CalledProcessError:
                        print "fail in", c, n, i
                        r = "Concurrency Level: FAIL at %i %i %i" % (c, n, i)
                    s = parse_ab_result(r)
                    statistics.append(s)
    elif args.concurrency:
        result = execute(args.concurrency, args.requests, args.intensity)
        statistics = parse_ab_result(result)
    output(args.output, statistics)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
