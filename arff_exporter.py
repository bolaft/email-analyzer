#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    cross_validator.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 13, 2014 (creation)

:Description:
    K-fold cross-validator for tagged emails as outputted by the LINA email-analyser project
    (see https://github.com/bolaft/email-analyser)
"""

from text.blob import TextBlob
from arff_writer import wordstotal as wt

import arff_writer
import math
import sys
import codecs
import subprocess
import os

# Constants

TEMP_FOLDER = "tmp/"
DATA_FOLDER = "data/"

PATTERN_FILE = "patterns"

MIN_TF_IDF = 0.4
K = 3

# Main
def main(argv):
    if len(argv) != 0:
        print("This script takes no argument")
        sys.exit()

    clear_temp_folder()

    features = [
        ("position", "integer"),
        ("number_of_tokens", "integer"),
        ("number_of_characters", "integer"),
        ("number_of_quote_symbols", "integer"),
        ("average_token_length", "real"),
        ("proportion_of_uppercase", "real"),
        ("proportion_of_alphabetic_characters", "real"),
        ("proportion_of_numeric_characters", "real")
    ]

    data_sets = build_data_set(load_data(DATA_FOLDER))

    write_arff(data_sets, features, TEMP_FOLDER + "dataset.arff")

    # for train, test in generate_k_pairs(load_data(DATA_FOLDER), K):
    #     train_file = TEMP_FOLDER + str(i) + ".train.arff"
    #     test_file = TEMP_FOLDER + str(i) + ".test.arff"
    #     gold_file = TEMP_FOLDER + str(i) + ".gold.arff"

    #     print "exporting " + train_file + "..."
    #     write_arff(build_data_set(train), features, train_file)
    #     print "exporting " + test_file + "..."
    #     write_arff(build_data_set(test), features, test_file, True)
    #     print "exporting " + gold_file + "..."
    #     write_arff(build_data_set(test), features, test_file)

    #     # train_and_label(train_file, test_file)
    #     i += 1


# Finds, filters and computes features
def compute_tf_idf_features(data):
    # computes TF
    tfs = [arff_writer.tf(tokens) for tokens, label in data]
 
    # computes TF-IDF
    tfs_idfs = [arff_writer.idf(atf, len(data)) for atf in tfs]
 
    global wt
    
    # filters features on TF-IDF threshold
    tfs_idfs = arff_writer.filterOnLowTf(tfs_idfs, 0.4)
 
    labels = [label for tokens, label in data]

    return zip(tfs_idfs, labels)


# Builds data sets
def build_data_set(data):
    data_set = []

    for tokens, label, line_number in data:
        sentence = " ".join(tokens)

        data_set.append(([
            line_number, # position
            len(tokens), # number_of_tokens
            len(sentence), # number_of_characters
            sentence.count(">"), # number_of_quote_symbols
            sum(map(len, tokens)) / float(len(tokens)), # average_token_length
            sum(x.isupper() for x in sentence) / len(sentence), # proportion_of_uppercase_characters
            sum(x.isalpha() for x in sentence) / len(sentence), # proportion_of_alphabetic_characters
            sum(x.isnumeric() for x in sentence) / len(sentence) # proportion_of_numeric_characters
        ], label))

    return data_set


# Writes arff files
def write_arff(data, features, filename, test=False): 
    with codecs.open(filename, "w", "utf-8") as out:
        # writes header
        out.write("@relation " + filename.replace(".arff", "").replace(".", "-") + "\n\n")

        for feature, feature_type in features:
            out.write("@attribute " + feature + " " + feature_type + "\n")

        out.write("@attribute class {")
        out.write(",".join(set([label for values, label in data])))
        out.write("}\n\n")
 
        # writes data
        out.write("@data\n")

        for values, label in data:
            for i, value in enumerate(values):
                out.write(str(value))
                if not i == len(values) - 1:
                    out.write(",")
            if not test:
                out.write("," + label + "\n")
            else:
                out.write("\n")


# Loads data from tagged email files
def load_data(folder):
    data = []
    for filename in os.listdir(folder):
        for i, line in enumerate(tuple(codecs.open(folder + filename, "r", "UTF-8"))):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)
                    if (label in ["B", "I", "E", "BE"]):
                        data.append((tokens, label, i))
    return data


# Generates K (train, test) pairs from the items in data.
def generate_k_pairs(data, K,):
    for k in xrange(K):
        train = [x for i, x in enumerate(data) if i % K != k]
        test = [x for i, x in enumerate(data) if i % K == k]

        yield train, test


# Trains a model on the training file and apply it on the test file to generate a result file
def train_and_label(train_file, test_file):
    model_file = train_file.replace("train", "model")
    result_file = test_file.replace("test", "result")

    print("wapiti train -a rprop -p " + PATTERN_FILE + " " + train_file + " " + model_file)
    # training model
    subprocess.call("wapiti train -a rprop -p " + PATTERN_FILE + " " + train_file + " " + model_file, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

    print("wapiti label -m " + model_file + " -p " + test_file + " " + result_file)
    # applying model on test data
    subprocess.call("wapiti label -m " + model_file + " -p " + test_file + " " + result_file, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)


# Writes data to file
def write_arff_file(data, filepath, test = False):
    with codecs.open(filepath, "w") as data_file:
        data_file.write("")
        
        for blob, features, label in data:

            for i, feature in enumerate(features):
                data_file.write(str(features[feature]))

                if i != len(features) - 1:
                    data_file.write("\t")

            if not test:
                data_file.write("\t" + label)

            data_file.write("\n")


# Deletes all files in the temp folder
def clear_temp_folder():
    for filename in os.listdir(TEMP_FOLDER):
        filepath = os.path.join(TEMP_FOLDER, filename)
        try:
            if os.path.isfile(filepath):
                os.unlink(filepath)
        except Exception, e:
            print e


# Finds the best words to use as feature with TF-IDF
def find_best_features(min_tf_idf):
    blob_list = []
    words = set([])
    n_containing = {}
    labels = {}

    # here we read each tagged email file 
    for filename in os.listdir(DATA_FOLDER):
        for line in tuple(codecs.open(DATA_FOLDER + filename, "r", "UTF-8")):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 0:
                    label = tokens.pop(0)
                    tokens = [x.lower() for x in tokens]
                    blob = TextBlob(" ".join(tokens))
                    labels[blob] = label
                    for word in set(blob.words):
                        if not word in n_containing:
                            n_containing[word] = 1
                        else:
                            n_containing[word] += 1

                    words.update(blob.words)
                    blob_list.append(blob)

    idfs = {}
    for word in words:
        idfs[word] = compute_idf(word, blob_list, n_containing)

    scores = compute_scores(blob_list, idfs, min_tf_idf)

    return [(blob, scores[blob], labels[blob]) for blob in scores]


# Compute scores for each word in each blob with TF-IDF weighting
def compute_scores(blob_list, idfs, min_tf_idf):
    scores = {}
    features = set([])
    
    for blob in blob_list:
        scores[blob] = {}
        for word in blob.words:
            tf_idf = compute_tf_idf(word, blob, idfs[word])
            if tf_idf > min_tf_idf:
                scores[blob][word] = tf_idf
                features.update([word])
    
    for blob in blob_list:
        for feature in features:
            if not feature in scores[blob]:
                scores[blob][feature] = 0

    return scores

# Computes TF
def compute_tf(word, blob):
    return blob.words.count(word) / len(blob.words)

# Computes IDF
def compute_idf(word, blob_list, n_containing):
    return math.log(len(blob_list) / n_containing[word])

# Computes TF-IDF
def compute_tf_idf(word, blob, idf):
    return compute_tf(word, blob) * idf

# Launch
if __name__ == "__main__":
    main(sys.argv[1:])
