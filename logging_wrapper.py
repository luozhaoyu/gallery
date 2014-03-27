# -*- coding: utf-8 -*-
"""
    logging_wrapper.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import logging
import logging.handlers


def create_logger(filename, logger_name=None):
    logger = logging.getLogger(logger_name or __name__)
    fmt='[%(asctime)s] %(levelname)s [#%(process)d %(funcName)s %(filename)s:%(lineno)d] %(message)s'
    datefmt="%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    handler = logging.handlers.RotatingFileHandler(filename, maxBytes=1024 * 1024 * 1024, backupCount=10)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def _main(argv):
    l = create_logger('guohe_itemcf.log')
    l.warning("fuck")


if __name__ == '__main__':
    import sys
    _main(sys.argv)
