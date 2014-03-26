# -*- coding: utf-8 -*-
"""
    parse_web_log.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import os
import io
import re
import time
import argparse


def parse_lines(lines, start_time=None):
    """
    Args:
        start_time: parse only log time after the specified time string, such as "1998-08-23 21:12:08"
    Returns:
        [{}, {}]
    """
    if not lines:
        return []
    # LogFormat "%{X-Forwarded-For}i %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"" lbcombined
    # 211.140.5.102 - - [19/Mar/2014:00:00:00 +0800] "GET ailbreak=0 HTTP/1.1" 200 8522 "-" "PopStar/1.7.1 CF/72.0.8 Darwin/14.0.0"
    # 211.140.5.102, 1.2.3.4 - - [19/Mar/2014:00:00:00 +0800] "GET ailbreak=0 HTTP/1.1" 200 8522 "-" "PopStar/1.7.1 CF/72.0.8 Darwin/14.0.0"
    log_re = re.compile(
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
            d = match.groupdict()
            if start_time:
                if time.strptime(d['time'].split(' ')[0], "%d/%b/%Y:%H:%M:%S") >=\
                    time.strptime(start_time, "%Y-%m-%d %H:%M:%S"):
                    res.append(d)
                else:
                    continue
            else:
                res.append(d)
        else:
            print "UNMATCHED LINE:", line
    return res


def parse_single_log(logfile, start_time=None):
    """
    Returns:
        [{}, {}]
    """
    try:
        f = open(logfile, 'r')
        filesize = os.fstat(f.fileno()).st_size
        lines = f.readlines()
    finally:
        f.close()

    if filesize == 0:
        return []

    res = parse_lines(lines, start_time=start_time)
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


def parse_folder(folder, start_time=None):
    def get_first_last_line(filepath):
        f = open(filepath, 'rb')
        filesize = os.fstat(f.fileno()).st_size
        if filesize == 0:
            return '', ''

        offset = -min(1024, filesize)
        first = next(f)
        while True:
            f.seek(offset, io.SEEK_END)
            lines = f.readlines()
            if len(lines) >= 1:
                last = lines[-1]
                break
            offset *= 2
        return first, last

    all_files = get_recursive_files(folder)
    # It is very IMPORTANT to parse each log file in order
    # since the other application may find the last row in database to resume its operation
    all_files.sort()
    res = []
    for each_file in all_files:
        if start_time:
            first, last = get_first_last_line(each_file)
            last_row = parse_lines([last], start_time)
            if last_row:
                res.append(parse_single_log(each_file, start_time=start_time))
            else:
                print 'ignore file:', each_file
        else:
            res.append(parse_single_log(each_file))
    return res


def _main(argv):
    parser = argparse.ArgumentParser(description='parse web log')
    exclusives = parser.add_mutually_exclusive_group()
    exclusives.add_argument('-l', '--log', help='single log file')
    exclusives.add_argument('-f', '--folder', help='folder')
    parser.add_argument('-t', '--time', help='filter out logs after startime such as: 1998-12-11 10:23:37', default=None)
    args = parser.parse_args()
    print args
    res = parse_folder(args.folder, args.time)
    print res



if __name__ == '__main__':
    import sys
    _main(sys.argv)
