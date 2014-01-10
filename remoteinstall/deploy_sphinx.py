# -*- coding: utf-8 -*-
"""
    deploy_sphinx.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
from fab import env
from remote_install import install_packages

def deploy():
    print env

def install():
    packages_raw = [['sphinx', '', 'prefix', 'configure']]
    install_packages(packages_raw)

def reconfigure():
    pass


def _main(argv):
    deploy()


if __name__ == '__main__':
    import sys
    _main(sys.argv)
