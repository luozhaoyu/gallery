# -*- coding: utf-8 -*-
"""
    gpa.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import argparse
import re

def get_gpa(inputfile, outputfile=None):
    gpa = 0
    total_credit = 0
    with open(inputfile, 'r') as f:
        for line in f.readlines():
            credit, score = map(float, re.split(r'\s+', line.strip()))
            total_credit += credit
            gpa += credit * score
    gpa /= total_credit
    return gpa


def _main(argv):
    parser = argparse.ArgumentParser(description='aggregate hindex')
    parser.add_argument('-i', '--input', help='origin file of hindex', default='hindex.txt')
    parser.add_argument('-o', '--output', help='output file', default='hindex_rank.txt')
    args = parser.parse_args()
    gpa = get_gpa(args.input)
    print gpa, gpa / 100 * 4
    


if __name__ == '__main__':
    import sys
    _main(sys.argv)
