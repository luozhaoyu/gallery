# -*- coding: utf-8 -*-
"""
    wordlib.py
    ~~~~~~~~~~~~~~

    useful toolkit of words' related operations
"""
import os
import re


def is_word(alphas):
    if not alphas[0].isalpha() or alphas.find('.') != -1 or alphas.find('+') != -1:
        return False
    else:
        return True


def get_words(words_file):
    """
    space is acceptable, characters before the frist tab is recognized as a word

    Returns:
        [wordslist]
    """
    words = []
    try:
        with open(words_file, 'r') as f:
            line = f.readline()
            while line:
                wordmatches = re.match(r'[a-zA_Z-]+', line)
                if wordmatches:
                    word = wordmatches.group()
                    if word and is_word(word):
                        words.append(word)
                line=f.readline()
    except IOError:
        return []
    return words


def get_words_among_folder(folder_path):
    """
    Returns:
        ()
    """
    result = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            file_path = os.path.join(root, f)
            words = get_words(file_path)
            result.extend(words)
    result = set(result)
    return result


def get_difference_words(existed_file, wordfile=None, wordfolder=None):
    exists_words = get_words(existed_file)
    if wordfile:
        words = get_words(wordfile)
    elif wordfolder:
        words = get_words_among_folder(wordfolder)
    else:
        print "INPUT WORD FILE IS EMPTY"
        words = []
    need_query_words = set(words).difference(exists_words)
    return need_query_words


def _main(argv):
    pass


if __name__ == '__main__':
    import sys
    _main(sys.argv)
