#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: University of Zürich
# Author: Laura Mascarell <mascarell@cl.uzh.ch>
# For licensing information, see LICENSE

import operator
from collections import defaultdict
import argparse
import sys
from sensegram import sensegram
from sensegram import wsd
import codecs
from lxml import etree
import string
import gensim
import ConfigParser


def parse_command_line():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="get word senses using sensegram")
    
    parser.add_argument(
        '--input', '-i', type=argparse.FileType('r'), default=sys.stdin,
        metavar='PATH',
        help='Input file (default: standard input)')

    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w'), default=sys.stdout,
        metavar='PATH',
        help='Output file (default: standard output)')
    
    return parser.parse_args()


if __name__ == "__main__":
 
    sys.stderr = codecs.getwriter('UTF-8')(sys.stderr)
    sys.stout = codecs.getwriter('UTF-8')(sys.stdout)
    sys.stdin = codecs.getreader('UTF-8')(sys.stdin)
     
    config = configParser = ConfigParser.RawConfigParser()
    config.read('config.ini')
    sv = sensegram.SenseGram.load_word2vec_format(config.get('lexCH', 'senses'), binary=True)
    wv = gensim.models.KeyedVectors.load_word2vec_format(config.get('lexCH', 'words'), binary=True)
    wsd_model = wsd.WSD(sv, wv, window=5, method='sim', max_context_words=3)
    stopW = set(word.strip().lower() for word in codecs.open(config.get('lexCH', 'stopw'), 'r', 'utf-8'))

    args = parse_command_line()
    tree = etree.parse(args.input)
    root = tree.getroot()
    src = root[0]
    
    out_root = etree.Element('senses')
    #out_root.attrib["fileid"] = root.attrib['fileid'] 
    out_root.set('fileid', root.attrib['fileid']) 
        
    for d_i, doci in enumerate(src):
        doc = etree.SubElement(out_root, 'doc')
        doc.set('docid', doci.attrib["docid"])
        #doc.attrib["docid"] = doci.attrib["docid"]
        for seg in doci:
            index = 0
            snt = seg.text
            words = []
            if not snt is None:
                words = snt.rstrip().split()
            snt_senses = []
            for word in words:
                if (word.lower() in stopW) or (word.lower() in string.punctuation):
                    snt_senses.append(word)
                    index += (len(word) + +1)
                    continue
                try:
                    sense, _ = wsd_model._disambiguate(snt.lower(), word.lower(), index, index+len(word), False)
                except UnicodeEncodeError:
                    sense = None
                index += (len(word) + 1)
                if sense is None:
                    snt_senses.append(word)
                    continue
                snt_senses.append(word+"#"+sense.split("#")[1])

            out_seg = etree.SubElement(doc, 'seg')
            out_seg.text = ' '.join(snt_senses)
            #out_seg.attrib["segid"] = str(seg.attrib["segid"])
            out_seg.set('segid', str(seg.attrib["segid"]))

    args.output.write(etree.tostring(out_root, encoding="utf-8", xml_declaration=True))#, pretty_print=True))
