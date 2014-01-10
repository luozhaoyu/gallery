# -*- coding: utf-8 -*-
"""
    hindex.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import re
import argparse
def get_researchers_info(infile):
    info = {}
    with open(infile, 'r') as f:
        for line in f.readlines():
            m = re.match(r"(?P<index>\d+) (?P<name>[^\(]+) \((?P<org>.*?)\)[,]{0,1}[ ]{0,1}(?P<detail>.*)", line.strip())
            if m:
                researcher = m.groupdict()
                org = re.sub(r"^U | U$", '', researcher['org']).strip()
                if info.has_key(org):
                    info[org].append(researcher)
                else:
                    info[org] = [researcher]
            else:
                print line
    return info


def aggregate_researcher_info(info, outfile):
    fields = ['org', 'index', 'name', 'detail']
    lines = []
    overall = []
    for org in sorted(info, key=lambda k: (
        len(info[k]),
        sum([int(i['index']) for i in info[k]]),
        sum([len(i['detail']) for i in info[k]])
        )):
    #for org in sorted(info, key=lambda k: (len(info[k]), sum([int(index) for index in info[k]])int(info[k][0]['index']), len(info[k][0]['detail']))):
        researchers = info[org]
        line = "%i %s: %i" % (len(info[org]), org, sum([int(i['index']) for i in info[org]]))
        overall.append(line)
        for r in sorted(researchers, key=lambda i: (int(i['index']), len(i['detail']))):
            line = "\t".join([r.get(f) for f in fields])
            lines.append(line)

    with open(outfile, 'w') as f:
        for line in lines:
            f.writelines(line + '\n')
        for line in overall:
            f.writelines(line + '\n')
#        for line in lines:
#            f.write(line)


def _main(argv):
    parser = argparse.ArgumentParser(description='aggregate hindex')
    parser.add_argument('-i', '--input', help='origin file of hindex', default='hindex.txt')
    parser.add_argument('-o', '--output', help='output file', default='hindex_rank.txt')
    args = parser.parse_args()
    info = get_researchers_info(infile=args.input)
    result = aggregate_researcher_info(info, outfile=args.output)
    


if __name__ == '__main__':
    import sys
    _main(sys.argv)
