#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    beep.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import subprocess
import sys

def beep(s):
    MINTONE = 261.6
    MAXTONE = 523.2
    frequencies = []
    for c in s:
        try:
            if ord(c) > ord('z') or ord(c) < ord('A'):
                f = 20
                l = 50
            else:
                f = MINTONE + float((ord(c) - ord('A'))) / (ord('z') - ord('A')) * (MAXTONE - MINTONE)
                l = 100
        except TypeError as e:
            continue
        frequencies.append((f, l))
    cmd = "beep %s" % " -n ".join(["-f %s -l %s" % (i[0], i[1]) for i in frequencies])
    print cmd
    result = subprocess.check_output(cmd, shell=True)
    print result

def _main(argv):
    if len(argv) > 1:
        string = argv[1]
        beep(string)
    else:
        while True:
            #string = sys.stdin.readlines()[0]
            string = sys.stdin.readline()
            beep(string)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
