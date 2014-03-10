#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    sequence_labeller.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 27, 2014 (creation)

:Description:
    converts tokens extracted from tagged emails into wapiti datafiles, then trains, labels and evaluates
    (see https://github.com/bolaft/email-analyzer)
"""

from progressbar import ProgressBar
from nltk.stem.wordnet import WordNetLemmatizer

import nltk
import sys
import codecs
import os
import subprocess


# Wapiti
WAPITI_TRAIN_FILE = "var/train"
WAPITI_TEST_FILE = "var/test"
WAPITI_GOLD_FILE = "var/gold"
WAPITI_RESULT_FILE = "var/result"
WAPITI_MODEL_FILE = "var/model"
WAPITI_PATTERN_FILE = "var/patterns"

# Mallet
MALLET_DATA_FOLDER = "var/mallet/"

# Constants
limit = 1000

train_limit = int(limit * 0.9)

avg = {
    "position": 0,
    "number_of_tokens": 0,
    "number_of_characters": 0,
    "number_of_quote_symbols": 0,
    "average_token_length": 0,
    "proportion_of_uppercase_characters": 0,
    "proportion_of_alphabetic_characters": 0,
    "proportion_of_numeric_characters": 0
}

instances = 0

# Main
def main(argv):
    source_folder = process_argv(argv)

    print("Converting %s to wapiti datafiles..." % source_folder)
    # make_patterns()
    make_datafiles(source_folder, filter_i=True)

    # print("Training model...")
    # subprocess.call("wapiti train -p " + WAPITI_PATTERN_FILE + " " + WAPITI_TRAIN_FILE + " " + WAPITI_MODEL_FILE, shell=True)

    # print("Applying model on test data...")
    # subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p " + WAPITI_TEST_FILE + " " + WAPITI_RESULT_FILE, shell=True)

    # print("Checking...")
    # subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p -c " + WAPITI_GOLD_FILE, shell=True)


# Writes wapiti datafiles
def make_datafiles(source_folder, filter_i=False):
    print("Making datafiles...")

    train = True

    progress = ProgressBar(maxval=limit).start()

    wnl = WordNetLemmatizer()

    with codecs.open(WAPITI_TRAIN_FILE, "w", "utf-8") as train_out:
        with codecs.open(WAPITI_TEST_FILE, "w", "utf-8") as test_out:
            with codecs.open(WAPITI_GOLD_FILE, "w", "utf-8") as gold_out:
                prev_label = None

                for i, filename in enumerate(os.listdir(source_folder)):
                    progress.update(i)
                    if i == limit:
                        break
                    if i == train_limit:
                        train = False

                    lines = tuple(codecs.open(source_folder + filename, "r", "utf-8"))

                    for line_number, line in enumerate(lines):
                        line = line.strip()

                        if not line.startswith("#"):
                            tokens = line.split()
                            if len(tokens) > 1:
                                label = tokens.pop(0)

                                label = "T" if label == "B" or label == "BE" else "F"

                                for i_token, (token, tag) in enumerate(nltk.pos_tag(tokens)):
                                    # token_label = label if i_token == (len(tokens) - 1) else "F"
                                    pos = "v" if tag.startswith("V") else "n"
                                    obs = wnl.lemmatize(token.lower(), pos) + " " + tag + "\t" + label + "\n"

                                    if train:
                                        if label == prev_label:
                                            continue
                                        train_out.write(obs)
                                    else:
                                        test_out.write(obs)
                                        gold_out.write(obs)
                                        
                                prev_label = label

                    if train:
                        train_out.write("\n")
                    else:
                        test_out.write("\n")
                        gold_out.write("\n")

    progress.finish()
    make_patterns()


# Computes and writes patterns
def make_patterns():
    print("Making patterns...")

    with codecs.open(WAPITI_PATTERN_FILE, "w", "utf-8") as out:

        i = 1
        for off in xrange(-15, 16):
            # uni pos
            out.write("*" + str(i) + "_unipos:%x[" + str(off) + ",1]\n")
            i += 1

            # bi pos
            out.write("*" + str(i) + "_bipos:%x[" + str(off) + ",1]/%x[" + str(off + 1) + ",1]\n")
            i += 1

            # tri pos
            out.write("*" + str(i) + "_tripos:%x[" + str(off) + ",1]/%x[" + str(off + 1) + ",1]/%x[" + str(off + 2) + ",1]\n")
            i += 1

            # unigrams
            out.write("*" + str(i) + "_unigram:%x[" + str(off) + ",0]\n")
            i += 1

            # bigrams
            out.write("*" + str(i) + "_bigram:%x[" + str(off) + ",0]/%x[" + str(off + 1) + ",0]\n")
            i += 1

            # trigrams
            out.write("*" + str(i) + "_trigram:%x[" + str(off) + ",0]/%x[" + str(off + 1) + ",0]/%x[" + str(off + 2) + ",0]\n")
            i += 1

            out.write("\n")


# Process argv
def process_argv(argv):
    if len(argv) != 2:
        print("Usage: " + argv[0] + " <source folder>")
        sys.exit()

    # adding a "/" to the dirpath if not present
    source_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

    if not os.path.isdir(source_folder):
        sys.exit(source_folder + " is not a directory")

    return source_folder


# Launch
if __name__ == "__main__":
    main(sys.argv)
