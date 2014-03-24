#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    bc3_parser.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    march 24, 2014 (creation)

:Description:
    converts annotated data from the BC3 email corpus to annotated text files
    (see https://github.com/bolaft/email-analyzer)
"""

import codecs

from nltk import wordpunct_tokenize
from xml.etree import ElementTree


BC3_CORPUS_FILE = "data/corpus/bc3/corpus.xml"
BC3_ANNOTATION_FILE = "data/corpus/bc3/annotation.xml"

BC3_TAGGED_FILE = "data/bc3/bc3_tagged"
BC3_LABELLED_FILE = "data/bc3/bc3_labelled"


# Parses the BC3 corpus and annotation files and converts them to test gold files
def parse_bc3():
    annotators = []

    for i in xrange(1, 14):
        for j in xrange(1, 3):
            annotators.append("Annotator{0}-Part{1}".format(i, j))

    corpus_root = ElementTree.parse(BC3_CORPUS_FILE).getroot()
    annotation_root = ElementTree.parse(BC3_ANNOTATION_FILE).getroot()

    with codecs.open(BC3_TAGGED_FILE, "w") as tout:
        with codecs.open(BC3_LABELLED_FILE, "w") as lout:
            for thread in corpus_root:
                tid = thread.find("listno").text # thread id

                for m in thread.findall("DOC"):
                    prev_tag = None

                    for s in m.find("Text"):
                        sid = s.attrib["id"] # sentence id

                        tokens = wordpunct_tokenize(s.text)
                        tag = find_tag(annotation_root, tid, sid)

                        tout.write("{0}\t{1}\n".format("T" if tag != prev_tag else "F", " ".join(tokens)))
                        lout.write("{0}\t{1}\t{2}\n".format("T" if tag != prev_tag else "F", tag, " ".join(tokens)))

                        prev_tag = tag

                    tout.write("\n")
                    lout.write("\n")


# Finds a tag for a sentence in the BC3 annotation xml file
def find_tag(root, tid, sid):
    for thread in root:
        if thread.find("listno").text == tid:
            for label in thread.find("annotation").find("labels"):
                if sid == label.attrib["id"]:
                    return label.tag

    return "none"


# Launch
if __name__ == "__main__":
    parse_bc3()