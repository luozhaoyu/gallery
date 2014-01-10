# -*- coding: utf-8 -*-
"""
    remote_install.py
    ~~~~~~~~~~~~~~

    install softs in remote machines.
"""
import os
from fabric.api import run, cd, settings, env


packages_raw_test = [
        ['sqlalchemy-0.6.9', '.tgz', 'http://downloads.sourceforge.net/project/sqlalchemy/sqlalchemy/0.6.9/SQLAlchemy-0.6.9.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fsqlalchemy%2Ffiles%2Fsqlalchemy%2F0.6.9%2F&ts=1350359250&use_mirror=voxel', None, None],
        [],
        ]

def get_packages_info(packages_raw):
    packages = {}
    for p, i in enumerate(packages_raw):
        packages[i] = {
                    'soft_name': p[1],
                    'soft_format': p[2],
                    'source': p[3],
                    'prefix': p[4],
                    'configure': p[5]
                }
    return packages


def install_packages(default_prefix='/home/jiepang', packages_raw=None):
    packages = get_packages_info(packages_raw)
    for i in packages:
        source = i['source']
        download_name = i['download_name']
        prefix = i['prefix'] if i['prefix'] else default_prefix
        configure = i['configure']
        download_abspath = download_tarfile(source=source, download_name=download_name, download_folder=prefix)
        makeinstall_software(download_file=download_abspath,configure=configure)


def makeinstall_software(download_file, prefix, configure=None):
    extract = 'tar zxvf %s -C %s' % ()
    run(extract)
    if configure:
        # cd
        run(configure)
    makeinstall = 'make || make all || make install'
    with settings(warn_only=True):
        run(makeinstall)


def download_tarfile(source, download_name, download_folder):
    download_abspath = os.path.join(download_folder.strip('/'), download_name)
    wget = "wget -t 10 -c -O %s %s" % (download_abspath, source)
    print wget
    run(wget)
    return download_abspath


def _main(argv):
    print env
    install_packages('/home/jiepang', packages_raw_test)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
