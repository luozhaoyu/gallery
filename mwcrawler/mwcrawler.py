# -*- coding: utf-8 -*-
"""
    mwcrawler.py
    ~~~~~~~~~~~~~~

    get merriam-webster's word definition by crawling
"""
import urllib
import urllib2
from xml.dom.minidom import parseString
import argparse
import re
import os

import wordlib

THESAURUS_KEY = '3df8ba2b-d796-4541-a3b2-477436bf9af8'
DICTIONARY_KEY = '688593d7-bfcb-4302-9473-65cc7cac14f0'

def query_word_xml(word, dictionary='theaurus'):
    if dictionary.lower().startswith('theaurus'):
        request_url = "http://www.dictionaryapi.com/api/v1/references/thesaurus/xml/%s?key=%s" % (urllib.quote_plus(word), THESAURUS_KEY)
    else:
        request_url = "http://www.dictionaryapi.com/api/v1/references/collegiate/xml/%s?key=%s" % (urllib.quote_plus(word), DICTIONARY_KEY)
    print request_url
    timeout = 40
    result = urllib2.urlopen(request_url, data=None, timeout=timeout).read()
    return result


T = '<?xml version="1.0" encoding="utf-8" ?>\r\n<entry_list version="1.0">\n\t<entry id="hello"><term><hw>hello</hw></term><fl>noun</fl><sens><mc>an expression of goodwill upon meeting</mc><vi>we said our <it>hellos</it> and got right down to business</vi><syn>greeting, salutation, salute, welcome</syn><rel>ave, hail; amenities, civilities, pleasantries; regards, respects, wishes</rel><ant>adieu, bon voyage, cong\xc3\xa9 (<it>also</it> congee), farewell, Godspeed, good-bye (<it>or</it> good-by)</ant></sens></entry>\r\n</entry_list>'

def get_raw_text(xml_element):
    if xml_element.nodeType == 3:  # Text Node
        return xml_element.nodeValue
    else:
        return ' '.join([get_raw_text(i) for i in xml_element.childNodes])


def parse_word_xml(word_xml):
    """
    Args:
        word_xml: entry_list

    Returns:
        [entry, entry, entry ...],
        entry: {'hw':, 'fl':, [sens, sens, sens ...]}
        sens := [{'mc':, 'syn':, 'ant': ...}, {}]
    """
    word_dom = parseString(word_xml)
    #word_entries = word_dom.getElementsByTagName('entry_list')[0].getElementsByTagName('entry')
    word_entries = word_dom.getElementsByTagName('entry')
    entries = []
    for entry in word_entries:
        hw = get_raw_text(entry.getElementsByTagName('hw')[0])
        fl = get_raw_text(entry.getElementsByTagName('fl')[0])
        word_senses = entry.getElementsByTagName('sens')
        senses = []
        for sense in word_senses:
            try:
                mc = get_raw_text(sense.getElementsByTagName('mc')[0])
            except IndexError as e:
                print e
                continue
            try:
                syn = get_raw_text(sense.getElementsByTagName('syn')[0])
            except IndexError:
                syn = None
            try:
                ant = get_raw_text(sense.getElementsByTagName('ant')[0])
            except IndexError:
                ant = None
            senses.append({'mc': mc, 'syn': syn, 'ant': ant})
        entries.append({'hw': hw, 'fl': fl, 'senses': senses})
    return entries


def get_word_entries(word):
    """
    Returns:
        [{entry}, {entry}, ]
    """
    word_xml = query_word_xml(word)
    entries = parse_word_xml(word_xml)
    return entries


def get_words_entries(words):
    """
    Returns:
        {'word': [entries]}
    """
    entry_map = {}
    for word in words:
        entry_map[word] = {'detail': get_word_entries(word)}
    return entry_map


def get_exists_words_from_file(outputfile):
    """
    space is acceptable, characters before the frist tab is recognized as a word

    Returns:
        (exists words) the_word:art_of_speech
    """
    result = []
    try:
        with open(outputfile, 'r') as f:
            line = f.readline()
            while line:
                fields = re.split(r'\t', line.strip())
                word_key = "%s:%s" % (fields[0], fields[1])
                result.append(word_key)
                line=f.readline()
    except IOError:
        return []
    result = set(result)
    return result


def append_entries_to_file(entries, target_file, style=''):
    if not os.path.exists(target_file):
        open(target_file, 'w').close()
    with open(target_file, 'a') as f:
        for i in entries:
            try:
                senses = ''
                if style.startswith('verbose'):
                    senses = "\t".join(["%i %s(%s)<%s>" % (index + 1,
                        j.get('mc'), j.get('syn') or '', j.get('ant') or '') for index, j in enumerate(i.get('senses'))])
                elif style.startswith('pithy'):
                    senses = "\t".join(["%i %s" % (index + 1,
                        j.get('mc')) for index, j in enumerate(i.get('senses'))])
                else:
                    columns = []
                    syncs = []
                    ants = []
                    for index, j in enumerate(i.get('senses')):
                        columns.append("%i %s" % (index + 1, j.get('mc')))
                        syncs.append(j.get('syn') or '')
                        ants.append(j.get('ant') or '')
                    columns.extend(["(%s)" % " ".join(syncs), "<%s>" % " ".join(ants)])
                    senses = "\t".join(columns)
            except TypeError as e:
                print e, i, i.get('senses')
                raise
            line = "%s\t%s\t%s\n" % (i.get('hw'), i.get('fl'), senses)
            if isinstance(line, unicode):
                line = line.encode('utf8')
            f.write(line)




def append_words_from_folder(words_folder, outputfile):
    need_query_words = wordlib.get_difference_words(existed_file=outputfile, wordfolder=words_folder)
    print "THESE WORDS SHOULD BE ADDED:", need_query_words
    need_append_entries = []
    for index, i in enumerate(need_query_words):
        need_append_entries.extend(get_word_entries(i))
        if index % 5 == 0:
            print 'appending: %s' % list(need_query_words)[index - 5 + 1: index + 1]
            append_entries_to_file(need_append_entries, outputfile)
            append_entries_to_file(need_append_entries, outputfile + ".verbose", style='verbose')
            append_entries_to_file(need_append_entries, outputfile + ".pithy", style='pithy')
            need_append_entries = []
    append_entries_to_file(need_append_entries, outputfile)
    append_entries_to_file(need_append_entries, outputfile + ".verbose", style='verbose')
    append_entries_to_file(need_append_entries, outputfile + ".pithy", style='pithy')


def _main(argv):
    parser = argparse.ArgumentParser(description='auto crawler for merriam-webster')
    parser.add_argument('-f', '--folder', help='words list file need to be checked in the dictionary', default='words')
    parser.add_argument('-o', '--output', help='output file', default='verbal_words.csv')
    args = parser.parse_args()
    print args
    append_words_from_folder(args.folder, args.output)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
