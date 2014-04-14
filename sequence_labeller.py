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

import codecs
import math
import operator
import os
import re
import string
import subprocess
import sys
import time

from collections import Counter
from nltk import pos_tag
from nltk.classify import SklearnClassifier
from nltk.metrics.scores import accuracy
from nltk.metrics.segmentation import windowdiff, ghd, pk
from nltk.probability import FreqDist
from nltk.stem.wordnet import WordNetLemmatizer
from optparse import OptionParser
from progressbar import ProgressBar
from sklearn import metrics
from sklearn.naive_bayes import MultinomialNB


# Parameters
ONLY_INITIAL = True
ONLY_UTF8 = True
ONLY_TEXT_PLAIN = True
FILTER_OBSERVATIONS = True
OCCURRENCE_THRESHOLD_QUOTIENT = 0.05

# Data
DATA_FOLDER = "data/email.message.tagged/"
TEXT_TILING_FOLDER = "data/TT/ubuntu-users/"

# Scores
HTML_RESULT_FILE = TEXT_RESULT_FILE = None

# BC3
BC3_TAGGED_FILE = "data/bc3/bc3_tagged"
BC3_LABELLED_FILE = "data/bc3/bc3_labelled"
BC3_TEXT_TILING_FILE = "data/bc3/bc3_text_tiling"

# Wapiti
WAPITI_TRAIN_FILE = WAPITI_TEST_FILE = WAPITI_GOLD_FILE = WAPITI_RESULT_FILE = WAPITI_MODEL_FILE = WAPITI_PATTERN_FILE = None

# Constants
min_occurrences = 0

standard_deviation = standard_average = None

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

occ = {} # occurrences counter


# Main
def main(options, args):
    dirpath = "var/%s/" % args[0]

    # Makes the folder if it does not exist already
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    # Makes a copy of the script for future reference
    if options.save:
        print("[{0}] Copying script.py...".format(time.strftime("%H:%M:%S")))
        subprocess.call("cp {0} {1}script.py".format(sys.argv[0], dirpath), shell=True)

    # Dynamic text tiling result file path
    global TEXT_TILING_RESULT_FILE

    TEXT_TILING_RESULT_FILE = dirpath + "text_tiling"

    # Wapiti paths
    global WAPITI_TRAIN_FILE, WAPITI_TEST_FILE, WAPITI_GOLD_FILE, WAPITI_RESULT_FILE, WAPITI_MODEL_FILE, WAPITI_PATTERN_FILE

    WAPITI_TRAIN_FILE = dirpath + "train"
    WAPITI_TEST_FILE = dirpath + "test"
    WAPITI_GOLD_FILE = dirpath + "gold"
    WAPITI_RESULT_FILE = dirpath + "result"
    WAPITI_MODEL_FILE = dirpath + "model"
    WAPITI_PATTERN_FILE = dirpath + "patterns"

    # HTML path
    global HTML_RESULT_FILE, TEXT_RESULT_FILE

    HTML_RESULT_FILE = dirpath + "export.html"
    TEXT_RESULT_FILE = dirpath + "scores.txt"

    if options.patterns:
        print("[{0}] Building pattern file...".format(time.strftime("%H:%M:%S")))
        make_patterns()

    scores = []

    # filenames will be suffixed by fold
    if not options.bc3 and options.folds > 1:
        WAPITI_TRAIN_FILE += "_"
        WAPITI_TEST_FILE += "_"
        WAPITI_GOLD_FILE += "_"
        WAPITI_RESULT_FILE += "_"
        WAPITI_MODEL_FILE += "_"

    if options.build or options.train or options.label or options.check or options.evaluate:
        for fold, (train_files, test_files) in enumerate(generate_k_pairs(options.bc3, options.maximum, options.folds, only_initial=ONLY_INITIAL, only_utf8=ONLY_UTF8, only_text_plain=ONLY_TEXT_PLAIN)):
            if not options.bc3 and options.folds > 1:
                print("[{0}] Fold {1}/{2}...".format(time.strftime("%H:%M:%S"), fold + 1, options.folds))

                WAPITI_TRAIN_FILE = update_filename(WAPITI_TRAIN_FILE, fold)
                WAPITI_TEST_FILE = update_filename(WAPITI_TEST_FILE, fold)
                WAPITI_GOLD_FILE = update_filename(WAPITI_GOLD_FILE, fold)
                WAPITI_RESULT_FILE = update_filename(WAPITI_RESULT_FILE, fold)
                WAPITI_MODEL_FILE = update_filename(WAPITI_MODEL_FILE, fold)
            
            if options.build:
                print("[{0}] Building datafiles...".format(time.strftime("%H:%M:%S")))

                global min_occurrences
                min_occurrences = options.maximum * OCCURRENCE_THRESHOLD_QUOTIENT

                make_datafiles(train_files, test_files, options.bc3, filter_observations=True)

            if options.train:
                print("[{0}] Training model...".format(time.strftime("%H:%M:%S")))
                subprocess.call("wapiti train -p {0} {1} {2}".format(WAPITI_PATTERN_FILE, WAPITI_TRAIN_FILE, WAPITI_MODEL_FILE), shell=True)

            if options.label:
                print("[{0}] Applying model on test data...".format(time.strftime("%H:%M:%S")))
                subprocess.call("wapiti label -m {0} -p {1} {2}".format(WAPITI_MODEL_FILE, WAPITI_TEST_FILE, WAPITI_RESULT_FILE) , shell=True)

            if options.check:
                print("[{0}] Checking results...".format(time.strftime("%H:%M:%S")))
                subprocess.call("wapiti label -m {0} -p -c {1}".format(WAPITI_MODEL_FILE, WAPITI_GOLD_FILE), shell=True)

            if options.evaluate:
                print("[{0}] Computing scores...".format(time.strftime("%H:%M:%S")))
                evaluation = evaluate_segmentation(test_files, bc3=options.bc3)
                scores.append(evaluation)
                write_evaluation(fold, evaluation)

            if options.bc3:
                break;

    if options.bow:
        evaluate_bow()

    if options.experiments:
        print("[{0}] Displaying available experiments...".format(time.strftime("%H:%M:%S")))

        for filename in os.listdir("var"):
            print("# %s" % filename)

    if options.evaluate:
        display_evaluations(scores)


# Makes a new filename (s) for each fold (i)
def update_filename(s, i):
    return s[:s.rfind("_") + 1] + str(i)


# Generates k (train, test) pairs of filename listsfrom the data
def generate_k_pairs(bc3, limit, folds, only_initial=False, only_utf8=False, only_text_plain=False):
    data = []
    lengths = []

    progress = ProgressBar()

    print("# verifying data files...")

    for filename in progress(os.listdir(DATA_FOLDER)):
        if len(data) == limit:
            break

        lines = codecs.open(DATA_FOLDER + filename, "r").readlines()

        for line in lines:
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

                    if (is_initial != "true" and only_initial) or (encoding != "UTF-8" and only_utf8) or (mime != "text/plain" and only_text_plain):
                        break

                    data.append(filename)
                    lengths.append(len(lines))

                    break
            else:
                break

    global standard_deviation, standard_average

    standard_deviation = standard_deviation(lengths)
    standard_average = average(lengths)

    print("# dataset size: {0} ({1} requested)".format(len(data), limit))

    if bc3:
        yield data, [BC3_TAGGED_FILE]
    elif folds == 0:
        yield [], []
    elif folds == 1:
        max_train = int(float(len(data)) * 0.9);
        yield data[:max_train], data[max_train:]
    else:
        for k in xrange(folds):
            train = [x for i, x in enumerate(data) if i % folds != k]
            test = [x for i, x in enumerate(data) if i % folds == k]

            yield train, test


# Writes wapiti datafiles
def make_datafiles(train_files, test_files, bc3=False, filter_observations=False):
    cnt = 0

    with codecs.open(WAPITI_TRAIN_FILE, "w") as train_out:
        with codecs.open(WAPITI_TEST_FILE, "w") as test_out:
            with codecs.open(WAPITI_GOLD_FILE, "w") as gold_out:

                preprocess(train_files, filter_observations) # preprocessing...
               
                print("# building train, test and gold datafiles...")
               
                wnl = WordNetLemmatizer()

                progress = ProgressBar(maxval=len(train_files + test_files)).start()

                # iterates over email.message.tagged files
                for i, filename in enumerate(train_files + test_files):
                    progress.update(i)
                    prev_label = next_label = None
                   
                    # if not building train file, checks if the gold and test files should be made from the bc3 corpus
                    lines = codecs.open(DATA_FOLDER + filename, "r").readlines() if not (bc3 and filename in test_files) else codecs.open(BC3_TAGGED_FILE, "r").readlines()

                    # heuristic: messages of more than n lines are ignored in order to avoid large copy/pasted content such as command outputs
                    if len(lines) > standard_deviation + standard_average and not (filename in test_files and bc3):
                        cnt += 1
                        continue

                    for line_number, line in enumerate(lines):
                        line = line.strip()

                        if not line.startswith("#"): # ignores file header
                            tokens = line.split()

                            # ignores tokens with a low number of occurrences
                            if min_occurrences > 0:
                                for token in tokens[1:]:
                                    if not token.lower() in occ or occ[token.lower()] < min_occurrences:
                                        tokens.remove(token)

                            if len(tokens) == 1:
                                tokens.append("@NULL")

                            if len(tokens) > 1:
                                raw_label = tokens.pop(0) # "B", "I", "E", "BE"
                                label = "T" if raw_label == "B" or raw_label == "BE" or raw_label =="T" else "F" # "T" or "F"
                                next_label = None

                                if len(lines) > line_number + 1:
                                    next_line = lines[line_number + 1].split()
                                    if len(next_line) > 1:
                                        next_label = next_line.pop(0)

                                if raw_label != "I" or not filter_observations or not filename in train_files or raw_label != prev_label or raw_label != next_label:
                                    tokens_lemmas_tags = [(token, wnl.lemmatize(clear_numbers(token.lower()), "v" if tag.startswith("V") else "n"), tag) for token, tag in pos_tag(tokens)]

                                    features = ""

                                    for j in [0, 1, 2, -3, -2, -1]:
                                        if j >= len(tokens_lemmas_tags) or j < len(tokens_lemmas_tags) * -1:
                                            features += "@NULL\t@NULL\t@NULL\t"
                                        else:
                                            token, lemma, tag = tokens_lemmas_tags[j]

                                            features += "{0}\t{1}\t{2}\t".format(token, lemma, tag)

                                    for vf in build_visual_features(tokens_lemmas_tags, line_number + 1, len(lines)):
                                        features += "{0}\t".format(vf)

                                    if filename in train_files:
                                        train_out.write("{0}{1}\n".format(features, label))
                                    else:
                                        # getting the corresponding text tiling label
                                        tt_lines = codecs.open(TEXT_TILING_FOLDER + filename, "r").readlines()
                                        tt_line = tt_lines[line_number - 3]
                                        tt_label = tt_line.strip().split().pop(0)

                                        gold_out.write("{0}{1}\t{2}\n".format(features, tt_label, label))
                                        test_out.write("{0}\n".format(features))

                                prev_label = raw_label

                    if filename in train_files:
                        train_out.write("\n")
                    else:
                        gold_out.write("\n")
                        test_out.write("\n")

                progress.finish()

    print("# {0} messages were ignored (over standard deviation length plus average length, i.e. {1} + {2} = {3})".format(cnt, standard_deviation, standard_average, standard_deviation + standard_average))


# Preprocessing
def preprocess(files, filter_observations):
    print("# preprocessing...")

    global occ # token occurrence counter

    progress = ProgressBar(maxval=len(files)).start()

    # iterates over email.message.tagged files
    for i, filename in enumerate(files):
        progress.update(i)

        prev_label = next_label = None
       
        lines = codecs.open(DATA_FOLDER + filename, "r").readlines()

        for line_number, line in enumerate(lines):
            line = line.strip()

            if not line.startswith("#"): # ignores file header
                tokens = line.split()
                if len(tokens) > 1:
                    raw_label = tokens.pop(0) # "B", "I", "E", "BE"
                    next_label = None

                    for token in tokens:
                        if token.lower() in occ:
                            occ[token.lower()] += 1
                        else:
                            occ[token.lower()] = 1

                    if len(lines) > line_number + 1:
                        next_line = lines[line_number + 1].split()
                        if len(next_line) > 1:
                            next_label = next_line.pop(0)

                    if raw_label != "I" or not filter_observations or raw_label != prev_label or raw_label != next_label:
                        update_average_visual_features(tokens, line_number + 1, len(lines))

                    prev_label = raw_label

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

    # has question mark
    features.append("has_question_mark" if line.count("?") > 0 else "no_question_mark")

    # ends with question mark
    features.append("ends_with_question_mark" if line.endswith("?") else "does_not_end_with_question_mark")

    # has colon
    features.append("has_colon" if line.count(":") > 0 else "no_colon")

    # ends with colon
    features.append("ends_with_colon" if line.endswith(":") else "does_not_end_with_colon")

    # has semicolon
    features.append("has_semicolon" if line.count(";") > 0 else "no_semicolon")

    # ends with semicolon
    features.append("ends_with_semicolon_mark" if line.endswith(";") else "does_not_end_with_semicolon")

    # has early punctuation
    first_punctuation_position = 999

    for i, token in enumerate(tokens):
        if token in [".", ";", ":", "?", "!", ","]:
            first_punctuation_position = i

    features.append("has_early_punctuation" if first_punctuation_position < 4 else "no_early_punctuation")

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
    ]) else "does_not_contain_first_person_mark")
   
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
    progress = ProgressBar(maxval=127).start()

    with codecs.open(WAPITI_PATTERN_FILE, "w") as out:
        i = 1
        progress.update(i)

        for off in xrange(-1, 2):
            off = str(off) if off < 1 else "+" + str(off)

            for base_col in xrange(0, 3):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, base_col)) # unigram 1
                i += 1
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, base_col + 3)) # unigram 2
                i += 1
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, base_col + 6)) # unigram 3
                i += 1
                out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, off, base_col, base_col + 3)) # bigram 1
                i += 1
                out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, off, base_col + 3, base_col + 6)) # bigram 2
                i += 1
                out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]/%x[{1},{4}]\n".format(i, off, base_col, base_col + 3, base_col + 6)) # trigram
                i += 1

                progress.update(i)

            out.write("\n")

            for col in xrange(18, 42):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, col))
                i += 1
               
                progress.update(i)

            out.write("\n")
   
    progress.finish()


# Evaluates the segmentation results
def evaluate_segmentation(test_files, bc3=False, limit=1000):
    g = data_to_string(WAPITI_GOLD_FILE, limit=limit) # gold string
    r = data_to_string(WAPITI_RESULT_FILE, limit=limit) # result string

    if bc3:
        t = data_to_string(BC3_TEXT_TILING_FILE, limit=limit, label_position=0) # text tiling baseline string
    else:
        t = data_to_string(WAPITI_GOLD_FILE, limit=limit, label_position=-2)

    avg = float(len(g)) / (g.count("T") + 1) # average segment size
    k = int(avg / 2) # window size for WindowDiff

    b = ("T" + (int(math.floor(avg)) - 1) * ".") * int(math.ceil(float(len(g)) / int(math.floor(avg))))
    b = b[:len(g)] # baseline string

    # WindowDiff
    wd_rs = (float(windowdiff(g, r, k, boundary="T")) / len(g)) * 100
    wd_bl = (float(windowdiff(g, b, k, boundary="T")) / len(g)) * 100
    wd_tt = (float(windowdiff(g, t, k, boundary="T")) / len(g)) * 100

    # Beeferman's Pk
    pk_rs = (pk(g, r, boundary="T")) * 100
    pk_bl = (pk(g, b, boundary="T")) * 100
    pk_tt = (pk(g, t, boundary="T")) * 100

    # Generalized Hamming Distance
    ghd_rs = (ghd(g, r, boundary="T") / len(g)) * 100
    ghd_bl = (ghd(g, b, boundary="T") / len(g)) * 100
    ghd_tt = (ghd(g, t, boundary="T") / len(g)) * 100

    # accuracy
    acc_rs = accuracy(list(g), list(r)) * 100
    acc_bl = accuracy(list(g), list(b)) * 100
    acc_tt = accuracy(list(g), list(t)) * 100

    # precision, recall, f-measure
    pr_rs = metrics.precision_score(list(g), list(r)) * 100
    re_rs = metrics.recall_score(list(g), list(r)) * 100
    f1_rs = (2.0 * (re_rs * pr_rs)) / (re_rs + pr_rs)

    pr_bl = metrics.precision_score(list(g), list(b)) * 100
    re_bl = metrics.recall_score(list(g), list(b)) * 100
    f1_bl = (2.0 * (re_bl * pr_bl)) / (re_bl + pr_bl)
    
    pr_tt = metrics.precision_score(list(g), list(t)) * 100
    re_tt = metrics.recall_score(list(g), list(t)) * 100
    f1_tt = (2.0 * (re_tt * pr_tt)) / (re_tt + pr_tt)

    return acc_rs, acc_bl, acc_tt, pr_rs, pr_bl, pr_tt, re_rs, re_bl, re_tt, f1_rs, f1_bl, f1_tt, wd_rs, wd_bl, wd_tt, pk_rs, pk_bl, pk_tt, ghd_rs, ghd_bl, ghd_tt, g.count("T"), b.count("T"), r.count("T"), t.count("T")


# Writes evaluation to file
def write_evaluation(fold, evaluation):
    acc_rs, acc_bl, acc_tt, pr_rs, pr_bl, pr_tt, re_rs, re_bl, re_tt, f1_rs, f1_bl, f1_tt, wd_rs, wd_bl, wd_tt, pk_rs, pk_bl, pk_tt, ghd_rs, ghd_bl, ghd_tt, g_count, b_count, r_count, t_count = evaluation
    
    with codecs.open(TEXT_RESULT_FILE, "a+") as out:
        out.write("\n# fold %s\n" % fold)
        out.write(scores_to_string(acc_rs, acc_bl, acc_tt, pr_rs, pr_bl, pr_tt, re_rs, re_bl, re_tt, f1_rs, f1_bl, f1_tt, wd_rs, wd_bl, wd_tt, pk_rs, pk_bl, pk_tt, ghd_rs, ghd_bl, ghd_tt, g_count, b_count, r_count, t_count))


# Formats a float (0.26315 => "0.26")
def dec(f):
    return "{0:.2f}".format(f)


# Makes a string of labels
def data_to_string(path, limit=0, label_position=-1):
    s = ""
    i = 1

    with codecs.open(path, "r") as f:
        for line in f:
            if i == limit:
                break
            tokens = line.split()
            if len(tokens) > 1:
                s += tokens[label_position]
                i += 1

    return s.replace("F", ".").replace("O", ".").replace("S", "T")


# Exports to HTML
def export_html(g, b, r):
    html = ""

    html += "<!doctype html>"
    html += "<html lang=\"%s\">" % "en"
    html += "<head>"
    html += "   <link rel=\"stylesheet\" href=\"%s\" type=\"text/css\">" % "../../style.css"
    html += "   <meta charset=\"%s\">" % "utf-8"
    html += "   <title>%s</title>" % "result.html"
    html += "</head>"
    html += "<body style=\"width: auto\">"
    html += "   <table>"
    html += "       <tr>"
    html += g.replace("T", "<td class=\"g T\">").replace(".", "<td class=\"g F\">")
    html += "       </tr>"
    html += "       <tr>"
    html += r.replace("T", "<td class=\"r T\">").replace(".", "<td class=\"r F\">")
    html += "       </tr>"
    html += "       <tr>"
    html += b.replace("T", "<td class=\"b T\">").replace(".", "<td class=\"b F\">")
    html += "       </tr>"
    html += "   </table>"
    html += "</body>"
    html += "</html>"

    with codecs.open(HTML_RESULT_FILE, "w") as out:
        out.write(html)


# Evaluates BoW approach on segmented and non-segmented BC3
def evaluate_bow():
    lines = codecs.open(BC3_LABELLED_FILE, "r").readlines()

    data = []
    gold = []

    for i, line in enumerate(lines):
        tokens = line.strip().split()

        if len(tokens) > 2:
            label = tokens.pop(0)
            tag = tokens.pop(0)

            if tag == "none":
                continue

            if i < len(lines) and len(lines[i + 1].strip().split()) > 2:
                lines[i + 1].strip().split().pop(0)
                next_label = lines[i + 1].strip().split().pop(0)
            else:
                next_label = "T"

            gold.append(tag)
            data.append((FreqDist(tokens), tag, next_label))

    limit = int(float(len(data)) * 0.8)

    # training set: bags-of-words and tag tuples
    train = [(bow, tag) for bow, tag, next_label in data[:limit]]
    # training the classifier
    classifier = SklearnClassifier(MultinomialNB()).train(train)

    results = {
        "segmented": [],
        "unsegmented": []
    }

    all_choices = [] # all choices made
    choices = [] # choices for the current segment
    nb = 1 # number of lines in the segment
   
    for i, (bow, tag, next_label) in enumerate(data[limit:]):
        # bow classification
        choice = classifier.classify(bow)
        choices.append(choice)
        all_choices.append(choice)

        # line by line classification for unsegmented results
        results["unsegmented"].append(choice)

        # more complex classification for segmented results
        if next_label == "T":
            most_common = Counter(choices).most_common()

            if len(most_common) > 1:
                tf = FreqDist(all_choices)
                vote = most_common[0]
                best = 1

                for candidate, occ in most_common:
                    if tf[candidate] > best:
                        vote = candidate
                        best = tf[candidate]
            else:
                vote, occ = most_common[0]

            results["segmented"] += [vote for choice in choices]
            choices = []
            nb = 1
        else:
            nb += 1 # incrementing the current number of lines in the bag
  
    for i, label in enumerate(gold[limit:]):
        bow, tag, next_label = data[i + limit]
        print("# {0}\t{1}\t{2}".format(label, results["unsegmented"][i], results["segmented"][i]))
        if next_label == "T":
            print("# ------------------")

    # segmented metrics
    sp = metrics.precision_score(gold[limit:], results["segmented"])
    sr = metrics.recall_score(gold[limit:], results["segmented"])
    sf = (2.0 * (sr * sp)) / (sr + sp)

    # unsegmented metrics
    up = metrics.precision_score(gold[limit:], results["unsegmented"])
    ur = metrics.recall_score(gold[limit:], results["unsegmented"])
    uf = (2.0 * (ur * up)) / (ur + up)

    print("#")
    print("#                Pre.:\t\tRec:\t\tF1:")
    print("# segmented:     {0}%\t\t{1}%\t\t{2}%".format(dec(sp * 100), dec(sr * 100), dec(sf * 100)))
    print("# non-segmented: {0}%\t\t{1}%\t\t{2}%".format(dec(up * 100), dec(ur * 100), dec(uf * 100)))


# Merges two bags-of-words:
def merge_bow(a, b):
    for k, v in a.iteritems():
        if k in b:
            b[k] += v
        else:
            b[k] = v

    return b


def display_evaluations(scores):
    total = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0)

    for s in scores:
        total = tuple(map(operator.add, s, total))

    acc_rs, acc_bl, acc_tt, pr_rs, pr_bl, pr_tt, re_rs, re_bl, re_tt, f1_rs, f1_bl, f1_tt, wd_rs, wd_bl, wd_tt, pk_rs, pk_bl, pk_tt, ghd_rs, ghd_bl, ghd_tt, g_count, b_count, r_count, t_count = tuple(x/len(scores) for x in total)

    print(scores_to_string(acc_rs, acc_bl, acc_tt, pr_rs, pr_bl, pr_tt, re_rs, re_bl, re_tt, f1_rs, f1_bl, f1_tt, wd_rs, wd_bl, wd_tt, pk_rs, pk_bl, pk_tt, ghd_rs, ghd_bl, ghd_tt, g_count, b_count, r_count, t_count))


def scores_to_string(acc_rs, acc_bl, acc_tt, pr_rs, pr_bl, pr_tt, re_rs, re_bl, re_tt, f1_rs, f1_bl, f1_tt, wd_rs, wd_bl, wd_tt, pk_rs, pk_bl, pk_tt, ghd_rs, ghd_bl, ghd_tt, g_count, b_count, r_count, t_count):
    s  = "# Cross-validation:\n"
    s += "#\n"
    s += "#            \tResult:\t\tBase.:\tDiff.:\t\tTT.:\tDiff.:\n"
    s += "# WindowDiff:\t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(wd_rs), dec(wd_bl), dec(wd_rs - wd_bl), dec(wd_tt), dec(wd_rs - wd_tt))
    s += "# pk:        \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(pk_rs), dec(pk_bl), dec(pk_rs - pk_bl), dec(pk_tt), dec(pk_rs - pk_tt))
    s += "# ghd:       \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(ghd_rs), dec(ghd_bl), dec(ghd_rs - ghd_bl), dec(ghd_tt), dec(ghd_rs - ghd_tt))
    s += "#\n"
    s += "#            \tResult:\t\tBase.:\tDiff.:\t\tTT.:\tDiff.:\n"
    s += "# accuracy:  \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(acc_rs), dec(acc_bl), dec(acc_rs - acc_bl), dec(acc_tt), dec(acc_rs - acc_tt))
    s += "#\n"
    s += "#            \tResult:\t\tBase.:\tDiff.:\t\tTT.:\tDiff.:\n"
    s += "# precision: \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(pr_rs), dec(pr_bl), dec(pr_rs - pr_bl), dec(pr_tt), dec(pr_rs - pr_tt))
    s += "# recall:    \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(re_rs), dec(re_bl), dec(re_rs - re_bl), dec(re_tt), dec(re_rs - re_tt))
    s += "# F1:        \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(f1_rs), dec(f1_bl), dec(f1_rs - f1_bl), dec(f1_tt), dec(f1_rs - f1_tt))
    s += "#\n"
    s += "#            \tResult:\tBase.:\tTT.:\n"
    s += "# seg. ratio:\tx{0}\tx{1}\tx{2}".format(dec(float(r_count) / g_count), dec(float(b_count) / g_count), dec(float(t_count) / g_count))

    return s


# Compute average
def average(l):
    return sum(l, 0.0) / len(l)
    

# Compute variance
def variance(l):
    m = average(l)

    return average([(x-m)**2 for x in l])


# Compute standard deviation
def standard_deviation(l):
    return variance(l)**0.5


# Launch
if __name__ == "__main__":
    op = OptionParser(usage="usage: %prog [options] experiment_name")

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

    op.add_option("-e", "--evaluate",
        dest="evaluate",
        default=False,
        action="store_true",
        help="prints segmentation metrics (-l required in current or previous run)")

    op.add_option("-a", "--all",
        dest="all",
        default=False,
        action="store_true",
        help="switches all previous options on")

    op.add_option("-c", "--check",
        dest="check",
        default=False,
        action="store_true",
        help="displays P, R and F1 for each fold (-bt required in current or previous run)")

    op.add_option("--bc3",
        dest="bc3",
        default=False,
        action="store_true",
        help="uses the annotated BC3 corpus for evaluation (not k-fold)")

    op.add_option("--bow",
        dest="bow",
        default=False,
        action="store_true",
        help="tests the impact of segmentation for a simple bag-of-words classification task")

    op.add_option("-m", "--maximum",
        dest="maximum",
        type="int",
        default=1000,
        help="maximum number of instances (defaults to 1000)")

    op.add_option("-f", "--folds",
        dest="folds",
        type="int",
        default=10,
        help="number of folds for cross-validation (defaults to 10)")

    op.add_option("-x", "--experiments",
        dest="experiments",
        default=False,
        action="store_true",
        help="displays the list of saved experiments")

    options, args = op.parse_args()
   
    if options.experiments:
        args = [""] if len(args) == 0 else args
    elif len(args) < 1:
        op.error("missing argument \"experiment_name\"")

    if options.all:
        options.save = options.train = options.build = options.patterns = options.label = options.evaluate = True

    main(options, args)
