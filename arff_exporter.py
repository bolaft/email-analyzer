#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    arff_exporter.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 13, 2014 (creation)

:Description:
    Converts tagged emails as outputted by the LINA email-analyzer project into valid Weka datasets (.arff files)
    (see https://github.com/bolaft/email-analyzer)
"""

from text.blob import TextBlob

import math
import sys
import codecs
import os
import hashlib

# Main
def main(argv):
    ######################## ARGS ########################
    
    if len(argv) != 5:
        print("Usage: " + argv[0] + " <data folder> <ngram file> <arff file> <TF-IDF threshold>")
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

    if not os.access(os.path.dirname(arff_file), os.W_OK):
        sys.exit(arff_file + " is not accessible")

    try:
        threshold = float(argv[4])
    except:
        sys.exit(argv[4] + " is not a floating number")

    ###################### DATA SET ######################

    print("loading data from " + data_folder + "...")

    data = load_data(data_folder)

    print("building visual features...")
    visual_features, visual_features_list = build_visual_features(data)
    print("building unigram features, with TF-IDF threshold of " + str(threshold) + "...")
    unigram_features, unigram_features_list = build_unigram_features(data, threshold)
    print("building ngram features, from " + ngram_file + "...")
    ngram_features, ngram_features_list = build_ngram_features(data, ngram_file)

    features_list = visual_features_list + unigram_features_list + ngram_features_list
    
    data_set = merge_data(merge_data(visual_features, unigram_features), ngram_features)

    # for sid, feature_dic in data_set.iteritems():
    #     print sid
    #     for feature, value in feature_dic.iteritems():
    #         print "\t" + sid + " " + feature + " " + str(value)
    #     break;

    print("writing to " + arff_file + "...")

    write_arff(data_set, features_list, arff_file)

    print("export successful")
    print("total features: " + str(len(features_list)) + " (visual: " + str(len(visual_features_list)) + ", unigrams: " + str(len(unigram_features_list)) + ", ngrams: " + str(len(ngram_features_list)) + ")")


# Writes arff files
def write_arff(data, features, filename, test=False): 
    with codecs.open(filename, "w", "UTF-8") as out:
        # writes header
        out.write("@relation " + filename.replace(".arff", "").replace(".", "-") + "\n\n")

        for feature, feature_type in features:
            out.write("@attribute " + feature + " " + feature_type + "\n")

        out.write("@attribute class {")
        out.write(",".join(set([data[sid]["label"] for sid in data])))
        out.write("}\n\n")

        # writes data
        out.write("@data\n")

        for sid in data:
            for i, (feature, feature_type) in enumerate(features):
                out.write(str(data[sid][feature]))

                if not i == len(features) - 1:
                    out.write(",")

            if not test:
                out.write("," + data[sid]["label"])

            out.write("\n")


# Merges two data sets
def merge_data(base_set, added_set):
    common_ids = [sid for sid in base_set if sid in added_set]

    for sentence_id in common_ids:
        base_set[sentence_id].update(added_set[sentence_id])

    missing_ids = [sid for sid in base_set if sid not in added_set] + [sid for sid in added_set if sid not in base_set]

    if len(missing_ids) > 0:
        print "ERROR! Missing sentence ids in dataset:"
        print missing_ids

    return base_set


# Builds a data set based on visual features
def build_visual_features(data):
    features = {}

    features_list = [
        ("position", "integer"),
        ("number_of_tokens", "integer"),
        ("number_of_characters", "integer"),
        ("number_of_quote_symbols", "integer"),
        ("average_token_length", "real"),
        ("proportion_of_uppercase_characters", "real"),
        ("proportion_of_alphabetic_characters", "real"),
        ("proportion_of_numeric_characters", "real")
    ]

    for tokens, label, line_number in data:
        sentence_id = make_id_from_tokens(tokens)
        features[sentence_id] = compute_visual_features(dict(features_list), tokens, line_number)
        features[sentence_id]["label"] = label # label is included here (TODO this operation should be moved elsewhere)

    return features, features_list


# Computes visual features
def compute_visual_features(vflist, tokens, line_number):
    values = {}
    sentence = " ".join(tokens)

    if "position" in vflist:
        values["position"] = line_number
    if "number_of_tokens" in vflist:
        values["number_of_tokens"] = len(tokens)
    if "number_of_characters" in vflist:
        values["number_of_characters"] = len(sentence)
    if "number_of_quote_symbols" in vflist:
        values["number_of_quote_symbols"] = sentence.count(">")
    if "average_token_length" in vflist:
        values["average_token_length"] = sum(map(len, tokens)) / float(len(tokens))
    if "proportion_of_uppercase_characters" in vflist:
        values["proportion_of_uppercase_characters"] = sum(x.isupper() for x in sentence) / len(sentence)
    if "proportion_of_alphabetic_characters" in vflist:
        values["proportion_of_alphabetic_characters"] = sum(x.isalpha() for x in sentence) / len(sentence)
    if "proportion_of_numeric_characters" in vflist:
        values["proportion_of_numeric_characters"] = sum(x.isdigit() for x in sentence) / len(sentence)

    return values


# Builds a dataset based on unigram features
def build_unigram_features(data, threshold):
    blob_list = [] # list of all text blob (one per sentence)
    words = set([]) # set of all distinct words in corpus
    n_containing = {} # for each word, number of documents containing it
    idfs = {} # for each word, its inverse document frequency

    # computing blob_list, words and n_containing
    for tokens, label, line_number in data:
        blob = TextBlob(" ".join(tokens))

        for word in set(blob.tokens):
            n_containing[word] = 1 if not word in n_containing else n_containing[word] + 1

        words.update(blob.tokens)
        blob_list.append(blob)

    # computing idfs
    for word in words:
        idfs[word] = compute_idf(word, blob_list, n_containing)

    return compute_unigram_features(blob_list, idfs, threshold)


# Compute unigram features with TF-IDF weighting
def compute_unigram_features(blob_list, idfs, threshold):
    values = {}
    features = set([])
    
    for blob in blob_list:
        sentence_id = hashlib.md5(" ".join(blob.tokens)).hexdigest()
        values[sentence_id] = {}

        for word in blob.tokens:
            tf_idf = compute_tf_idf(word, blob, idfs[word])

            if tf_idf > threshold:
                values[sentence_id][word] = tf_idf
                features.update([word])
    
    for blob in blob_list:
        sentence_id = make_id_from_tokens(blob.tokens)

        for feature in features:
            if not feature in values[sentence_id]:
                values[sentence_id][feature] = 0

    return values, [(x, "real") for x in features]


# Builds a dataset based on the ngram list
def build_ngram_features(data, ngram_file):
    features = [line for line in tuple(codecs.open(ngram_file, "r"))]
    values = {}

    for tokens, label, line_number in data:
        sentence_id = make_id_from_tokens(tokens)
        values[sentence_id] = {}

        for i, feature in enumerate(features):
            values[sentence_id]["ngram-" + str(i)] = "TRUE" if contains(tokens, feature.split()) else "FALSE"

    return values, [("ngram-" + str(i), "{TRUE,FALSE}") for i in xrange(len(features))]


# Computes TF
def compute_tf(word, blob):
    return float(blob.tokens.count(word)) / len(blob.tokens)


# Computes IDF
def compute_idf(word, blob_list, n_containing):
    return math.log(len(blob_list) / n_containing[word])


# Computes TF-IDF
def compute_tf_idf(word, blob, idf):
    return compute_tf(word, blob) * idf


# Loads data from tagged email files
def load_data(folder):
    data = []

    for filename in os.listdir(folder):
        for i, line in enumerate(tuple(codecs.open(folder + filename, "r"))):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)
                    data.append((tokens, label, i))

    return data


# Checks if a list contains another
def contains(big, small):
    for i in xrange(len(big) - len(small) + 1):
        for j in xrange(len(small)):
            if big[i + j] != small[j]:
                break
        else:
            return i, i + len(small)

    return False


# Builds an id string from a list of tokens
def make_id_from_tokens(tokens):
    # weirdly done but ensures ids are identical to those created in build_unigram_features()
    return hashlib.md5(" ".join(TextBlob(" ".join(tokens)).tokens)).hexdigest()


# Launch
if __name__ == "__main__":
    main(sys.argv)
