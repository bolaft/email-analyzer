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


# Main
def main(argv):
    data_folder, ngram_file = process_argv(argv)

    # data structure:
    # 
    # [("B", ["token", "tnkoe", "ekotn", ...], 1), ...]

    data = load_data(data_folder, 25000)
    
    print("preprocessing...")

    blobs = [] # list of all text blobs (one per sentence)
    ngrams = set([]) # set of all distinct ngrams in corpus
    n_containing = {} # for each word, number of documents containing it

    progress = ProgressBar()

    ################################################################################
    
    for label, tokens in progress(data.items()):
        sentence = " ".join(tokens)

        blob = TextBlob(sentence)
        blob_ngrams = blob.tokens
        # blob_ngrams = blob.tokens + extract_bigrams(blob)

        for ngram in set(blob_ngrams):
            if not ngram in n_containing:
                n_containing[ngram] = 1
            else:
                n_containing[ngram] += 1

        ngrams.update(blob_ngrams)
        blobs.append(blob)

    #################################################################################
    
    print("selecting features...")

    best_scores = {}
    selected_features = []

    progress = ProgressBar()

    for blob in progress(blobs):
        # for ngram in blob.tokens + extract_bigrams(blob):
        for ngram in blob.tokens:
            tf = float(" ".join(blob.tokens).count(ngram)) / len(blob.tokens)
            idf = math.log(len(blobs) / n_containing[ngram])
            tf_idf = tf * idf

            if not ngram in best_scores or best_scores[ngram] < tf_idf:
                best_scores[ngram] = tf_idf
    
    sorted_scores = sorted(best_scores.iteritems(), key=operator.itemgetter(1)) # sorting scores by order of tf_idf
    
    for ngram, best_tf_idf in sorted_scores[:len(ngrams) / 1000]: # keeping only the best 0.1%
        selected_features.append(ngram)

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


# Loads data from tagged email files
def load_data(folder, max_lines):
    data = {}

    print("loading data from " + folder + "...")

    progress = ProgressBar(maxval=max_lines).start()

    ln = 0

    for filename in os.listdir(folder):
        for i, line in enumerate(tuple(codecs.open(folder + filename, "r", "utf-8"))):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)

                    if not label in data:
                        data[label] = []

                    for token in tokens:
                        data[label].append(token)
                    
                    ln += 1
                    if ln < max_lines:
                        progress.update(ln)
            
        if ln > max_lines:
            break

    progress.finish()

    return data


# Process argv
def process_argv(argv):
    if len(argv) != 3:
        print("Usage: " + argv[0] + " <data folder> <ngram file>")
        sys.exit()

    # adding a "/" to the dirpath if not present
    data_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

    ngram_file = argv[2]

    if not os.path.isdir(data_folder):
        sys.exit(data_folder + " is not a directory")

    if not os.access(os.path.dirname(ngram_file), os.W_OK) or os.path.isdir(ngram_file):
        sys.exit(ngram_file + " is not writable as a file")

    return data_folder, ngram_file


# Launch
if __name__ == "__main__":
    main(sys.argv)
