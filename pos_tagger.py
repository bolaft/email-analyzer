#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
:Name:
    pos_tagger.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 26, 2014 (creation)

:Description:
    POS tags and lemmatize tokens extracted from tagged emails as outputted by the LINA email-analyzer project
    (see https://github.com/bolaft/email-analyzer)
"""

from text.blob import TextBlob
from progressbar import ProgressBar

from nltk.stem.wordnet import WordNetLemmatizer

import nltk
import sys
import codecs
import os
import hashlib


# Main
def main(argv):
    data_folder, tag_file = process_argv(argv)

    print("tagging data from " + data_folder + "...")

    progress = ProgressBar()

    with codecs.open(tag_file, "w", "UTF-8") as out:
        wnl = WordNetLemmatizer()

        for filename in progress(os.listdir(data_folder)):
            # prev_label = None
            for i, line in enumerate(tuple(codecs.open(data_folder + filename, "r"))):
                line = line.strip()
                if not line.startswith("#"):
                    tokens = line.split()
                    if len(tokens) > 1:
                        label = tokens.pop(0)
                        out.write(make_sid(TextBlob(" ".join(tokens))))
                        out.write(label)

                        for token, tag in nltk.pos_tag(tokens):
                            out.write("\t")
                            out.write(wnl.lemmatize(token) + "_" + tag)
                            out.write("\t")


# Makes sentence id from blob
def make_sid(blob):
    return hashlib.md5(" ".join(blob.tokens)).hexdigest()


# Process argv
def process_argv(argv):
    if len(argv) != 3:
        print("Usage: " + argv[0] + " <data folder> <tag file>")
        sys.exit()

    # adding a "/" to the dirpath if not present
    data_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

    tag_file = argv[2]

    if not os.path.isdir(data_folder):
        sys.exit(data_folder + " is not a directory")

    if not os.access(os.path.dirname(tag_file), os.W_OK) or os.path.isdir(tag_file):
        sys.exit(tag_file + " is not writable as a file")

    return data_folder, tag_file


# Launch
if __name__ == "__main__":
    main(sys.argv)
