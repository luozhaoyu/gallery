# -*- coding: utf-8 -*-
"""
    parse_web_log.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import os
import re
import time
import subprocess


def output(string):
    print string


def parse_lines(lines, start_time=None, verbose=False):
    """
    Args:
        start_time: parse only log time after the specified time string, such as "1998-08-23 21:12:08"
    Yields:
        {}
    """
    if not lines:
        yield None
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
    for line in lines:
        match = log_re.match(line)
        if match:
            d = match.groupdict()
            if start_time:
                if time.strptime(d['time'].split(' ')[0], "%d/%b/%Y:%H:%M:%S") >=\
                    time.strptime(start_time, "%Y-%m-%d %H:%M:%S"):
                    yield d
                else:
                    continue
            else:
                yield d
        else:
            if verbose:
                output("UNMATCHED LINE: %s" % line)


def parse_single_log(logfile, start_time=None):
    """
    Returns:
        res: generator of [{}, {}], it is yielded
    """
    try:
        f = open(logfile, 'r')
        filesize = os.fstat(f.fileno()).st_size
        lines = f.readlines()
    finally:
        f.close()

    if filesize == 0:
        return []

    output("Parsing %s from time: %s..." % (logfile, start_time))
    res = parse_lines(lines, start_time=start_time)
    return res


def execute(cmd):
    result = None
    try:
        result = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                shell=True)
    except subprocess.CalledProcessError as e:
        output("%s %s: %s" % (e.returncode, e.cmd, e.output))
        raise e
    return result


def parse_single_log_with_pregrep(logfile, grepcmd, start_time=None, tmp_folder=None, force_grep=False):
    """grep that file before parsing it
    Program would skip grep if the tmp file exists TODO

    Args:
        tmp_folder: the tmp file would be stored here if it is set
        force_grep: it would grep the logfile no matter whether the tmpfile exists
    """
    if not grepcmd:
        return parse_single_log(logfile, start_time=start_time)

    output("Greping %s from time: %s... force_grep: %s" % (logfile, start_time, force_grep))

    logfilepath = os.path.abspath(logfile)
    log_name = os.path.basename(logfilepath)
    tmp_folderpath = os.path.abspath(tmp_folder if tmp_folder else '.')
    tmp_filepath = os.path.join(tmp_folderpath, log_name + '.pregrep')
    if force_grep or not os.path.exists(tmp_filepath):
        cmd = "%s %s > %s" % (grepcmd, logfilepath, tmp_filepath)
        try:
            execute(cmd)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:  # grepped, but matched nothing
                return []  # CAREFUL! blank list should be returned since one file return one list
            else:
                raise e

    res = parse_single_log(tmp_filepath, start_time=start_time)

    if not tmp_folder:
        output('removing %s' % tmp_filepath)
        os.remove(tmp_filepath)
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


def parse_folder(folder, start_time=None, grepcmd=None, tmp_folder=None, force_grep=False):
    """
    Args:
        grepcmd, tmp_folder, force_grep's default value should be the same with parse_single_log_with_pregrep

    Yields:
        [[yield], []]: nested yields
    """
    def get_first_last_line(filepath):
        f = open(filepath, 'rb')
        filesize = os.fstat(f.fileno()).st_size
        if filesize == 0:
            return '', ''

        offset = -min(1024, filesize)
        first = next(f)
        while True:
            f.seek(offset, os.SEEK_END)
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

    for each_file in all_files:
        if start_time:
            first, last = get_first_last_line(each_file)
            last_row = list(parse_lines([last], start_time))
            if last_row:
                if grepcmd:
                    yield parse_single_log_with_pregrep(each_file,
                        grepcmd=grepcmd, start_time=start_time, tmp_folder=tmp_folder, force_grep=force_grep)
                else:
                    yield parse_single_log(each_file, start_time=start_time)
            else:
                output('ignore file: %s' % each_file)
        else:
            if grepcmd:
                yield parse_single_log_with_pregrep(each_file,
                    grepcmd=grepcmd, start_time=start_time, tmp_folder=tmp_folder, force_grep=force_grep)
            else:
                yield parse_single_log(each_file)


def _main(argv):
    import argparse
    parser = argparse.ArgumentParser(description='parse web log')
    exclusives = parser.add_mutually_exclusive_group()
    exclusives.add_argument('-l', '--log', help='single log file')
    exclusives.add_argument('-f', '--folder', help='folder')
    parser.add_argument('-t', '--time', help='filter out logs after startime such as: 1998-12-11 10:23:37', default=None)
    parser.add_argument('-g', '--grep', help='pregrep', action='store_true')
    parser.add_argument('-tmp', '--tmp-folder', help='tmp folder', default='.')
    args = parser.parse_args()
    print args
    grepcmd = "grep -P \"stats_click.php|stats_imp.php\""
    parse_single_log_with_pregrep(args.log, grepcmd=grepcmd, start_time=args.time, tmp_folder=args.tmp_folder)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
