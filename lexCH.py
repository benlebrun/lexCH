#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: University of Zürich
# Author: Laura Mascarell <mascarell@cl.uzh.ch>
# For licensing information, see LICENSE

import pprint
import operator
from collections import defaultdict
import argparse
import sys
import codecs 
import cPickle
from lxml import etree
import string
import sensegram
import ConfigParser


class Node:
    """Node is an element of the lexical chain"""
    
    def __init__(self, idN, sent, word_num, word):
        self.idN = idN
        self.sent = sent
        self.word_num = word_num
        self.word = word
        self.oriWord = None
        self.trans = []
        self.chain = None
        self.rel = []

    def printNode(self):
        if self.oriWord:
            print self.oriWord,
        else:
            print self.word,
        
        print self.idN, "relates to", self.rel, "trans", self.trans

        
class Chain:
    """Chain is a list of Nodes"""

    def __init__(self, idC, firstNode):
        self.idC = idC
        self.chain = [firstNode]

    def add(self, n):
        n.chain = self.idC
        self.chain.append(n)

    def getLastNode(self):
        return self.chain[-1]

    def delete(self):
        self.idC = None
        self.chain = []

    def getWordRelInChain(self, word):
        for n in self.chain:
            if n.oriWord == word:
               rels = [ r.split("-")[0] for r in n.rel ]
               return rels
        return []

    def mergeChains(self, chain2):
        # copy elements from chain2
        for n in chain2.chain:
            n.chain = self.idC
            self.add(n)

    def getMaxIdN(self):
        max_idN = 0
        for n in self.chain:
            if n.idN > max_idN: 
                max_idN = n.idN
        return max_idN+1
        
    def transitivity(self):
        vec = [None]*self.getMaxIdN()
        for n in self.chain:
            vec[n.idN] = n

        for n in vec:
            if n != None:
                trans=[r2 for r in n.rel for r2 in vec[int(r.split("-")[-1])].rel if r2 not in n.rel]
                n.trans = trans
                
    def printChain(self):
        print "Chain", self.idC
        for n in self.chain:
            print "\t", 
            n.printNode(),
        print

    def printPoints(self):
        res = []
        for n in self.chain:
            word = n.word
            if n.oriWord:
                word = n.oriWord
            for r in n.rel:
                res.append("(\""+word+"-"+str(n.idN)+"\", \""+r+"\")")
        return res



def restricted_float(x):
    x = float(x)
    if x < 0.0 or x > 1.0:
        raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]"%(x,))
    return x

def parse_command_line():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="get lexical chains")
    
    parser.add_argument(
        '--input', '-i', type=argparse.FileType('r'), required=True,
        metavar='PATH',
        help='Original input xml file used to obtain the senses');

    parser.add_argument(
        '--senses', '-s', type=argparse.FileType('r'), required=True,
        metavar='PATH',
        help='xml file with sense annotations obtained from get_senses.py');

    parser.add_argument(
        '--out', '-o', type=argparse.FileType('w'), required=True,
        metavar='PATH',
        help='Output xml file with the resulting lexical chains annotations')

    parser.add_argument(
        '--simt', '-st', type=restricted_float,
        metavar='[0.0-1.0]', default=0.85,
        help='Similarity threshold to detect words as semantically similar (default is 0.85)')

    return parser.parse_args()

        
def addToSpan(span, nodes):
    if len(span) == 5:
        span.pop(0)
    span.append(nodes)

    
def similarity(w1, w2, model):
    if w1.lower() in model.vocab and w2.lower() in model.vocab:
        sim = model.similarity(w1.lower(), w2.lower())
        return sim
    return 0

def isInChain(cand, span, model, snt_num, all_chains):
    chains = {}
    ini_rel = []

    for snt in span:
        snt_words = [n for n in snt if n.word.lower() in model.vocab]
        for n in snt_words:
            if n.idN < cand.idN:
                sim = similarity(cand.word, n.word, model)
                if sim >= args.simt:
                    chains[n.idN] = {}
                    chains[n.idN]["node"] = n
                    chains[n.idN]["chains"] = n.chain
    return chains

def minChainId(nChains):
    m_id = None
            
    for nC in nChains:
        cId = nChains[nC]["chains"]
        if cId != None and (cId < m_id or m_id == None):
            m_id = cId

    return m_id

def updChains(chains, nChains, cand, final_nodes):
    seen = []
    m_id = minChainId(nChains)

    # create a chain with the first and candidate.
    rel_word = cand.word
    if cand.oriWord:
        rel_word = cand.oriWord
    if m_id == None:
        m_id = len(chains)
        first_k, first_v = nChains.popitem()
        n1 = first_v["node"]
        n1.rel.append(rel_word+"-"+str(cand.idN))
        n1.chain = m_id
        chains.append(Chain(m_id, n1))
        final_nodes.append(n1)

    last = None
    
    for nC in nChains:
        # merge chains
        cId = nChains[nC]["chains"]
        if cId in seen: continue
        if cId == None:
            nChains[nC]["node"].rel.append(rel_word+"-"+str(cand.idN))
            chains[m_id].add(nChains[nC]["node"])
            final_nodes.append(nChains[nC]["node"])
        elif cId != m_id:
            nChains[nC]["node"].rel.append(rel_word+"-"+str(cand.idN))
            chains[m_id].mergeChains(chains[cId])
            chains[cId].delete()
            seen.append(cId)
        elif cId == m_id and (nC > last or last == None):
            last = nC

    if last:
        nChains[last]["node"].rel.append(rel_word+"-"+str(cand.idN))
    chains[m_id].add(cand)
    
        
def getRelations(node, curr_rel, last_rel_id, rels):
    out = []
    if node.idN in curr_rel:
        out += curr_rel[node.idN]

    for r in rels:
        curr_rel[int(r.split("-")[-1])].append(str(last_rel_id))
        out.append(str(last_rel_id))
        last_rel_id += 1
        
    return (last_rel_id, out)


def existsNode(nodes, idN):
    for n in nodes:
        if n.idN == idN:
            return n
        elif n.idN > idN:
            return None

    return None


def toXML(docfile, root, docid, final_nodes):   
    last_id = 0
    curr_rel = defaultdict(list)
    curr_trans = defaultdict(list)
    idW = 0
    
    doc = etree.SubElement(root, 'doc')
    doc.attrib["docid"] = docid
    
    for snt_num, snt in enumerate(docfile):
        seg = etree.SubElement(doc, 'seg')
        words = snt.rstrip().split()
        seg.attrib["segid"] = str(snt_num)

        for w_num, w in enumerate(words):
            w_tag = etree.SubElement(seg,'w')
            w_tag.text = w            
            n = existsNode(final_nodes, w_num+idW)

            if n != None:
                 last_id, n_rel = getRelations(n, curr_rel, last_id, n.rel)
                 last_id, n_trans = getRelations(n, curr_trans, last_id, n.trans)
                 w_tag.attrib["ch"] = str(n.chain)
                 if n_rel: w_tag.attrib["rel"] = ','.join(n_rel)
                 if n_trans: w_tag.attrib["tran"] = ','.join(n_trans)

        idW += len(words)
    
     
if __name__ == "__main__":
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)

    args = parse_command_line()

    config = configParser = ConfigParser.RawConfigParser()
    config.read('config_local.ini')
    stopW = set(word.strip().lower() for word in codecs.open(config.get('lexCH', 'stopw'), 'r', 'utf-8'))
    model = sensegram.SenseGram.load_word2vec_format(config.get('lexCH', 'senses'), binary=True)

    tree = etree.parse(args.senses)
    root = tree.getroot()

    srctree = etree.parse(args.input)
    srcroot = srctree.getroot()
    src_doc = next(srcroot.iter('doc'))

    out_root = etree.Element('lexical_chains')

    for d_i, doc in enumerate(root):
        print src_doc.attrib['docid']
        
        docid = doc.attrib["docid"]

        idW = 0
        chains = []
        span = []
        final_nodes = []

        src_segs = []
        src_seg = next(src_doc.iter('seg'))

        for seg in doc:
            src_segs.append(src_seg.text)

            snt_num = int(seg.attrib["segid"]) - 1
            snt = seg.text
            words = []

            if not snt is None:
                words = snt.rstrip().split()
            nodes = [Node(idW+w_num, snt_num, w_num, w) for w_num, w in enumerate(words) if not w.lower() in stopW and not w.lower() in string.punctuation]
            idW += len(words)

            addToSpan(span, nodes)
            if snt_num%5 == 0: x = snt_num

            for n in nodes:
                nChains = isInChain(n, span, model, snt_num, chains)

                # update chains
                if len(nChains) > 0:
                    updChains(chains, nChains, n, final_nodes)
                    final_nodes.append(n)
                    
            src_seg = src_seg.getnext()
        src_doc = src_doc.getnext()        

        # get transitivity links
        for c in chains:
            c.transitivity()
        
        final_nodes.sort(key=operator.attrgetter('idN'))

        toXML(src_segs, out_root, docid, final_nodes)
        
    args.out.write(etree.tostring(out_root, encoding="UTF-8", xml_declaration=True, pretty_print=True))

