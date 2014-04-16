#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
:Name:
    ngram_selector.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    march 4, 2014 (creation)

:Description:
    Selects useful ngram features from tagged emails as outputted by the LINA email-analyzer project (.arff files)
    (see https://github.com/bolaft/email-analyzer)
"""

from text.blob import TextBlob
from progressbar import ProgressBar

import os
import sys
import codecs
import hashlib
import math
import operator


# Parameters
ONLY_INITIAL = True # keep only the first message of each thread
ONLY_UTF8 = True # filter out payloads not encoded in utf-8
ONLY_TEXT_PLAIN = True # filter out xml and html payloads

# Paths
DATA_FOLDER = "data/email.message.tagged/"


# Main
def main(argv):
    ngram_file = process_argv(argv)

    # data structure:
    # 
    # [("B", ["token", "tnkoe", "ekotn", ...], 1), ...]

    data = load_data(7000)
    
    print("preprocessing...")

    blobs = [] # list of all text blobs (one per sentence)
    n_containing = {} # for each word, number of documents containing it

    progress = ProgressBar()

    ################################################################################
    
    for label, tokens in progress(data.items()):
        sentence = " ".join(tokens)

        blob = TextBlob(sentence)
        # blob_ngrams = blob.tokens
        # blob_ngrams = extract_bigrams(blob)
        # blob_ngrams = blob.tokens + extract_bigrams(blob)
        blob_ngrams = blob.tokens + extract_bigrams(blob) + extract_trigrams(blob)

        for ngram in set(blob_ngrams):
            ngram_lower = ngram.lower()
            if not ngram_lower in n_containing:
                n_containing[ngram_lower] = 1
            else:
                n_containing[ngram_lower] += 1

        blobs.append(blob)

    #################################################################################
    
    print("selecting features...")

    best_scores = {}
    selected_features = []

    progress = ProgressBar()

    for blob in progress(blobs):
        # for ngram in extract_bigrams(blob):
        # for ngram in blob.tokens:
        # for ngram in blob.tokens + extract_bigrams(blob):
        for ngram in blob.tokens + extract_bigrams(blob) + extract_trigrams(blob):
            ngram_lower = ngram.lower()

            # tf = float(" ".join(blob.tokens).count(ngram_lower)) / len(blob.tokens)
            tf = 1
            idf = math.log(float(len(blobs)) / n_containing[ngram_lower])
            tf_idf = tf * idf

            if not ngram_lower in best_scores or best_scores[ngram_lower] < tf_idf:
                best_scores[ngram_lower] = tf_idf
    
    sorted_scores = sorted(best_scores.iteritems(), key=operator.itemgetter(1)) # sorting scores by order of tf_idf

    for ngram_lower, best_tf_idf in sorted_scores[:1000]: # keeping only the best 100
        selected_features.append(ngram_lower)

    for ngram in selected_features:
        print("%s: %d" % (ngram, n_containing[ngram.lower()]))
    sys.exit()

    #################################################################################

    with codecs.open(ngram_file, "w", "utf-8") as out:
        for feat in selected_features:
            out.write(feat + "\n")


# Makes sentence id from blob
def make_sid(blob):
    return hashlib.md5(" ".join(blob.tokens)).hexdigest()


# Extracts bigrams from a blob
def extract_bigrams(blob):
    return [x + " " + y for x, y in zip(blob.tokens, blob.tokens[1:])]


# Extracts trigrams from a blob
def extract_trigrams(blob):
    return [x + " " + y + " " + z for x, y, z in zip(blob.tokens, blob.tokens[1:], blob.tokens[2:])]


# Loads data from tagged email files
def load_data(limit):
    data = {}

    files = []

    progress = ProgressBar()

    print("# verifying data files...")

    # iterates through files in the data folder
    for filename in progress(os.listdir(DATA_FOLDER)):
        if len(files) == limit:
            break

        # reads and splits a file into lines
        lines = codecs.open(DATA_FOLDER + filename, "r").readlines()

        for line in lines:
            # "#" prefixed lines contain metadata
            if line.startswith("#"):
                metadata = line[2:].split("\t")

                if len(metadata) == 8:
                    # message_id = metadata[0]
                    mime = metadata[1]
                    encoding = metadata[2]
                    is_initial = metadata[3]
                    # from_address = metadata[4]
                    # from_personal = metadata[5]
                    # to_address = metadata[6]
                    # to_personal = metadata[7]

                    if (is_initial != "true" and ONLY_INITIAL) or (encoding != "UTF-8" and ONLY_UTF8) or (mime != "text/plain" and ONLY_TEXT_PLAIN):
                        break

                    files.append(filename)

                    break
            else:
                break

    print("# dataset size: {0} ({1} requested)".format(len(files), limit))

    print("loading data from " + DATA_FOLDER + "...")

    progress = ProgressBar()

    for filename in progress(files):
        for i, line in enumerate(tuple(codecs.open(DATA_FOLDER + filename, "r", "utf-8"))):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)

                    if not label in data:
                        data[label] = []

                    for token in tokens:
                        data[label].append(token)

    return data


# Process argv
def process_argv(argv):
    if len(argv) != 2:
        sys.exit("Usage: " + argv[0] + " <ngram file>")

    # previxing "./" to the dirpath if not present
    ngram_file = "./" + argv[1] if not argv[1].startswith("./") and not argv[1].startswith("/") else argv[1]

    if not os.access(os.path.dirname(ngram_file), os.W_OK) or os.path.isdir(ngram_file):
        sys.exit(ngram_file + " is not writable as a file")

    return ngram_file


# Launch
if __name__ == "__main__":
    main(sys.argv)
