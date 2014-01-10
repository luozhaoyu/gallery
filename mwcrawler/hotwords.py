# -*- coding: utf-8 -*-
"""
    hotwords.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import argparse
import mwcrawler

import wordlib

def get_words_frequencies(infile):
    """
    Returns:
        {word: 10}
    """
    word_frequency = {}
    with open(infile, 'r') as f:
        for line in f:
            word, frequency = line.strip().split(' ')
            word_frequency[word] = int(frequency)
    return word_frequency


def get_words_info(words, frequency_file):
    """
    Returns:
        {word: {'frequency': 10, 'entries': [{}, {}]}}
    """
    words_frequencies = get_words_frequencies(frequency_file)
    words_entries = mwcrawler.get_words_entries(words)
    words_info = {}
    for word in words_entries:
        words_info[word] = {'frequency': words_frequencies.get(word, 0),
                            'detail': words_entries[word]['detail']}
    return words_info


def write_words_info(words_info, outputfile):
    """
    Write:
        word with frequency meaning
        only word
    """
    verbose_output = open(outputfile, 'a')
    word_only_output = open(outputfile + '.simple.txt', 'a')
    for index, word in enumerate(
            sorted(words_info,
            key=lambda x: words_info[x]['frequency'],
            reverse=True)):
        word_info = words_info[word]
        frequency = word_info['frequency']
        detail = word_info['detail']
        senses = []
        for entry in detail:
            senses.extend(entry.get('senses'))
        meaning = '\t'.join([sense.get('mc', '') for sense in senses])
        line = "%s\t%i\t%s\n" % (word, frequency, meaning)
        verbose_output.write(line)
        if index % 10 == 0:
            word_only_output.write("%s \n%i " % (word, index + 1))
        else:
            word_only_output.write(word + ' ')
    verbose_output.close()
    word_only_output.close()


def _main(argv):
    parser = argparse.ArgumentParser(description='hot words with meaning in merriam-webster & sorted by frequency')
    parser.add_argument('-l', '--list', help='word list file need to get checked', default='hotword.txt')
    parser.add_argument('-o', '--output', help='output file', default='hotword_info')
    parser.add_argument('-d', '--debug', help='not query', default='')
    args = parser.parse_args()
    print args
    need_query_words = wordlib.get_difference_words(existed_file=args.output, wordfile=args.list)
    print need_query_words
    if args.debug != 'debug':
        need_query_words = list(need_query_words)
        for i in range(len(need_query_words) / 10 + 1):
            query_words = need_query_words[i * 10 : i * 10+10]
            words_info = get_words_info(query_words, 'word_frequency.txt')
            print 'writing', query_words
            write_words_info(words_info, args.output)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
