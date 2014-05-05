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
from utility import float_to_string as f

# Input

WAPITI_TRAIN_FILE = "var/wapiti_train.tsv"
WAPITI_TEST_FILE = "var/wapiti_test.tsv"
WAPITI_GOLD_FILE = "var/wapiti_gold.tsv"
WAPITI_ORIGIN_FILE = "var/wapiti_origin.tsv"

# Output

PATTERN_FILE = "patterns.tsv"


def test_segment(opts, args):
    """
    Perform and evaluate a test segmentation 
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

        base_result_file = False if not opts.combine else "var/{0}/result_{1}".format(opts.combine, fold)

        timed_print("Training model...")
        subprocess.call("wapiti train -p {0} {1} {2}".format(pattern_file, train_file, model_file), shell=True)

        timed_print("Applying model on test data...")
        subprocess.call("wapiti label -m {0} -s -p {1} {2}".format(model_file, test_file, result_file) , shell=True)

        timed_print("Computing scores...")
        scores.append(evaluate_segmentation(
            result_file, gold_file, train_file, 
            base_result_file=base_result_file, smart_combine=opts.smart_combine
        ))

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
                        col = off_col + offset

                        out.write("*{0}:%x[{1},{2}]\n".format(i, off, col + 0)) # unigram 1
                        i += 1
                        out.write("*{0}:%x[{1},{2}]\n".format(i, off, col + 3)) # unigram 2
                        i += 1
                        out.write("*{0}:%x[{1},{2}]\n".format(i, off, col + 6)) # unigram 3
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, off, col + 0, col + 3)) # bigram 1
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, off, col + 3, col + 6)) # bigram 2
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]/%x[{1},{4}]\n".format(i, off, col + 0, col + 3, col + 6)) # trigram
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


def evaluate_segmentation(result_file, gold_file, train_file, limit=-1, base_result_file=False, smart_combine=True):
    """
    Compute scores for the current fold
    """

    d = "".join(data_to_list(train_file)) # training string
    g = "".join(data_to_list(gold_file, limit=limit)) # gold string
    t = "".join(data_to_list(result_file, limit=limit, label_position=-3)) # TextTiling string

    result_data = data_to_list(result_file, limit=limit, label_position=-2)

    if base_result_file:
        base_result_data = data_to_list(base_result_file, limit=limit, label_position=-2)
        result_data = data_to_list(result_file, limit=limit, label_position=-1)

        max_boundaries = int(t.count("T") * (float(len(g)) / len(t))) if smart_combine else -1

        r = combine_results(result_data, base_result_data, max_boundaries=max_boundaries) # result string
    else:
        r = "".join(data_to_list(result_file, limit=limit, label_position=-2)) # result string

    avg_g = float(len(g)) / (g.count("T") + 1) # average segment size (reference)
    avg_d = float(len(d)) / (d.count("T") + 1) # average segment size (training)

    k = int(avg_g / 2) # window size for WindowDiff

    b = ("T" + (int(math.floor(avg_d)) - 1) * "F") * int(math.ceil(float(len(d)) / int(math.floor(avg_d))))
    b = b[:len(g)] # baseline string

    ########################################

    # WindowDiff, Beeferman's Pk, Generalized Hamming Distance
    wdi_rs, bpk_rs, ghd_rs = compute_segmentation_scores(g, r, k)
    wdi_bl, bpk_bl, ghd_bl = compute_segmentation_scores(g, b, k)
    wdi_tt, bpk_tt, ghd_tt = compute_segmentation_scores(g, t, k)

    # accuracy
    acc_rs = accuracy(g, r)
    acc_bl = accuracy(g, b)
    acc_tt = accuracy(g, t)

    # precision, recall, f-measure
    pre_rs, rec_rs, f_1_rs = compute_ir_scores(g, r)
    pre_bl, rec_bl, f_1_bl = compute_ir_scores(g, b)
    pre_tt, rec_tt, f_1_tt = compute_ir_scores(g, t)

    ########################################

    return (
        acc_rs, acc_bl, acc_tt, 
        pre_rs, pre_bl, pre_tt, 
        rec_rs, rec_bl, rec_tt, 
        f_1_rs, f_1_bl, f_1_tt, 
        wdi_rs, wdi_bl, wdi_tt, 
        bpk_rs, bpk_bl, bpk_tt, 
        ghd_rs, ghd_bl, ghd_tt, 
        g.count("T"), b.count("T"), r.count("T"), t.count("T")
    )


def data_to_list(path, limit=-1, label_position=-1):
    """
    Extract labels from data file
    """

    s = []

    with codecs.open(path, "r") as file_contents:
        for raw_line in file_contents:
            if len(s) == limit:
                break

            line = raw_line.strip()

            if not line.startswith("# 0"):
                tokens = line.split()

                if len(tokens) > 0:
                    s.append(tokens[label_position].replace("S", "T").replace("O", "F"))

    return s


def compute_segmentation_scores(reference, results, k):
    """
    Compute WindowDiff, Beeferman's Pk and Generalized Hamming Distance
    """

    window_diff = float(windowdiff(reference, results, k, boundary="T")) / len(reference)
    bpk = pk(reference, results, boundary="T")
    generalized_hamming_distance = ghd(reference, results, boundary="T") / len(reference)

    return window_diff, bpk, generalized_hamming_distance


def compute_ir_scores(reference, results, label="T"):
    """
    Compute precision, recall and f-measure
    """

    precision = metrics.precision_score(list(reference), list(results), pos_label=label)
    recall = metrics.recall_score(list(reference), list(results), pos_label=label)
    f1 = (2.0 * (recall * precision)) / (recall + precision)

    return precision, recall, f1


def combine_results(results, base_results, max_boundaries=-1):
    """
    Combine results with those of a base classifier
    """
    
    scores = {}

    for i, result in enumerate(results):
        score = 0

        if base_results[i] == "T":
            score = 1
        elif result[:result.index("/")] == "T":
            score = float(result[result.index("/") + 1:])

        scores[i] = score

    sorted_indexes = sorted(scores, key=scores.get, reverse=True)
    indexes = [index for index, score in scores.iteritems() if score > 0.99]

    length = len(results)

    r = "F" * length

    for i, index in enumerate(sorted_indexes):
        r = r[:index] + "T" + r[index + 1:]
        if i == max_boundaries:
            break
    
    for index in indexes:
        r = r[:index] + "T" + r[index+1:]

    return r


def display_evaluations(scores):
    """
    Print out average scores in human-readable format
    """

    total = tuple(([0.0] * 3 * 7) + ([0] * 4)) 

    for s in scores:
        total = tuple(map(operator.add, s, total))

    print(scores_to_string(*tuple(x / len(scores) for x in total)))


def scores_to_string(
    ar, ab, at,
    pr, pb, pt,
    rr, rb, rt,
    fr, fb, ft,
    wr, wb, wt,
    br, bb, bt,
    gr, gb, gt,
    g_count, b_count, r_count, t_count
):
    """
    Convert scores to human-readable format
    """

    s  = "#            \tResult:\t\tBase.:\tDiff.:\t\tT.T.:\tDiff.:\n"
    s += "# WindowDiff:\t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(f(wr), f(wb), f(wr - wb), f(wt), f(wr - wt))
    s += "# pk:        \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(f(br), f(bb), f(br - bb), f(bt), f(br - bt))
    s += "# ghd:       \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(f(gr), f(gb), f(gr - gb), f(gt), f(gr - gt))
    s += "#\n"
    s += "#            \tResult:\t\tBase.:\tDiff.:\t\tT.T.:\tDiff.:\n"
    s += "# accuracy:  \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(f(ar), f(ab), f(ar - ab), f(at), f(ar - at))
    s += "#\n"
    s += "#            \tResult:\t\tBase.:\tDiff.:\t\tT.T.:\tDiff.:\n"
    s += "# precision: \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(f(pr), f(pb), f(pr - pb), f(pt), f(pr - pt))
    s += "# recall:    \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(f(rr), f(rb), f(rr - rb), f(rt), f(rr - rt))
    s += "# F1:        \t{0}%\t\t{1}%\t{2}%\t\t{3}\t{4}\n".format(f(fr), f(fb), f(fr - fb), f(ft), f(fr - ft))
    s += "#\n"
    s += "#            \tResult:\tBase.:\tT.T.:\n"
    s += "# seg. ratio:\tx{0}\tx{1}\tx{2}".format(
        f(float(r_count) / g_count), f(float(b_count) / g_count), f(float(t_count) / g_count)
    )

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
        default=False,
        action="store_true",
        help="use syntactic features")

    op.add_option("--stylistic",
        dest="stylistic",
        default=False,
        action="store_true",
        help="use stylistic features")

    op.add_option("--lexical",
        dest="lexical",
        default=False,
        action="store_true",
        help="use lexical features")

    op.add_option("--thematic",
        dest="thematic",
        default=False,
        action="store_true",
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

    op.add_option("--combine",
        dest="combine",
        default=False,
        type="string",
        help="base experiment name for combination")

    op.add_option("--smart_combine",
        dest="smart_combine",
        default=False,
        action="store_true",
        help="when combining, limit the number of boundaries based on average segment length in the training set")

    ########################################

    op.add_option("--test",
        dest="test",
        default=False,
        action="store_true",
        help="executes the test suite")

    ########################################
    
    opts, args = op.parse_args()

    if len(args) != 1 and not opts.test:
        op.error("missing argument \"experiment_name\"")

    return opts, args


if __name__ == "__main__":
    options, arguments = parse_args()

    if options.test:
        doctest.testmod() # unit testing
    else:
        test_segment(options, arguments)