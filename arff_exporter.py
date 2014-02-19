#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
:Name:
    dataset_builder.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 13, 2014 (creation)

:Description:
    Extract features from tagged emails as outputted by the LINA email-analyzer project and converts them into valid Weka datasets (.arff files)
    (see https://github.com/bolaft/email-analyzer)
"""

from text.blob import TextBlob
from progressbar import ProgressBar

import math
import sys
import codecs
import os
import hashlib
import re
import time


# Constants

visual_feature_list = [
    ("position", "integer"),
    ("number_of_tokens", "integer"),
    ("number_of_characters", "integer"),
    ("number_of_quote_symbols", "integer"),
    ("average_token_length", "real"),
    ("proportion_of_uppercase_characters", "real"),
    ("proportion_of_alphabetic_characters", "real"),
    ("proportion_of_numeric_characters", "real")
]

# Main
def main(argv):
    data_folder, ngram_file, arff_file = process_argv(argv)

    # dataset structure:
    # 
    # {"7aa6b6e69f16a93101bc51832f331b1f": {
    #   "features": {
    #       "abc": 0.156, "xyz": "FALSE"...
    #   }, "label": "BE" }, ... }}
    
    dataset = {} 

    # feature_list structure:
    # 
    # [("abc", "real"), ("xyz", "{TRUE, FALSE}"), ...]

    feature_list = [] + visual_feature_list

    # data structure:
    # 
    # [("B", ["token", "tnkoe", "ekotn", ...], 1), ...]

    data = load_data(data_folder)

    # features structure:
    # 
    # {"abc": 0.156, "xyz": "FALSE"...}

    features = {}

    # building dataset
    
    print("selecting features...")

    blobs = [] # list of all text blob (one per sentence)
    ngrams = set([]) # set of all distinct ngrams in corpus
    n_containing = {} # for each word, number of documents containing it

    progress = ProgressBar(maxval=len(data)*2).start()

    ################################################################################
    
    for i, (tokens, label, line_number) in enumerate(data):
        sentence = " ".join(tokens)

        # building visual features

        features.update(build_visual_features(dict(visual_feature_list), sentence, tokens, line_number))

        # preprocessing for ngram features

        blob = TextBlob(sentence)
        blob_ngrams = tokens + extract_bigrams(blob)

        for ngram in set(blob_ngrams):
            if not ngram in n_containing:
                n_containing[ngram] = 1
            else:
                n_containing[ngram] += 1

        ngrams.update(blob_ngrams)
        blobs.append(blob)

        sid = make_sid(blob)

        dataset[sid] = {}
        dataset[sid]["label"] = label
        dataset[sid]["features"] = features

        progress.update(i)

    #################################################################################
    
    nb = len(ngrams) / 100
    threshold = 0
    best_scores = []
    best_ngrams = []

    for i, blob in enumerate(blobs):
        sid = make_sid(blob)

        for ngram in tokens + extract_bigrams(blob):
            tf = float(" ".join(blob.tokens).count(ngram)) / len(blob.tokens)
            idf = math.log(len(blobs) / n_containing[ngram])
            tf_idf = tf * idf

            if (len(best_scores) < nb or tf_idf >= threshold) and ngram not in best_ngrams:
                best_ngrams.append(ngram)
                best_scores.append((ngram, tf_idf))
                best_scores = sorted(best_scores, key=lambda x: x[1], reverse=True)

                if len(best_scores) >= nb:
                    popped_ngram, popped_score = best_scores.pop()
                    best_ngrams.remove(popped_ngram)

                best_ngram, threshold = best_scores[0]

                dataset[sid]["features"][ngram] = tf_idf

        progress.update(i + len(data))
    
    for ngram, tf_idf in best_scores:
        feature_list.append((ngram, "real"))

    #################################################################################

    progress.finish()

    # writing arff file
    
    print("compiling and exporting data to " + arff_file + "...")

    write_arff(dataset, set(feature_list), arff_file)

    print("export successful")


# Makes sentence id from blob
def make_sid(blob):
    return hashlib.md5(" ".join(blob.tokens)).hexdigest()


# Extracts bigrams from a blob
def extract_bigrams(blob):
    l = [x + " " + y for x, y in zip(blob.tokens, blob.tokens[1:])]
    return [x.encode("utf-8") for x in l]


# Builds visual features
def build_visual_features(visual_feature_list, sentence, tokens, line_number):
    values = {}

    if "position" in visual_feature_list:
        values["position"] = line_number
    if "number_of_tokens" in visual_feature_list:
        values["number_of_tokens"] = len(tokens)
    if "number_of_characters" in visual_feature_list:
        values["number_of_characters"] = len(sentence)
    if "number_of_quote_symbols" in visual_feature_list:
        values["number_of_quote_symbols"] = sentence.count(">")
    if "average_token_length" in visual_feature_list:
        values["average_token_length"] = sum(map(len, tokens)) / float(len(tokens))
    if "proportion_of_uppercase_characters" in visual_feature_list:
        values["proportion_of_uppercase_characters"] = sum(x.isupper() for x in sentence) / len(sentence)
    if "proportion_of_alphabetic_characters" in visual_feature_list:
        values["proportion_of_alphabetic_characters"] = sum(x.isalpha() for x in sentence) / len(sentence)
    if "proportion_of_numeric_characters" in visual_feature_list:
        values["proportion_of_numeric_characters"] = sum(x.isdigit() for x in sentence) / len(sentence)

    return values
        

# Writes arff files
def write_arff(dataset, feature_list, filename, test=False):
    with codecs.open(filename, "w", "UTF-8") as out:
        # writes header
        out.write("@relation " + filename.replace(".arff", "").replace(".", "-") + "\n\n")

        for i, (feature, feature_type) in enumerate(feature_list):
            attribute_name = feature if (feature, feature_type) in visual_feature_list else "ngram_" + str(i)
            out.write("@attribute " + attribute_name + " " + feature_type + "\n")

        out.write("@attribute class {")
        out.write(",".join(set([dataset[sid]["label"] for sid in dataset])))
        out.write("}\n\n")

        # writes data
        out.write("@data\n")

        progress = ProgressBar()

        for sid in progress(dataset):
            for i, (feature, feature_type) in enumerate(feature_list):
                out.write(str(dataset[sid]["features"][feature]))

                if not i == len(feature_list) - 1:
                    out.write(",")

            if not test:
                out.write("," + dataset[sid]["label"])

            out.write("\n")


# Replaces special chars from a string
def replace_special_chars(str, replace):
    return re.sub("[^0-9a-zA-Z]+", replace, str)


# Loads data from tagged email files
def load_data(folder):
    data = []

    print("loading data from " + folder + "...")

    progress = ProgressBar()

    for filename in progress(os.listdir(folder)):
        for i, line in enumerate(tuple(codecs.open(folder + filename, "r"))):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)
                    data.append((tokens, label, i))

    return data

# Process argv
def process_argv(argv):
    if len(argv) != 4:
        print("Usage: " + argv[0] + " <data folder> <ngram file> <arff file>")
        sys.exit()

    # adding a "/" to the dirpath if not present
    data_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

    ngram_file = argv[2]

    # adding a .arff extension if it was not specified
    arff_file = argv[3] + ".arff" if not argv[3].endswith(".arff") else argv[3]

    if not os.path.isdir(data_folder):
        sys.exit(data_folder + " is not a directory")

    if not os.path.isfile(ngram_file):
        sys.exit(ngram_file + " is not a file")

    if not os.access(os.path.dirname(arff_file), os.W_OK) or os.path.isdir(arff_file):
        sys.exit(arff_file + " is not writable as a file")

    return data_folder, ngram_file, arff_file

# Launch
if __name__ == "__main__":
    main(sys.argv)
