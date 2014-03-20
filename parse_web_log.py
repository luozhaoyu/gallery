# -*- coding: utf-8 -*-
"""
    parse_web_log.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import os
import re
import argparse


def parse_lines(lines):
    """
    Returns:
        [{}, {}]
    """
    # LogFormat "%{X-Forwarded-For}i %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"" lbcombined
    # 211.140.5.102 - - [19/Mar/2014:00:00:00 +0800] "GET ailbreak=0 HTTP/1.1" 200 8522 "-" "PopStar/1.7.1 CF/72.0.8 Darwin/14.0.0"
    # 211.140.5.102, 1.2.3.4 - - [19/Mar/2014:00:00:00 +0800] "GET ailbreak=0 HTTP/1.1" 200 8522 "-" "PopStar/1.7.1 CF/72.0.8 Darwin/14.0.0"
    log_re = re.compile(
        #r"(?P<host>(([\d\.]+)(, ){0, 1})+)\s"
        r"(?P<host>[\d\., ]+)\s"
        r"(?P<identity>\S*)\s"
        r"(?P<user>\S*)\s"
        r"\[(?P<time>.*?)\]\s"
        r'"(?P<request>.*?)"\s'
        r"(?P<status>\d+)\s"
        r"(?P<bytes>\d+)\s"
        r'"(?P<referer>.*?)"\s'
        r'"(?P<user_agent>.*?)"\s*'
        r"(?P<others>.*?)"
    )
    res = []
    for line in lines:
        match = log_re.match(line)
        if match:
            res.append(match.groupdict())
        else:
            print line
    return res


def parse_single_log(logfile):
    """
    Returns:
        [{}, {}]
    """
    with open(logfile, 'r') as f:
        lines = f.readlines()
    res = parse_lines(lines)
    return res


def get_recursive_files(folder_path):
    """
    Returns:
        [], sub-files
    """
    result = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            file_path = os.path.join(root, f)
            result.append(file_path)
    return result


def _main(argv):
    parser = argparse.ArgumentParser(description='parse web log')
    exclusives = parser.add_mutually_exclusive_group()
    exclusives.add_argument('-l', '--log', help='single log file')
    exclusives.add_argument('-f', '--folder', help='folder')
    #parser.add_argument('log', help='single log file')
    args = parser.parse_args()
    print args
    print parse_single_log(args.log)



if __name__ == '__main__':
    import sys
    _main(sys.argv)
