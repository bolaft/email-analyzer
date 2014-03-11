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
from nltk.metrics.segmentation import windowdiff, ghd, pk
from optparse import OptionParser

import re
import nltk
import codecs
import os
import string
import subprocess
import math
import sys
import time

# Paths
DATA_FOLDER = "data/ubuntu-users/email.message.tagged/"

# Wapiti
WAPITI_TRAIN_FILE = WAPITI_TEST_FILE = WAPITI_GOLD_FILE = WAPITI_RESULT_FILE = WAPITI_MODEL_FILE = WAPITI_PATTERN_FILE = None

# Constants
instances = 0

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

# Main
def main(options):
    dirpath = "var/" + time.strftime("%m%d") + "/" + options.name + "/"

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    if options.save:
        print("[%s] Copying script.py..." % time.strftime("%H:%M:%S"))
        subprocess.call("cp %s %sscript.py" % (sys.argv[0], dirpath), shell=True)

    global WAPITI_TRAIN_FILE, WAPITI_TEST_FILE, WAPITI_GOLD_FILE, WAPITI_RESULT_FILE, WAPITI_MODEL_FILE, WAPITI_PATTERN_FILE

    WAPITI_TRAIN_FILE = dirpath + "train"
    WAPITI_TEST_FILE = dirpath + "test"
    WAPITI_GOLD_FILE = dirpath + "gold"
    WAPITI_RESULT_FILE = dirpath + "result"
    WAPITI_MODEL_FILE = dirpath + "model"
    WAPITI_PATTERN_FILE = dirpath + "patterns"

    if options.build:
        print("[%s] Building datafiles..." % time.strftime("%H:%M:%S"))
        make_datafiles(options.maximum, filter_observations=True)

    if options.patterns:
        print("[%s] Building pattern file..." % time.strftime("%H:%M:%S"))
        make_patterns()

    if options.train:
        print("[%s] Training model..." % time.strftime("%H:%M:%S"))
        subprocess.call("wapiti train -p %s %s %s" % (WAPITI_PATTERN_FILE, WAPITI_TRAIN_FILE, WAPITI_MODEL_FILE), shell=True)

    if options.label:
        print("[%s] Applying model on test data" % time.strftime("%H:%M:%S"))
        subprocess.call("wapiti label -m %s -p %s %s" % (WAPITI_MODEL_FILE, WAPITI_TEST_FILE, WAPITI_RESULT_FILE) , shell=True)

    if options.check:
        print("[%s] Checking results..." % time.strftime("%H:%M:%S"))
        subprocess.call("wapiti label -m %s -p -c %s" % (WAPITI_MODEL_FILE, WAPITI_GOLD_FILE), shell=True)

    if options.evaluate:
        print("[%s] Evaluating segmentation..." % time.strftime("%H:%M:%S"))
        evaluate_segmentation()


# Evaluates the segmentation results
def evaluate_segmentation():
    g = data_to_string(WAPITI_GOLD_FILE) # gold string
    r = data_to_string(WAPITI_RESULT_FILE) # result string

    avg = float(len(g)) / g.count("T") # average segment size
    k = int(avg / 2) # window size for WindowDiff

    b = ("T" + (int(avg) - 1) * ".") * int(math.ceil(float(len(g)) / int(avg)))
    b = b[:len(g)]

    # WindowDiff
    wd_rs = (float(windowdiff(g, r, k, boundary="T")) / len(g)) * 100
    wd_bl = (float(windowdiff(g, b, k, boundary="T")) / len(g)) * 100

    # Beeferman's Pk
    pk_rs = (pk(g, r, boundary="T")) * 100
    pk_bl = (pk(g, b, boundary="T")) * 100

    # Generalized Hamming Distance
    ghd_rs = (ghd(g, r, boundary="T") / len(g)) * 100
    ghd_bl = (ghd(g, b, boundary="T") / len(g)) * 100

    print("#            \tResult:\tBase.:\tDiff.:")
    print("# WindowDiff:\t%s%%\t%s%%\t%s" % (dec(wd_rs), dec(wd_bl), dec(wd_bl - wd_rs)))
    print("# pk:        \t%s%%\t%s%%\t%s" % (dec(pk_rs), dec(pk_bl), dec(pk_bl - pk_rs)))
    print("# ghd:       \t%s%%\t%s%%\t%s" % (dec(ghd_rs), dec(ghd_bl), dec(ghd_bl - ghd_rs)))
    print("#")
    print("#            \tResult:\tBase.:")
    print("# seg. ratio:\tx%s\tx%s" % (dec(float(r.count("T")) / g.count("T")), dec(float(b.count("T")) / g.count("T"))))
    print("#")
    print("# gold:     %s" % g[:75])
    print("# result:   %s" % r[:75])
    print("# baseline: %s" % b[:75])


# Formats a float
def dec(f):
    return "{0:.2f}".format(f)


# Makes a string of labels
def data_to_string(path):
    s = ""

    with codecs.open(path, "r", "utf-8") as f:
        for line in f:
            if len(line) > 1:
                tokens = line.split()
                s += tokens[-1]

    return s.replace("F", ".")

# Writes wapiti datafiles
def make_datafiles(limit, filter_observations=False):
    with codecs.open(WAPITI_TRAIN_FILE, "w", "utf-8") as train_out:
        with codecs.open(WAPITI_TEST_FILE, "w", "utf-8") as test_out:
            with codecs.open(WAPITI_GOLD_FILE, "w", "utf-8") as gold_out:
                train_limit = int(limit * 0.9)

                print("# preprocessing...")

                train = True
                progress = ProgressBar(maxval=limit).start()

                for i, filename in enumerate(os.listdir(DATA_FOLDER)):
                    progress.update(i)
                    if i == limit:
                        break
                    if i == train_limit:
                        train = False

                    prev_label = next_label = None
                    
                    lines = codecs.open(DATA_FOLDER + filename, "r", "utf-8").readlines()
                    for line_number, line in enumerate(lines):
                        line = line.strip()

                        if not line.startswith("#"):
                            tokens = line.split()
                            if len(tokens) > 1:
                                raw_label = tokens.pop(0)
                                label = "T" if raw_label == "B" or raw_label == "BE" else "F"
                                next_label = None

                                if len(lines) > line_number + 1:
                                    next_line = lines[line_number + 1].split()
                                    if len(next_line) > 1:
                                        next_label = next_line.pop(0)

                                if raw_label != "I" or not filter_observations or not train or raw_label != prev_label or raw_label != next_label:
                                    update_average_visual_features(tokens, line_number + 1, len(lines))

                                prev_label = raw_label

                progress.finish()
                
                print("# building train, test and gold datafiles...")
                
                wnl = WordNetLemmatizer()
                train = True
                progress = ProgressBar(maxval=limit).start()

                for i, filename in enumerate(os.listdir(DATA_FOLDER)):
                    progress.update(i)
                    if i == limit:
                        break
                    if i == train_limit:
                        train = False

                    prev_label = next_label = None

                    lines = codecs.open(DATA_FOLDER + filename, "r", "utf-8").readlines()
                    for line_number, line in enumerate(lines):
                        line = line.strip()

                        if not line.startswith("#"):
                            tokens = line.split()

                            if len(tokens) > 1:
                                raw_label = tokens.pop(0)
                                label = "T" if raw_label == "B" or raw_label == "BE" else "F"
                                next_label = None

                                if len(lines) > line_number + 1:
                                    next_line = lines[line_number + 1].split()
                                    if len(next_line) > 1:
                                        next_label = next_line.pop(0)

                                if raw_label != "I" or not filter_observations or not train or raw_label != prev_label or raw_label != next_label:
                                    tokens_lemmas_tags = [(token, wnl.lemmatize(clear_numbers(token.lower()), "v" if tag.startswith("V") else "n"), tag) for token, tag in nltk.pos_tag(tokens)]

                                    features = ""

                                    for j in [0, 1, 2, -3, -2, -1]:
                                        if j >= len(tokens_lemmas_tags) or j < len(tokens_lemmas_tags) * -1:
                                            features += "@NULL\t@NULL\t@NULL\t"
                                        else:
                                            token, lemma, tag = tokens_lemmas_tags[j]

                                            features += "%s\t%s\t%s\t" % (token, lemma, tag)

                                    for vf in build_visual_features(tokens_lemmas_tags, line_number + 1, len(lines)):
                                        features += "%s\t" % vf

                                    if train:
                                        train_out.write("%s%s\n" % (features, label))
                                    else:
                                        gold_out.write("%s%s\n" % (features, label))
                                        test_out.write("%s\n" % features)

                                prev_label = raw_label

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
    progress = ProgressBar(maxval=97).start()

    with codecs.open(WAPITI_PATTERN_FILE, "w", "utf-8") as out:
        i = 1
        progress.update(i)

        for off in xrange(-1, 2):
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


# Launch
if __name__ == "__main__":
    op = OptionParser()

    op.add_option("-s", "--save", 
        dest="save", 
        default=False, 
        action="store_true",
        help="saves a backup of the script in its current form")

    op.add_option("-b", "--build", 
        dest="build", 
        default=False, 
        action="store_true",
        help="builds train, test and gold datafiles")

    op.add_option("-p", "--patterns", 
        dest="patterns", 
        default=False, 
        action="store_true",
        help="builds a patterns file")

    op.add_option("-t", "--train", 
        dest="train", 
        default=False, 
        action="store_true",
        help="trains and saves a model to file (-b required in current or previous run)")

    op.add_option("-l", "--label", 
        dest="label", 
        default=False, 
        action="store_true",
        help="labels the test file and saves the result to file (-bt required in current or previous run)")

    op.add_option("-c", "--check", 
        dest="check", 
        default=False, 
        action="store_true",
        help="displays P, R and F1 (-bt required in current or previous run)")

    op.add_option("-e", "--evaluate", 
        dest="evaluate", 
        default=False, 
        action="store_true",
        help="prints segmentation metrics (-l required in current or previous run")

    op.add_option("-a", "--all", 
        dest="all", 
        default=False, 
        action="store_true",
        help="switches all options on")

    op.add_option("-m", "--maximum", 
        dest="maximum",
        type="int",
        default=1000,
        help="maximum number of instances (defaults to 1000)")

    op.add_option("-n", "--name", 
        dest="name",
        help="experiment name (required)")

    options, args = op.parse_args()

    if options.name == None:
        op.error("Set an experiment name with -n or --name")

    if options.all:
        options.save = options.check = options.train = options.build = options.patterns = options.label = options.evaluate = True

    main(options)
