# -*- coding: utf-8 -*-
"""
    logging_wrapper.py
    ~~~~~~~~~~~~~~

    include logging_wrapper.py
    include urlopen_wrapper.py
    A brief description goes here.
"""
import logging
import logging.handlers

import urllib
import urllib2
import json


def create_logger(filename, logger_name=None):
    logger = logging.getLogger(logger_name)
    fmt='[%(asctime)s] %(levelname)s [#%(process)d %(funcName)s %(filename)s:%(lineno)d] %(message)s'
    datefmt="%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    handler = logging.handlers.RotatingFileHandler(filename, maxBytes=1024 * 1024 * 1024, backupCount=10)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def urlopen_http(host, path, port=80, querys={}, timeout=5, data=None, deserialize_json=True):
    """call remote service in http

    Args:
        data: if this is a 'post' request, put data here

    Returns:
        False, some exception happened
    """
    try:
        request_url = "http://%s:%s/%s?%s" % (host, port, path, urllib.urlencode(querys))
    except TypeError:
        raise TypeError("querys: %s" % querys)

    try:
        if data:
            result = urllib2.urlopen(request_url, data=urllib.urlencode(data), timeout=timeout).read()
        else:
            result = urllib2.urlopen(request_url, timeout=timeout).read()
        if deserialize_json:
            result = json.loads(result)
    except Exception:
        raise Exception("%s: %s" % (request_url, data))
    return result


def _main(argv):
    l = create_logger('guohe_itemcf.log')
    l.warning("fuck")


if __name__ == '__main__':
    import sys
    _main(sys.argv)
