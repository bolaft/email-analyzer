#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
:Name:
    vector_sequence_labeller.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 27, 2014 (creation)

:Description:
    converts tokens extracted from tagged emails into vector-based wapiti datafiles, then trains, labels and evaluates
    (see https://github.com/bolaft/email-analyzer)
"""

from progressbar import ProgressBar

import sys
import codecs
import os
import subprocess


# Parameters
WAPITI_TRAIN_FILE = "var/wapiti_vector_train.txt"
WAPITI_TEST_FILE = "var/wapiti_vector_test.txt"
WAPITI_GOLD_FILE = "var/wapiti_vector_gold.txt"
WAPITI_RESULT_FILE = "var/wapiti_vector_result.txt"
WAPITI_MODEL_FILE = "var/wapiti_vector_model.txt"

PATTERN_FILE = "var/vector_patterns"


# Main
def main(argv):
    source_folder = process_argv(argv)

    print("Extracting data from %s..." % source_folder)
    data, vector = extract_data(source_folder)

    print("Converting data to wapiti datafiles...")
    make_datafiles(data, vector)

    # print("Building patterns...")
    # make_patterns(vector)

    # print("Training model...")
    # subprocess.call("wapiti train -p " + PATTERN_FILE + " " + WAPITI_TRAIN_FILE + " " + WAPITI_MODEL_FILE, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

    # print("Applying model on test data...")
    # subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p " + WAPITI_TEST_FILE + " " + WAPITI_RESULT_FILE, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

    # print("Checking...")
    # subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p -c " + WAPITI_GOLD_FILE, shell=True)


def make_patterns(vector):
    with codecs.open(PATTERN_FILE, "w", "UTF-8") as out:
        progress = ProgressBar()
        i = 0
        for col in progress(xrange(0, len(vector))):
            for off in xrange(-2, 3):
                i += 1
                col = str(col)
                off = str(off) if off < 1 else "+" + str(off)

                out.write("b" + str(i) + ":%t[" + off + "," + col + ",\"^1$\"]\n")
            out.write("\n")


def make_datafiles(data, vector):
    train_limit = int(len(data) * 0.9)

    with codecs.open(WAPITI_TRAIN_FILE, "w", "UTF-8") as train_out:
        with codecs.open(WAPITI_TEST_FILE, "w", "UTF-8") as test_out:
            with codecs.open(WAPITI_GOLD_FILE, "w", "UTF-8") as gold_out:
                out = [train_out]
                progress = ProgressBar()

                for i, (ngrams, label) in enumerate(progress(data)):
                    if label == None:
                        for chan in out:
                            chan.write("\n")
                        continue

                    if i == train_limit:
                        out = [test_out, gold_out]

                    obs = ""

                    for ngram in vector:
                        if ngram in ngrams:
                            obs += "1 "
                        else:
                            obs += "0 "

                    for chan in out:
                        chan.write(obs)
                        chan.write("T\n" if label == "B" or label == "BE" else "F\n")


# Extracts data from tagged emails
def extract_data(source_folder):
    data = []
    vector = set([]) # set of all distinct ngrams in corpus

    progress = ProgressBar()

    for i, filename in enumerate(progress(os.listdir(source_folder))):
        if i == 1000:
            break
        with codecs.open(source_folder + filename, "r") as f:
            for line in f:                
                if not line.startswith("#"):
                    tokens = line.split()

                    if len(tokens) > 1:
                        label = tokens.pop(0)
                        ngrams = set(tokens + extract_bigrams(tokens))
                        vector.update(ngrams)
                        data.append((ngrams, label))

        vector = set(vector)
        data.append((None, None))

    return data, vector


# Extracts bigrams
def extract_bigrams(tokens):
    l = [x + " " + y for x, y in zip(tokens, tokens[1:])]
    return [x.encode("utf-8") for x in l]


# Process argv
def process_argv(argv):
    if len(argv) != 2:
        print("Usage: " + argv[0] + " <source folder> <target file>")
        sys.exit()

    # adding a "/" to the dirpath if not present
    source_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

    if not os.path.isdir(source_folder):
        sys.exit(source_folder + " is not a directory")

    return source_folder


# Launch
if __name__ == "__main__":
    main(sys.argv)
