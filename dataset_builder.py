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
    Extracts features from tagged emails as outputted by the LINA email-analyzer project and converts them into valid Weka datasets (.arff files)
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
import operator


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

    # reading imposed ngram list
    
    imposed_ngrams = [ngram.strip() for ngram in tuple(codecs.open(ngram_file, "r", "utf-8"))]

    imposed_ngrams_feature_list = [(ngram, "integer") for ngram in imposed_ngrams]

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

    feature_list = [] + visual_feature_list + imposed_ngrams_feature_list

    # data structure:
    # 
    # [("B", ["token", "tnkoe", "ekotn", ...], 1), ...]

    data = load_data(data_folder, 25000, filter_i=True)

    # building dataset
    
    print("preprocessing...")

    blobs = [] # list of all text blob (one per sentence)
    ngrams = set([]) # set of all distinct ngrams in corpus
    n_containing = {} # for each word, number of documents containing it

    progress = ProgressBar()

    ################################################################################
    
    for i, (tokens, label, line_number) in enumerate(progress(data)):
        features = {}
        sentence = " ".join(tokens)

        # building visual features

        features.update(build_visual_features(dict(visual_feature_list), sentence, tokens, line_number))
        
        for imposed_ngram in imposed_ngrams:
            features[imposed_ngram] = sentence.count(imposed_ngram)
            print imposed_ngram
            print features[imposed_ngram]

        # preprocessing for ngram features

        blob = TextBlob(sentence)
        blob_ngrams = blob.tokens + extract_bigrams(blob)
        blob_ngrams = [ngram.encode("utf-8") for ngram in blob_ngrams]

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

    #################################################################################
    
    print("selecting features...")

    best_scores = {}

    progress = ProgressBar()

    for i, blob in enumerate(progress(blobs)):
        sid = make_sid(blob)

        blob_ngrams = blob.tokens + extract_bigrams(blob)
        blob_ngrams = [ngram.encode("utf-8") for ngram in blob_ngrams]

        for ngram in blob_ngrams:
            tokens = [t.encode("utf-8") for t in blob.tokens]
            tf = float(" ".join(tokens).count(ngram)) / len(blob.tokens)
            idf = math.log(len(blobs) / n_containing[ngram])
            tf_idf = tf * idf

            dataset[sid]["features"][ngram] = tf_idf

            if not ngram in best_scores or best_scores[ngram] < tf_idf:
                best_scores[ngram] = tf_idf
    
    sorted_scores = sorted(best_scores.iteritems(), key=operator.itemgetter(1)) # sorting scores by order of tf_idf
    
    for ngram, best_tf_idf in sorted_scores[:len(ngrams) / 1000]: # keeping only the best 0.1%
        feature_list.append((ngram, "real"))

    #################################################################################

    # writing arff file
    
    print("compiling and exporting data to " + arff_file + "...")

    write_arff(dataset, set(feature_list), arff_file)

    print("export successful")


# Makes sentence id from blob
def make_sid(blob):
    tokens = [ngram.encode("utf-8") for ngram in blob.tokens]
    return hashlib.md5(" ".join(tokens)).hexdigest()


# Extracts bigrams from a blob
def extract_bigrams(blob):
    return [x + " " + y for x, y in zip(blob.tokens, blob.tokens[1:])]


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
        values["proportion_of_uppercase_characters"] = float(sum(x.isupper() for x in sentence)) / len(sentence)
    if "proportion_of_alphabetic_characters" in visual_feature_list:
        values["proportion_of_alphabetic_characters"] = float(sum(x.isalpha() for x in sentence)) / len(sentence)
    if "proportion_of_numeric_characters" in visual_feature_list:
        values["proportion_of_numeric_characters"] = float(sum(x.isdigit() for x in sentence)) / len(sentence)

    return values


# Writes arff files
def write_arff(dataset, feature_list, filename, test=False):
    with codecs.open(filename, "w", "utf-8") as out:
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
                out.write(str(dataset[sid]["features"][feature]) if feature in dataset[sid]["features"] else "0.0")

                if not i == len(feature_list) - 1:
                    out.write(",")

            if not test:
                out.write("," + dataset[sid]["label"])

            out.write("\n")


# Replaces special chars from a string
def replace_special_chars(str, replace):
    return re.sub("[^0-9a-zA-Z]+", replace, str)


# Loads data from tagged email files
def load_data(folder, max_lines, filter_i=False):
    data = []

    print("loading data from " + folder + "...")

    progress = ProgressBar(maxval=max_lines).start()

    ln = 0

    prev_bool_val = prev_label = None

    for filename in os.listdir(folder):
        for i, line in enumerate(tuple(codecs.open(folder + filename, "r", "utf-8"))):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)

                    bool_val = "T" if label == "B" or label == "BE" else "F"

                    if prev_bool_val == bool_val:
                        continue

                    # if not filter_i or label != "I" or prev_label != "I": # filters out consecutive "I" labelled sentences
                    data.append((tokens, bool_val, i))
                    
                    prev_bool_val = bool_val
                    # prev_label = label
                    
                    ln += 1
                    if ln < max_lines:
                        progress.update(ln)
            
        if ln > max_lines:
            break

    progress.finish()

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
