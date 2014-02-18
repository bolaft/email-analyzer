#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    ngram_selector.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 18, 2014 (creation)

:Description:
    Selects the most interesting ngrams from tagged emails as outputted by the LINA email-analyzer project
    (see https://github.com/bolaft/email-analyzer)
"""

import nltk
import sys
import codecs
import os

from nltk.collocations import *

# Main
def main(argv):
    ######################## ARGS ########################
    
    if len(argv) != 4:
        print("Usage: " + argv[0] + " <data folder> <target file> <desired number of ngrams>")
        sys.exit()

    # adding a "/" to the dirpath if not present
    data_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

    target_file = argv[2]

    if not os.path.isdir(data_folder):
        sys.exit(data_folder + " is not a directory")

    if not os.access(os.path.dirname(target_file), os.W_OK):
        sys.exit(target_file + " is not accessible")

    try:
        n = int(argv[3])
    except:
        sys.exit(argv[3] + " is not an integer")

    ####################### FILTER #######################

    print("loading data from " + data_folder + "...")

    data = load_data(data_folder)

    print("finding best ngrams")

    best_ngrams = find_nbest(data, n)

    print("writing to " + target_file + "...")

    write_ngrams(best_ngrams, target_file)

    print(str(len(best_ngrams)) + " ngrams exported")


# Write the ngrams in a file
def write_ngrams(ngrams, filename): 
    with codecs.open(filename, "w", "UTF-8") as out:
        for ngram in ngrams:
            out.write(" ".join(ngram) + "\n")


# Uses collocations to find best bigrams and trigrams for each class
def find_nbest(data, n):
    nbest = []
    nb = n / len(data) / 2 # number of ngram for each class and each size (bi or tri)

    bigram_measures = nltk.collocations.BigramAssocMeasures()
    trigram_measures = nltk.collocations.TrigramAssocMeasures()

    for label in data:
        tokens = data[label]

        bigram_finder = BigramCollocationFinder.from_words(tokens)
        trigram_finder = TrigramCollocationFinder.from_words(tokens)

        nbest += bigram_finder.nbest(bigram_measures.pmi, nb) + trigram_finder.nbest(trigram_measures.pmi, nb)

    return nbest


# Loads data from tagged email files
def load_data(folder):
    data = {}

    for filename in os.listdir(folder):
        for line in tuple(codecs.open(folder + filename, "r")):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)
                    data[label] = tokens if not label in data else data[label] + tokens

    return data


# Launch
if __name__ == "__main__":
    main(sys.argv)
