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
import math
import os

from optparse import OptionParser
from progressbar import ProgressBar
from utility import timed_print

# Input

TRAIN_FILE = "var/train.tsv"
TEST_FILE = "var/test.tsv"
GOLD_FILE = "var/gold.tsv"
ORIGIN_FILE = "var/origin.tsv"

# Output

PATTERN_FILE = "var/patterns.tsv"

# Parameters

USE_SYNTACTIC = True
USE_STYLISTIC = True
USE_LEXICAL = True
USE_THEMATIC = True


def test_segment(opts, args):
    """
    Performs and evaluates a test segmentation 
    """

    dirpath = "var/%s/".format(args[0])

    # Makes the folder if it does not exist already
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    timed_print("Building pattern file...")

    make_patterns(
        opts.pattern_file,
        opts.window,
        syntactic=opts.syntactic, stylistic=opts.stylistic, lexical=opts.lexical, thematic=opts.thematic
    )


def make_patterns(path, window=5, syntactic=False, stylistic=False, lexical=False, thematic=False, nb_stylistic=24, nb_lexical=1000, nb_thematic=1):
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
            start_lexical = start_stylistic + nb_stylistic
            start_thematic = start_lexical + nb_lexical

            for col in xrange(start_stylistic, start_lexical):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, col))
                i += 1

            for col in xrange(start_lexical, start_thematic):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, col))
                i += 1

            for col in xrange(start_thematic, start_thematic + nb_thematic):
                out.write("*{0}:%x[{1},{2}]\n".format(i, off, col))
                i += 1

            out.write("\n")


def parse_args():
    """
     Parse command line options and arguments 
    """

    op = OptionParser(usage="usage: %prog [options]")

    ########################################

    op.add_option("-w", "--window",
        dest="window",
        type="int",
        default=5,
        help="window size for sequence labelling")

    ########################################

    op.add_option("--train_file",
        dest="train_file",
        default=TRAIN_FILE,
        type="string",
        help="input train file")

    op.add_option("--test_file",
        dest="test_file",
        default=TEST_FILE,
        type="string",
        help="input test file")

    op.add_option("--gold_file",
        dest="gold_file",
        default=GOLD_FILE,
        type="string",
        help="input gold file")

    op.add_option("--origin_file",
        dest="origin_file",
        default=ORIGIN_FILE,
        type="string",
        help="input origin file")

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

    op.add_option("--pattern_file",
        dest="pattern_file",
        default=PATTERN_FILE,
        type="string",
        help="output pattern file")

    ########################################

    op.add_option("--test",
        dest="test",
        default=False,
        action="store_true",
        help="executes the test suite")

    ########################################

    return op.parse_args()


if __name__ == "__main__":
    options, arguments = parse_args()

    if options.test:
        doctest.testmod() # unit testing
    else:
        test_segment(options, arguments)