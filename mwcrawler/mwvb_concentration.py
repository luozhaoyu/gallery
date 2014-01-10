# -*- coding: utf-8 -*-
"""
    mwvb_concentration.py
    ~~~~~~~~~~~~~~

    get a short brief version of merriam-webster vocabulary builder
"""
def concentrate(infile='mwvb.txt', outfile='mwvb_synopsis.txt'):
    out = open(outfile, 'w')
    with open(infile, 'r') as f:
        sample_words = []
        for line in f:
            first_word = line.strip().split(' ')[0]
            if first_word == line.strip() or not first_word[0].isalpha():
                continue
            elif len(first_word) == 1 or (len(first_word) == 2 and first_word[1] == '.'):
                if len(first_word) == 1:
                    print line
                continue
            elif first_word == 'same' and line.find('__'):
                continue
            if first_word == first_word.upper():
                out.write("::\t%s\n\n" % ' '.join(sample_words))
                out.write(line.strip() + '::\n')
                sample_words = []
            elif first_word == first_word.lower():
                sample_words.append(first_word)
    out.close()


def _main(argv):
    concentrate()


if __name__ == '__main__':
    import sys
    _main(sys.argv)
