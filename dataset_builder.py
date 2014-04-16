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

import nltk

import sys
import codecs
import os
import hashlib
import re


# Parameters
ONLY_INITIAL = True # keep only the first message of each thread
ONLY_UTF8 = True # filter out payloads not encoded in utf-8
ONLY_TEXT_PLAIN = True # filter out xml and html payloads
FILTER_OBSERVATIONS = False # ignores multiple consecutive observations with "I" label in training
OCCURRENCE_THRESHOLD_QUOTIENT = 0.075 # ignores words which occur less than once per (quotient * len(train)) messages

# Data
DATA_FOLDER = "data/email.message.tagged/" # folder where heuristically labelled emails are stored
TEXT_TILING_FOLDER = "data/TT/ubuntu-users/" # folder where emails labelled by text-tiling are stored
NGRAM_FILE = "ngrams"
ARFF_FILE = "dataset.arff"

# Misc.
ngrams = []
min_occurrences = 0
standard_deviation = standard_average = None

# Constants
visual_feature_list = [
    ("position", "integer"),
    ("number_of_tokens", "integer"),
    ("number_of_characters", "integer"),
    ("number_of_quote_symbols", "integer"),
    ("average_token_length", "real"),
    ("proportion_of_uppercase_characters", "real"),
    ("proportion_of_alphabetic_characters", "real"),
    ("proportion_of_numeric_characters", "real"),
    ("contains_interrogation_mark", "{TRUE, FALSE}"),
    ("ends_with_interrogation_mark", "{TRUE, FALSE}"),
    ("contains_colon", "{TRUE, FALSE}"),
    ("ends_with_colon", "{TRUE, FALSE}"),
    ("previous_contains_interrogation_mark", "{NULL, TRUE, FALSE}"),
    ("previous_ends_with_interrogation_mark", "{NULL, TRUE, FALSE}"),
    ("previous_contains_colon", "{NULL, TRUE, FALSE}"),
    ("previous_ends_with_colon", "{NULL, TRUE, FALSE}"),
    ("next_contains_interrogation_mark", "{NULL, TRUE, FALSE}"),
    ("next_ends_with_interrogation_mark", "{NULL, TRUE, FALSE}"),
    ("next_contains_colon", "{NULL, TRUE, FALSE}"),
    ("next_ends_with_colon", "{NULL, TRUE, FALSE}"),
    ("starts_with_interrogating_word", "{TRUE, FALSE}"),
    ("contains_interrogating_word", "{TRUE, FALSE}"),
    ("first_verb_form", "{NO_VERB, VB, VBD, VBG, VBN, VBP, VBZ}"),
    ("first_punctuation_position", "integer"),
    ("first_personal_pronoun", "{NO_PERSONAL_PRONOUN, I, YOU, HE, SHE, WE, THEY}"),
    ("contains_modal_word", "{TRUE, FALSE}"),
    ("contains_plan_phrase", "{TRUE, FALSE}")
]


# Main
def main(argv):
    # reading imposed ngram list
    
    imposed_ngrams = [ngram.strip() for ngram in tuple(codecs.open(NGRAM_FILE, "r"))]

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

    data = load_data()

    # building dataset
    
    print("preprocessing...")

    # blobs = [] # list of all text blob (one per sentence)
    # ngrams = set([]) # set of all distinct ngrams in corpus
    # n_containing = {} # for each word, number of documents containing it

    progress = ProgressBar()

    ################################################################################
    
    for i, (tokens, label, line_number) in enumerate(progress(data)):
        features = {}
        sentence = " ".join(tokens)

        next_sentence = previous_sentence = None

        if i < len(data) - 1:
            next_tokens, next_label, next_line_number = data[i + 1]
            next_sentence = " ".join(next_tokens)
        if i > 0:
            previous_tokens, previous_label, previous_line_number = data[i - 1]
            previous_sentence = " ".join(previous_tokens)

        # building visual features
        token_tag_pairs = nltk.pos_tag(tokens)

        features.update(build_visual_features(dict(visual_feature_list), previous_sentence, sentence, next_sentence, [t.lower() for t in tokens], token_tag_pairs, line_number))
        
        for imposed_ngram in imposed_ngrams:
            features[imposed_ngram] = sentence.count(imposed_ngram)

        # preprocessing for ngram features

        blob = TextBlob(sentence)
        # blob_ngrams = blob.tokens + extract_bigrams(blob)
        # blob_ngrams = [ngram.encode("utf-8") for ngram in blob_ngrams]

        # for ngram in set(blob_ngrams):
        #     if not ngram in n_containing:
        #         n_containing[ngram] = 1
        #     else:
        #         n_containing[ngram] += 1

        # ngrams.update(blob_ngrams)
        # blobs.append(blob)

        sid = make_sid(blob)

        dataset[sid] = {}
        dataset[sid]["label"] = label
        dataset[sid]["features"] = features

    #################################################################################

    # writing arff file
    
    print("compiling and exporting data to " + ARFF_FILE + "...")

    write_arff(dataset, feature_list)

    print("export successful")


# Makes sentence id from blob
def make_sid(blob):
    tokens = [ngram.encode("utf-8") for ngram in blob.tokens]
    return hashlib.md5(" ".join(tokens)).hexdigest()


# Extracts bigrams from a blob
def extract_bigrams(blob):
    return [x + " " + y for x, y in zip(blob.tokens, blob.tokens[1:])]


# Builds visual features
def build_visual_features(visual_feature_list, previous_sentence, sentence, next_sentence, tokens, token_tag_pairs, line_number):
    values = {}

    values["position"] = line_number
    values["number_of_tokens"] = len(tokens)
    values["number_of_characters"] = len(sentence)
    values["number_of_quote_symbols"] = sentence.count(">")
    values["average_token_length"] = sum(map(len, tokens)) / float(len(tokens))
    values["proportion_of_uppercase_characters"] = float(sum(x.isupper() for x in sentence)) / len(sentence)
    values["proportion_of_alphabetic_characters"] = float(sum(x.isalpha() for x in sentence)) / len(sentence)
    values["proportion_of_numeric_characters"] = float(sum(x.isdigit() for x in sentence)) / len(sentence)

    values["contains_interrogation_mark"] = "TRUE" if sentence.count("?") > 0 else "FALSE"
    values["ends_with_interrogation_mark"] = "TRUE" if sentence[-1] == "?" else "FALSE"
    values["contains_colon"] = "TRUE" if sentence.count(":") > 0 else "FALSE"
    values["ends_with_colon"] = "TRUE" if sentence[-1] == ":" else "FALSE"
    
    values["previous_contains_interrogation_mark"] = "NULL"
    
    if previous_sentence != None:
        values["previous_contains_interrogation_mark"] = "TRUE" if previous_sentence.count("?") > 0 else "FALSE"
    
    values["previous_ends_with_interrogation_mark"] = "NULL"
    
    if previous_sentence != None:
        values["previous_ends_with_interrogation_mark"] = "TRUE" if previous_sentence[-1] == "?" else "FALSE"
    
    values["previous_contains_colon"] = "NULL"
    
    if previous_sentence != None:
        values["previous_contains_colon"] = "TRUE" if previous_sentence.count(":") > 0 else "FALSE"
    
    values["previous_ends_with_colon"] = "NULL"
    
    if previous_sentence != None:
        values["previous_ends_with_colon"] = "TRUE" if previous_sentence[-1] == ":" else "FALSE"
    
    values["next_contains_interrogation_mark"] = "NULL"
    
    if next_sentence != None:
        values["next_contains_interrogation_mark"] = "TRUE" if next_sentence.count("?") > 0 else "FALSE"
    
    values["next_ends_with_interrogation_mark"] = "NULL"
    
    if next_sentence != None:
        values["next_ends_with_interrogation_mark"] = "TRUE" if next_sentence[-1] == "?" else "FALSE"
    
    values["next_contains_colon"] = "NULL"
    
    if next_sentence != None:
        values["next_contains_colon"] = "TRUE" if next_sentence.count(":") > 0 else "FALSE"
    
    values["next_ends_with_colon"] = "NULL"
    
    if next_sentence != None:
        values["next_ends_with_colon"] = "TRUE" if next_sentence[-1] == ":" else "FALSE"

    values["starts_with_interrogating_word"] = "TRUE" if tokens[0] in ["who", "when", "where", "what", "which", "what", "how"] else "FALSE"
    values["contains_interrogating_word"] = "TRUE" if not set(tokens).isdisjoint(["who", "when", "where", "what", "which", "what", "how"]) else "FALSE"

    values["first_verb_form"] = "NO_VERB"

    for token, tag in token_tag_pairs:
        if tag in ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]:
            values["first_verb_form"] = tag
            break

    values["first_punctuation_position"] = -1

    for i, token in enumerate(tokens):
        if token in [".", ";", ":", "?", "!"]:
            values["first_punctuation_position"] = i

    values["first_personal_pronoun"] = "NO_PERSONAL_PRONOUN"

    for token in tokens:
        if token in ["i", "you", "he", "she", "we", "they"]:
            values["first_personal_pronoun"] = token.upper()

    # values["tense_and_personal_pronoun"] = None

    values["contains_modal_word"] = "TRUE" if any(word in sentence for word in ["may", "must", "shall", "will", "might", "should", "would", "could"]) else "FALSE"
    values["contains_plan_phrase"] = "TRUE" if any(ngram in sentence for ngram in ["i will", "i am going to", "we will", "we are going to", "i plan to", "we plan to"]) else "FALSE"

    return values


# Writes arff files
def write_arff(dataset, feature_list):
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

            out.write("," + dataset[sid]["label"])

            out.write("\n")


# Replaces special chars from a string
def replace_special_chars(str, replace):
    return re.sub("[^0-9a-zA-Z]+", replace, str)


# Loads data from tagged email files
def load_data(max_lines, filter_i=False):
    data = []

    print("loading data from " + DATA_FOLDER + "...")

    progress = ProgressBar(maxval=max_lines).start()

    ln = 0

    # prev_label_boolean = prev_label = None

    for filename in os.listdir(DATA_FOLDER):
        for i, line in enumerate(tuple(codecs.open(DATA_FOLDER + filename, "r", "utf-8"))):
            line = line.strip()
            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)

                    label_boolean = "T" if label == "B" or label == "BE" else "F"

                    # if prev_label_boolean == label_boolean:
                    #     continue

                    # if not filter_i or label != "I" or prev_label != "I": # filters out consecutive "I" labelled sentences
                    data.append((tokens, label_boolean, i))
                    
                    # prev_label_boolean = label_boolean
                    # prev_label = label
                    
                    ln += 1
                    if ln < max_lines:
                        progress.update(ln)
            
        if ln > max_lines:
            break

    progress.finish()

    return data


# Launch
if __name__ == "__main__":
    main(sys.argv)
