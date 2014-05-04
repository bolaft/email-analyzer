#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    test_segmenter.py

:Authors:
    Soufian Salim (soufi@nsal.im)
"""

import codecs
import doctest
import operator
import linecache
import math
import os
import subprocess

from nltk.metrics.scores import accuracy
from nltk.metrics.segmentation import windowdiff, ghd, pk
from optparse import OptionParser
from sklearn import metrics
from utility import timed_print, compute_file_length

# Input

WAPITI_TRAIN_FILE = "var/wapiti_train.tsv"
WAPITI_TEST_FILE = "var/wapiti_test.tsv"
WAPITI_GOLD_FILE = "var/wapiti_gold.tsv"
WAPITI_ORIGIN_FILE = "var/wapiti_origin.tsv"

# Output

PATTERN_FILE = "patterns.tsv"

# Parameters

USE_SYNTACTIC = True
USE_STYLISTIC = True
USE_LEXICAL = True
USE_THEMATIC = True


def test_segment(opts, args):
    """
    Performs and evaluates a test segmentation 
    """

    dirpath = "var/{0}/".format(args[0])

    # Makes the folder if it does not exist already
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    timed_print("Building pattern file...")

    pattern_file = dirpath + PATTERN_FILE

    make_patterns(
        pattern_file,
        opts.window,
        syntactic=opts.syntactic, stylistic=opts.stylistic, lexical=opts.lexical, thematic=opts.thematic
    )

    timed_print("Splitting input data...")

    write_k_folds(
        opts.wapiti_train, opts.wapiti_test, opts.wapiti_gold, dirpath, 
        folds=opts.folds
    )

    scores = []

    for fold in xrange(opts.folds):
        timed_print("Fold {0}...".format(fold + 1))

        train_file = "{0}train_{1}".format(dirpath, fold)
        test_file = "{0}test_{1}".format(dirpath, fold)
        gold_file = "{0}gold_{1}".format(dirpath, fold)
        model_file = "{0}model_{1}".format(dirpath, fold)
        result_file = "{0}result_{1}".format(dirpath, fold)

        timed_print("Training model...")
        subprocess.call("wapiti train -p {0} {1} {2}".format(pattern_file, train_file, model_file), shell=True)

        timed_print("Applying model on test data...")
        subprocess.call("wapiti label -m {0} -s -p {1} {2}".format(model_file, test_file, result_file) , shell=True)

        timed_print("Computing scores...")
        scores.append(evaluate_segmentation(result_file, gold_file, train_file))

    display_evaluations(scores)


def make_patterns(
    path, 
    window=5, 
    syntactic=False, stylistic=False, lexical=False, thematic=False, 
    nb_stylistic=24, nb_lexical=1000, nb_thematic=1
):
    """
    Export a pattern file
    """

    with codecs.open(path, "w") as out:
        i = 1

        window_left = int(math.ceil(window - (window * 1.5)))
        window_right = window_left + window

        for off in xrange(window_left, window_right):

            off = str(off) if off < 1 else "+" + str(off)

            if syntactic:
                for offset in [0, 9]:
                    for off_col in xrange(0, 3):
                        base_col = off_col + offset

                        out.write("*{0}:%x[{1},{2}]\n".format(i, off, base_col + 0)) # unigram 1
                        i += 1
                        out.write("*{0}:%x[{1},{2}]\n".format(i, off, base_col + 3)) # unigram 2
                        i += 1
                        out.write("*{0}:%x[{1},{2}]\n".format(i, off, base_col + 6)) # unigram 3
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, off, base_col + 0, base_col + 3)) # bigram 1
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, off, base_col + 3, base_col + 6)) # bigram 2
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]/%x[{1},{4}]\n".format(i, off, base_col + 0, base_col + 3, base_col + 6)) # trigram
                        i += 1

                    out.write("\n")

            start_stylistic = 18
            start_lexical = start_stylistic + (nb_stylistic if stylistic else 0)
            start_thematic = start_lexical + (nb_lexical if lexical else 0)
            end = start_thematic + (nb_thematic if thematic else 0)

            for col in xrange(start_stylistic, start_lexical):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, col))
                i += 1

            for col in xrange(start_lexical, start_thematic):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, col))
                i += 1

            for col in xrange(start_thematic, end):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, col))
                i += 1

            out.write("\n")



def write_k_folds(source_train, source_test, source_gold, target_folder, folds=10):
    """
    Splits the data into train and test files for the specified number of folds
    """

    for fold in xrange(folds):
        with codecs.open("{0}/train_{1}".format(target_folder, fold), "w") as fold_train:
            with codecs.open("{0}/test_{1}".format(target_folder, fold), "w") as fold_test:
                with codecs.open("{0}/gold_{1}".format(target_folder, fold), "w") as fold_gold:
                
                    for i in xrange(compute_file_length(source_gold)):
                        if i % folds == fold:
                            fold_test.write(linecache.getline(source_test, i))
                            fold_gold.write(linecache.getline(source_gold, i))
                        else:
                            fold_train.write(linecache.getline(source_train, i))



# Evaluates the segmentation results
def evaluate_segmentation(result_file, gold_file, train_file, limit=-1):
    d = "".join(data_to_list(train_file)) # training data
    g = "".join(data_to_list(gold_file, limit=limit)) # gold string
    r = "".join(data_to_list(result_file, limit=limit, label_position=-2)) # result string
    t = "".join(data_to_list(result_file, limit=limit, label_position=-3)) # TextTiling string

    avg_g = float(len(g)) / (g.count("T") + 1) # average segment size (reference)
    avg_d = float(len(d)) / (d.count("T") + 1) # average segment size (training)

    k = int(avg_g / 2) # window size for WindowDiff

    b = ("T" + (int(math.floor(avg_d)) - 1) * "F") * int(math.ceil(float(len(d)) / int(math.floor(avg_d))))
    b = b[:len(g)] # baseline string

    # WindowDiff
    wdi_rs = (float(windowdiff(g, r, k, boundary="T")) / len(g)) * 100
    wdi_bl = (float(windowdiff(g, b, k, boundary="T")) / len(g)) * 100
    wdi_tt = (float(windowdiff(g, t, k, boundary="T")) / len(g)) * 100

    # Beeferman's Pk
    bpk_rs = (pk(g, r, boundary="T")) * 100
    bpk_bl = (pk(g, b, boundary="T")) * 100
    bpk_tt = (pk(g, t, boundary="T")) * 100

    # Generalized Hamming Distance
    ghd_rs = (ghd(g, r, boundary="T") / len(g)) * 100
    ghd_bl = (ghd(g, b, boundary="T") / len(g)) * 100
    ghd_tt = (ghd(g, t, boundary="T") / len(g)) * 100

    # accuracy
    acc_rs = accuracy(list(g), list(r)) * 100
    acc_bl = accuracy(list(g), list(b)) * 100
    acc_tt = accuracy(list(g), list(t)) * 100

    # precision, recall, f-measure
    pre_rs = metrics.precision_score(list(g), list(r), pos_label="T") * 100
    rec_rs = metrics.recall_score(list(g), list(r), pos_label="T") * 100
    f_1_rs = (2.0 * (rec_rs * pre_rs)) / (rec_rs + pre_rs)

    pre_bl = metrics.precision_score(list(g), list(b), pos_label="T") * 100
    rec_bl = metrics.recall_score(list(g), list(b), pos_label="T") * 100
    f_1_bl = (2.0 * (rec_bl * pre_bl)) / (rec_bl + pre_bl)
    
    pre_tt = metrics.precision_score(list(g), list(t), pos_label="T") * 100
    rec_tt = metrics.recall_score(list(g), list(t), pos_label="T") * 100
    f_1_tt = (2.0 * (rec_tt * pre_tt)) / (rec_tt + pre_tt)

    return acc_rs, acc_bl, acc_tt, pre_rs, pre_bl, pre_tt, rec_rs, rec_bl, rec_tt, f_1_rs, f_1_bl, f_1_tt, wdi_rs, wdi_bl, wdi_tt, bpk_rs, bpk_bl, bpk_tt, ghd_rs, ghd_bl, ghd_tt, g.count("T"), b.count("T"), r.count("T"), t.count("T")


def dec(f):
    return "{0:.2f}".format(f)


def data_to_list(path, limit=-1, label_position=-1):
    s = []

    with codecs.open(path, "r") as f:
        for line in f:
            if len(s) == limit:
                break
            if not line.startswith("#"):
                tokens = line.split()

                if len(tokens) > 0:
                    s.append(tokens[label_position].replace("O", "F").replace("S", "T"))

    return s



def display_evaluations(scores):
    total = (
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0, 0, 0, 0
    )

    for s in scores:
        total = tuple(map(operator.add, s, total))

    acc_rs, acc_bl, acc_tt, pre_rs, pre_bl, pre_tt, rec_rs, rec_bl, rec_tt, f_1_rs, f_1_bl, f_1_tt, wdi_rs, wdi_bl, wdi_tt, bpk_rs, bpk_bl, bpk_tt, ghd_rs, ghd_bl, ghd_tt, gcount, bcount, rcount, tcount = tuple(x/len(scores) for x in total)

    print(scores_to_string(
        acc_rs, acc_bl, acc_tt,
        pre_rs, pre_bl, pre_tt,
        rec_rs, rec_bl, rec_tt,
        f_1_rs, f_1_bl, f_1_tt,
        wdi_rs, wdi_bl, wdi_tt,
        bpk_rs, bpk_bl, bpk_tt,
        ghd_rs, ghd_bl, ghd_tt,
        gcount, bcount, rcount, tcount
    ))


def scores_to_string(
        acc_rs, acc_bl, acc_tt,
        pre_rs, pre_bl, pre_tt,
        rec_rs, rec_bl, rec_tt,
        f_1_rs, f_1_bl, f_1_tt,
        wdi_rs, wdi_bl, wdi_tt,
        bpk_rs, bpk_bl, bpk_tt,
        ghd_rs, ghd_bl, ghd_tt,
        gcount, bcount, rcount, tcount):

    s  = "#            \tResult:\t\tBase.:\tDiff.:\t\tT.T.:\tDiff.:\n"
    s += "# WindowDiff:\t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(wdi_rs), dec(wdi_bl), dec(wdi_rs - wdi_bl), dec(wdi_tt), dec(wdi_rs - wdi_tt))
    s += "# pk:        \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(bpk_rs), dec(bpk_bl), dec(bpk_rs - bpk_bl), dec(bpk_tt), dec(bpk_rs - bpk_tt))
    s += "# ghd:       \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(ghd_rs), dec(ghd_bl), dec(ghd_rs - ghd_bl), dec(ghd_tt), dec(ghd_rs - ghd_tt))
    s += "#\n"
    s += "#            \tResult:\t\tBase.:\tDiff.:\t\tT.T.:\tDiff.:\n"
    s += "# accuracy:  \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(acc_rs), dec(acc_bl), dec(acc_rs - acc_bl), dec(acc_tt), dec(acc_rs - acc_tt))
    s += "#\n"
    s += "#            \tResult:\t\tBase.:\tDiff.:\t\tT.T.:\tDiff.:\n"
    s += "# precision: \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(pre_rs), dec(pre_bl), dec(pre_rs - pre_bl), dec(pre_tt), dec(pre_rs - pre_tt))
    s += "# recall:    \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(rec_rs), dec(rec_bl), dec(rec_rs - rec_bl), dec(rec_tt), dec(rec_rs - rec_tt))
    s += "# F1:        \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(dec(f_1_rs), dec(f_1_bl), dec(f_1_rs - f_1_bl), dec(f_1_tt), dec(f_1_rs - f_1_tt))
    s += "#\n"
    s += "#            \tResult:\tBase.:\tT.T.:\n"
    s += "# seg. ratio:\tx{0}\tx{1}\tx{2}".format(dec(float(rcount) / gcount), dec(float(bcount) / gcount), dec(float(tcount) / gcount))

    return s


def parse_args():
    """
     Parse command line options and arguments 
    """

    op = OptionParser(usage="usage: %prog [options] experiment_name")

    ########################################

    op.add_option("-w", "--window",
        dest="window",
        type="int",
        default=5,
        help="window size for sequence labelling")

    ########################################

    op.add_option("--syntactic",
        dest="syntactic",
        default=USE_SYNTACTIC,
        action="store_false" if USE_SYNTACTIC else "store_true",
        help="use syntactic features")

    op.add_option("--stylistic",
        dest="stylistic",
        default=USE_STYLISTIC,
        action="store_false" if USE_STYLISTIC else "store_true",
        help="use stylistic features")

    op.add_option("--lexical",
        dest="lexical",
        default=USE_LEXICAL,
        action="store_false" if USE_LEXICAL else "store_true",
        help="use lexical features")

    op.add_option("--thematic",
        dest="thematic",
        default=USE_THEMATIC,
        action="store_false" if USE_THEMATIC else "store_true",
        help="use thematic features")

    ########################################

    op.add_option("--wapiti_train",
        dest="wapiti_train",
        default=WAPITI_TRAIN_FILE,
        type="string",
        help="input train file")

    op.add_option("--wapiti_test",
        dest="wapiti_test",
        default=WAPITI_TEST_FILE,
        type="string",
        help="input test file")

    op.add_option("--wapiti_gold",
        dest="wapiti_gold",
        default=WAPITI_GOLD_FILE,
        type="string",
        help="input gold file")

    op.add_option("--wapiti_origin",
        dest="wapiti_origin",
        default=WAPITI_ORIGIN_FILE,
        type="string",
        help="input origin file")

    ########################################

    op.add_option("-f", "--folds",
        dest="folds",
        type="int",
        default=10,
        help="number of folds for cross-validation (defaults to 10)")

    ########################################

    op.add_option("--test",
        dest="test",
        default=False,
        action="store_true",
        help="executes the test suite")

    ########################################
    
    opts, args = op.parse_args()

    if len(args) != 1:
        op.error("missing argument \"experiment_name\"")

    return opts, args


if __name__ == "__main__":
    options, arguments = parse_args()

    if options.test:
        doctest.testmod() # unit testing
    else:
        test_segment(options, arguments)