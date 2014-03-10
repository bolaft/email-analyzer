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
from nltk.metrics.segmentation import windowdiff

import re
import nltk
import sys
import codecs
import os
import string
import subprocess


# Wapiti
WAPITI_TRAIN_FILE = "var/train"
WAPITI_TEST_FILE = "var/test"
WAPITI_GOLD_FILE = "var/gold"
WAPITI_RESULT_FILE = "var/result"
WAPITI_MODEL_FILE = "var/model"
WAPITI_PATTERN_FILE = "var/patterns"

# Constants
limit = 100

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
    make_datafiles(source_folder)
    make_patterns()

    print("Training model...")
    subprocess.call("wapiti train -p " + WAPITI_PATTERN_FILE + " " + WAPITI_TRAIN_FILE + " " + WAPITI_MODEL_FILE, shell=True)

    print("Applying model on test data...")
    subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p " + WAPITI_TEST_FILE + " " + WAPITI_RESULT_FILE, shell=True)

    print("Checking...")
    subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p -c " + WAPITI_GOLD_FILE, shell=True)

    evaluate()


# Evaluates the results
def evaluate():
    g = ""

    with codecs.open(WAPITI_GOLD_FILE, "r", "utf-8") as gold:
        for line in gold:
            if len(line) > 1:
                tokens = line.split()
                g += tokens[-1]

    r = ""
    
    with codecs.open(WAPITI_RESULT_FILE, "r", "utf-8") as result:
        for line in result:
            if len(line) > 1:
                tokens = line.split()
                r += tokens[-1]

    r = r.replace("F", ".")
    g = g.replace("F", ".")

    k = int(float(len(g)) / g.count("T"))

    wd = windowdiff(g, r, k, boundary="T")

    print("WindowDiff: %s" % wd)
    print("gold:       %s" % g[:75])
    print("result:     %s" % r[:75])


# Writes wapiti datafiles
def make_datafiles(source_folder):

    train = True

    wnl = WordNetLemmatizer()

    with codecs.open(WAPITI_TRAIN_FILE, "w", "utf-8") as train_out:
        with codecs.open(WAPITI_TEST_FILE, "w", "utf-8") as test_out:
            with codecs.open(WAPITI_GOLD_FILE, "w", "utf-8") as gold_out:

                print("Preprocessing...")

                progress = ProgressBar(maxval=limit).start()

                for i, filename in enumerate(os.listdir(source_folder)):
                    progress.update(i)
                    if i == limit:
                        break

                    lines = tuple(codecs.open(source_folder + filename, "r", "utf-8"))
                    for line_number, line in enumerate(lines):
                        line = line.strip()

                        if not line.startswith("#"):
                            tokens = line.split()
                            if len(tokens) > 1:
                                label = tokens.pop(0)

                                update_average_visual_features(tokens, line_number, len(lines))

                progress.finish()
                
                print("Making datafiles...")

                progress = ProgressBar(maxval=limit).start()

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
                                tokens_lemmas_tags = [(token, wnl.lemmatize(clear_numbers(token.lower()), "v" if tag.startswith("V") else "n"), tag) for token, tag in nltk.pos_tag(tokens)]

                                features = ""

                                for j in [0, 1, 2, -3, -2, -1]:
                                    if j >= len(tokens_lemmas_tags) or j < len(tokens_lemmas_tags) * -1:
                                        features += "@NULL\t@NULL\t@NULL\t"
                                    else:
                                        token, lemma, tag = tokens_lemmas_tags[j]

                                        features += token + "\t" + lemma + "\t" + tag + "\t"

                                for vf in build_visual_features(tokens_lemmas_tags, line_number, len(lines)):
                                    features += vf + "\t"

                                label = "T" if label == "B" or label == "BE" else "F"

                                if train:
                                    train_out.write(features + label + "\n")
                                else:
                                    gold_out.write(features + label + "\n")
                                    test_out.write(features + "\n")

                    if train:
                        train_out.write("\n")
                    else:
                        gold_out.write("\n")
                        test_out.write("\n")

                progress.finish()


# Builds visual features
def build_visual_features(tokens_lemmas_tags, line_number, total_lines):
    features = []
    tokens = [token for token, lemma, tag in tokens_lemmas_tags]
    line = " ".join(tokens)
    line_lower = line.lower()
    
    # position
    x = float(line_number) / total_lines
    features.append(make_feature("position", x))

    # number of tokens
    x = len(tokens)
    features.append(make_feature("number_of_tokens", x))

    # number of characters
    x = len(line)
    features.append(make_feature("number_of_characters", x))

    # number of quote symbols
    x = line.count(">")
    features.append(make_feature("number_of_quote_symbols", x))

    # average token length
    x = sum(map(len, tokens)) / float(len(tokens))
    features.append(make_feature("average_token_length", x))

    # proportion of uppercase characters
    x = float(sum(x.isupper() for x in line)) / len(line)
    features.append(make_feature("proportion_of_uppercase_characters", x))

    # proportion of alphabetic characters
    x = float(sum(x.isalpha() for x in line)) / len(line)
    features.append(make_feature("proportion_of_alphabetic_characters", x))

    # proportion of numeric characters
    x = float(sum(x.isdigit() for x in line)) / len(line)
    features.append(make_feature("proportion_of_numeric_characters", x))

    # has interrogation mark
    features.append("has_interrogation_mark" if line.count("?") > 0 else "no_interrogation_mark")

    # has colon
    features.append("has_colon" if line.count(":") > 0 else "no_colon")

    # has early punctuation
    first_punctuation_position = 999

    for i, token in enumerate(tokens):
        if token in [".", ";", ":", "?", "!", ","]:
            first_punctuation_position = i

    features.append("has_early_punctuation" if first_punctuation_position < 5 else "no_early_punctuation")

    # has interrogating word
    features.append("has_interrogating_word" if not set([token.lower() for token in tokens]).isdisjoint(["who", "when", "where", "what", "which", "what", "how"]) else "no_interrogating_word")

    # starts with interrogating form
    features.append("starts_with_interrogating_form" if tokens[0].lower() in ["who", "when", "where", "what", "which", "what", "how", "is", "are", "am", "will", "do", "does", "have", "has"] else "does_not_start_with_interrogating_form")

    # first verb form
    first_verb_form = "NO_VERB"

    for token, lemma, tag in tokens_lemmas_tags:
        if tag in ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]:
            first_verb_form = tag
            break

    features.append(first_verb_form)

    # first personal pronoun
    first_personal_pronoun = "NO_PERSONAL_PRONOUN"

    for token in tokens:
        if token.lower() in ["i", "you", "he", "she", "we", "they"]:
            first_personal_pronoun = token.upper()

    features.append(first_personal_pronoun)

    # contains modal word
    features.append("contains_modal_word" if any(ngram in line_lower for ngram in [
        "may", "must", "musn" "shall", "shan" "will", "might", "should", "would", "could"
    ]) else "does_not_contain_modal_word")
    
    # contains plan phrase
    features.append("contains_plan_phrase" if any(ngram in line_lower for ngram in [
        "i will", "i am going to", "we will", "we are going to", "i plan to", "we plan to"
    ]) else "does_not_contain_plan_phrase")

    # contains first person mark
    features.append("contains_first_person_mark" if any(ngram in line_lower for ngram in [
        "me", "us", "i", "we", "my", "mine", "myself", "ourselves"
    ]) else "does_not_contain_first__person_mark")
    
    # contains second person mark
    features.append("contains_second_person_mark" if any(ngram in line_lower for ngram in [
        "you", "your", "yours", "yourself", "yourselves"
    ]) else "does_not_contain_second_person_mark")
    
    # contains third person mark
    features.append("contains_third_person_mark" if any(ngram in line_lower for ngram in [
        "he", "she", "they", "his", "their", "hers", "him", "her", "them"
    ]) else "does_not_contain_third_person_mark")

    return features


# Updates average visual features
def update_average_visual_features(tokens, line_number, total_lines):
    line = " ".join(tokens)

    global avg, instances

    instances += 1

    avg["position"] += float(line_number) / total_lines
    avg["number_of_tokens"] += len(tokens)
    avg["number_of_characters"] += len(line)
    avg["number_of_quote_symbols"] += line.count(">")
    avg["average_token_length"] += sum(map(len, tokens)) / float(len(tokens))
    avg["proportion_of_uppercase_characters"] += float(sum(x.isupper() for x in line)) / len(line)
    avg["proportion_of_alphabetic_characters"] += float(sum(x.isalpha() for x in line)) / len(line)
    avg["proportion_of_numeric_characters"] += float(sum(x.isdigit() for x in line)) / len(line)


# Transforms a numeric value into a string feature
def make_feature(prefix, x):
    x = float(x)
    average = float(avg[prefix]) / instances
    tier = "high"

    if x > average * 1.5:
        tier = "highest"
    elif x < average:
        tier = "low"
    elif x < float(average) / 2:
        tier = "lowest"

    return prefix + "_" + tier


# Replaces numbers by #
def clear_numbers(s):
    return re.sub('[%s]' % string.digits, '#', s)


# Computes and writes patterns
def make_patterns():
    print("Making patterns...")

    progress = ProgressBar(maxval=353).start()

    with codecs.open(WAPITI_PATTERN_FILE, "w", "utf-8") as out:
        i = 1
        progress.update(i)

        # for col in progress(range(8, largest_sentence + 8)):
        for off in xrange(-5, 6):
            off = str(off) if off < 1 else "+" + str(off)

            for base_col in xrange(0, 3):
                out.write("*" + str(i) + ":%x[" + off + "," + str(base_col + 0) + "]\n")
                i += 1
                out.write("*" + str(i) + ":%x[" + off + "," + str(base_col + 0) + "]/%x[" + off + "," + str(base_col + 3) + "]\n")
                i += 1
                out.write("*" + str(i) + ":%x[" + off + "," + str(base_col + 3) + "]/%x[" + off + "," + str(base_col + 6) + "]\n")
                i += 1
                out.write("*" + str(i) + ":%x[" + off + "," + str(base_col + 0) + "]/%x[" + off + "," + str(base_col + 3) + "]/%x[" + off + "," + str(base_col + 6) + "]\n")
                i += 1

                progress.update(i)

            for col in xrange(18, 38):
                out.write("*" + str(i) + ":%x[" + off + "," + str(col) + "]\n")
                i += 1
                
                progress.update(i)

            out.write("\n")

    progress.finish()


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
