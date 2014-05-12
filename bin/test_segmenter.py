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
import os
import subprocess

from dataset_builder import WAPITI_TRAIN_FILE, WAPITI_TEST_FILE, WAPITI_GOLD_FILE, WAPITI_ORIGIN_FILE
from math import ceil
from nltk.metrics.scores import accuracy
from nltk.metrics.segmentation import windowdiff, ghd, pk
from optparse import OptionParser
from progressbar import ProgressBar
from sklearn import metrics
from utility import timed_print, compute_file_length
from utility import float_to_string as f


# output

PATTERN_FILE = "patterns"

# var

VAR_FOLDER = "./../var/"


def test_segment(opts, args):
    """
    Perform and evaluate a test segmentation 
    """

    experiment_folder = "{0}experiments/{1}/".format(VAR_FOLDER, args[0])
    folds_folder = "{0}{1}_fold/".format(VAR_FOLDER, opts.folds)

    # # makes the folder if it does not exist already
    # if not os.path.exists(experiment_folder):
    #     os.makedirs(experiment_folder)

    # timed_print("Building pattern file...")

    # pattern_file = experiment_folder + PATTERN_FILE

    # make_patterns(
    #     pattern_file,
    #     opts.window,
    #     syntactic=opts.syntactic, stylistic=opts.stylistic, lexical=opts.lexical, thematic=opts.thematic
    # )

    # timed_print("Splitting input data...")

    # write_k_folds(
    #     opts.wapiti_train, opts.wapiti_test, opts.wapiti_gold, opts.wapiti_origin,
    #     folds_folder, 
    #     folds=opts.folds
    # )

    scores = []

    for fold in xrange(opts.folds):
        timed_print("Fold {0}...".format(fold + 1))

        train_file = "{0}train_{1}".format(experiment_folder, fold)
        test_file = "{0}test_{1}".format(experiment_folder, fold)
        gold_file = "{0}gold_{1}".format(experiment_folder, fold)
        model_file = "{0}model_{1}".format(experiment_folder, fold)
        result_file = "{0}result_{1}".format(experiment_folder, fold)
        print result_file
        print gold_file
        base_result_file = False if not opts.combine else "../var/{0}/result_{1}".format(opts.combine, fold)

        # timed_print("Training model...")

        # subprocess.call("wapiti train -p {0} {1} {2}".format(pattern_file, train_file, model_file), shell=True)

        # timed_print("Applying model on test data...")

        # subprocess.call("wapiti label -m {0} -s -p {1} {2}".format(model_file, test_file, result_file) , shell=True)

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

        window_left = int(ceil(window - (window * 1.5)))
        window_right = window_left + window

        for offset in xrange(window_left, window_right):

            x = str(offset) if offset < 1 else "+" + str(offset)

            if syntactic:
                for group_offset in [0, 9]:
                    for type_offset in xrange(0, 3):
                        y = type_offset + group_offset

                        # n-grams

                        out.write("*{0}:%x[{1},{2}]\n".format(i, x, y + 0)) # uni 1
                        i += 1
                        out.write("*{0}:%x[{1},{2}]\n".format(i, x, y + 3)) # uni 2
                        i += 1
                        out.write("*{0}:%x[{1},{2}]\n".format(i, x, y + 6)) # uni 3
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, x, y + 0, y + 3)) # bi 1
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]\n".format(i, x, y + 3, y + 6)) # bi 2
                        i += 1
                        out.write("*{0}:%x[{1},{2}]/%x[{1},{3}]/%x[{1},{4}]\n".format(i, x, y + 0, y + 3, y + 6)) # tri
                        i += 1

                    out.write("\n")

            start_stylistic = 18
            start_lexical = start_stylistic + (nb_stylistic if stylistic else 0)
            start_thematic = start_lexical + (nb_lexical if lexical else 0)
            end = start_thematic + (nb_thematic if thematic else 0)

            for y in xrange(start_stylistic, start_lexical):
                out.write("*{0}:%x[{1},{2}]\n".format(i, x, y))
                i += 1

            for y in xrange(start_lexical, start_thematic):
                out.write("*{0}:%x[{1},{2}]\n".format(i, x, y))
                i += 1

            for y in xrange(start_thematic, end):
                out.write("*{0}:%x[{1},{2}]\n".format(i, x, y))
                i += 1

            out.write("\n")


def write_k_folds(source_train, source_test, source_gold, source_origin, target_folder, folds=10):
    """
    Splits the data into train and test files for the specified number of folds
    """

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    filenames = os.listdir(target_folder)

    progress = ProgressBar()

    for fold in progress(xrange(folds)):
        fold_train = fold_test = fold_gold = fold_origin = False

        if not "train_{0}".format(fold) in filenames:
            fold_train = codecs.open("{0}/train_{1}".format(target_folder, fold), "w")
        if not "test_{0}".format(fold) in filenames:
            fold_test = codecs.open("{0}/test_{1}".format(target_folder, fold), "w")
        if not "gold_{0}".format(fold) in filenames:
            fold_gold = codecs.open("{0}/gold_{1}".format(target_folder, fold), "w")
        if not "origin_{0}".format(fold) in filenames:
            fold_origin = codecs.open("{0}/origin_{1}".format(target_folder, fold), "w")

        for i in xrange(compute_file_length(source_gold)):
            if i % folds == fold:
                if fold_gold:
                    fold_gold.write(linecache.getline(source_gold, i))
                if fold_test:
                    fold_test.write(linecache.getline(source_test, i))
                if fold_origin:
                    fold_origin.write(linecache.getline(source_origin, i))
            else:
                if fold_train:
                    fold_train.write(linecache.getline(source_train, i))


def evaluate_segmentation(result_file, gold_file, train_file, limit=-1, base_result_file=False, smart_combine=True):
    """
    Compute scores for the current fold
    """

    d = data_to_list(train_file) # training label list
    g = data_to_list(gold_file, limit=limit) # gold label list
    t = data_to_list(result_file, limit=limit, label_position=-3) # TextTiling label list

    result_data = data_to_list(result_file, limit=limit, label_position=-2)

    if base_result_file:
        base_result_data = data_to_list(base_result_file, limit=limit, label_position=-2)
        result_data = data_to_list(result_file, limit=limit, label_position=-1)

        max_boundaries = int(d.count("T") * (float(len(g)) / len(d))) if smart_combine else -1

        r = combine_results(result_data, base_result_data, max_boundaries=max_boundaries) # result label list
    else:
        r = data_to_list(result_file, limit=limit, label_position=-2) # result label list

    avg_g = float(len(g)) / (g.count("T") + 1) # average segment size (reference)
    avg_d = float(len(d)) / (d.count("T") + 1) # average segment size (training)

    k = int(avg_g / 2) # window size for WindowDiff

    b = list("T" + (int(ceil(avg_d) - 1) * "F")) * int(float(len(g)) / avg_d)
    b = b[:len(g)] # baseline label list

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

            if not line.startswith("#"):
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

    precision = metrics.precision_score(reference, results, pos_label=label)
    recall = metrics.recall_score(reference, results, pos_label=label)
    f1 = (2.0 * (recall * precision)) / (recall + precision)

    return precision, recall, f1


def combine_results(results, base_results, max_boundaries=-1, min_confidence=0.75):
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

        if score >= min_confidence:
            scores[i] = score

    sorted_indexes = sorted(scores, key=scores.get, reverse=True)

    length = len(results)

    r = "F" * length

    for index in sorted_indexes[:max_boundaries]:
        r = r[:index] + "T" + r[index + 1:]

    return list(r)


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
    s += "# seg. ratio:\t{0}%\t{1}%\t{2}%".format(
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

    if not opts.syntactic and not opts.stylistic and not opts.lexical and not opts.thematic:
        op.error("at least one feature set must be specified")

    return opts, args


if __name__ == "__main__":
    options, arguments = parse_args()

    if options.test:
        doctest.testmod() # unit testing
    else:
        test_segment(options, arguments)