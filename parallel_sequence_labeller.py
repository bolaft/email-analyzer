#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    parallel_sequence_labeller.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    february 27, 2014 (creation)

:Description:
    converts tokens extracted from tagged emails into wapiti datafiles, then trains, labels and evaluates
    (see https://github.com/bolaft/email-analyzer)
"""

from progressbar import ProgressBar
from multiprocessing import Pool, Process
# from nltk.stem.wordnet import WordNetLemmatizer

# import nltk
import sys
import codecs
import os
import subprocess
import dataset_builder


# Wapiti
WAPITI_TRAIN_FILE = "var/train"
WAPITI_TEST_FILE = "var/test"
WAPITI_GOLD_FILE = "var/gold"
WAPITI_RESULT_FILE = "var/result"
WAPITI_MODEL_FILE = "var/model"
WAPITI_PATTERN_FILE = "var/patterns"

# Mallet
MALLET_DATA_FOLDER = "var/mallet/"

# Constants
limit = 100
train_limit = int(limit * 0.9)


# Main
def main(argv):
    source_folder = process_argv(argv)

    print("Converting %s to wapiti datafiles..." % source_folder)
    make_datafiles(source_folder)

    # print("Training model...")
    # subprocess.call("wapiti train -p " + WAPITI_PATTERN_FILE + " " + WAPITI_TRAIN_FILE + " " + WAPITI_MODEL_FILE, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

    # print("Applying model on test data...")
    # subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p " + WAPITI_TEST_FILE + " " + WAPITI_RESULT_FILE, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

    # print("Checking...")
    # subprocess.call("wapiti label -m " + WAPITI_MODEL_FILE + " -p -c " + WAPITI_GOLD_FILE, shell=True)


# Converts email tagged files to Mallet data format
def make_mallet_data(source_folder):
    progress = ProgressBar()

    for filename in progress(os.listdir(source_folder)):
        for i, line in enumerate(tuple(codecs.open(source_folder + filename, "r", "utf-8"))):
            line = line.strip()

            if not line.startswith("#"):
                tokens = line.split()
                if len(tokens) > 1:
                    label = tokens.pop(0)

                    filepath = MALLET_DATA_FOLDER + label + "/" + filename + ".txt"

                    with codecs.open(filepath, "a", "utf-8") as out:
                        sentence = " ".join(tokens)
                        out.write(sentence)


# Writes wapiti datafiles
def make_datafiles(source_folder):
    print("Making datafiles...")

    train = True
    largest_sentence = 0

    progress = ProgressBar(maxval=limit).start()

    # wnl = WordNetLemmatizer()

    with codecs.open(WAPITI_TRAIN_FILE, "w", "utf-8") as train_out:
        with codecs.open(WAPITI_TEST_FILE, "w", "utf-8") as test_out:
            with codecs.open(WAPITI_GOLD_FILE, "w", "utf-8") as gold_out:
                for i, filename in enumerate(os.listdir(source_folder)):
                    if i == limit:
                        break

                    for line in tuple(codecs.open(source_folder + filename, "r", "utf-8")):
                        line = line.strip()

                        if not line.startswith("#"):
                            tokens = line.split()
                            if len(tokens) > 1:
                                label = tokens.pop(0)

                                if len(tokens) > largest_sentence:
                                    largest_sentence = len(tokens)

                pool = Pool()
                for i, filename in enumerate(os.listdir(source_folder)):
                    pool.apply_async(compute_stuff, [progress, i, source_folder, filename, largest_sentence, train_out, test_out, gold_out])

    progress.finish()
    make_patterns(largest_sentence)


def compute_stuff(progress, i, source_folder, filename, largest_sentence, train_out, test_out, gold_out):
    progress.update(i)
    train = True
    
    if i >= limit:
        return
    if i >= train_limit:
        train = False

    for line in tuple(codecs.open(source_folder + filename, "r", "utf-8")):
        line = line.strip()

        if not line.startswith("#"):
            tokens = line.split()
            if len(tokens) > 1:
                label = tokens.pop(0)

                for j in xrange(0, largest_sentence):
                    if len(tokens) > j:
                        obs = tokens[j].lower() + "\t"
                    else:
                        obs = "null\t"

                    if train:
                        train_out.write(obs)
                    else:
                        test_out.write(obs)
                        gold_out.write(obs)

                label = "T" if label == "B" or label == "BE" else "F"

                if train:
                    train_out.write(label + "\n")
                else:
                    gold_out.write(label + "\n")
                    test_out.write("\n")

    if train:
        train_out.write("\n")
    else:
        test_out.write("\n")
        gold_out.write("\n")

# Writes wapiti datafiles (vectorial approach)
def make_vector_datafiles(data, vector):
    print("Making vectorized datafiles...")

    with codecs.open(WAPITI_TRAIN_FILE, "w", "utf-8") as train_out:
        with codecs.open(WAPITI_TEST_FILE, "w", "utf-8") as test_out:
            with codecs.open(WAPITI_GOLD_FILE, "w", "utf-8") as gold_out:
                out = [train_out]
                progress = ProgressBar()

                for i, (ngrams, label) in enumerate(progress(data)):
                    if i == limit:
                        break

                    if label == None:
                        for chan in out:
                            chan.write("\n")
                        continue

                    if i == train_limit:
                        out = [test_out, gold_out]

                    obs = ""

                    for ngram in vector:
                        if ngram in ngrams:
                            obs += "1 "
                        else:
                            obs += "0 "

                    for chan in out:
                        chan.write(obs)
                        chan.write("T\n" if label == "B" or label == "BE" else "F\n")

    make_vector_patterns(vector)


# Computes and writes patterns
def make_patterns(largest_sentence):
    print("Making patterns...")

    progress = ProgressBar()
    with codecs.open(WAPITI_PATTERN_FILE, "w", "utf-8") as out:
        i = 1
        for col in progress(range(0, largest_sentence)):
            for off in xrange(-1, 2):
                off = str(off) if off < 1 else "+" + str(off)

                # unigram
                out.write("*" + str(i) + ":%x[" + off + "," + str(col) + "]\n")
                i += 1

                # bigram
                if col < largest_sentence - 1:
                    out.write("*" + str(i) + ":%x[" + off + "," + str(col) + "]/%x[" + off + "," + str(col + 1) + "]\n")
                    i += 1

                # trigram
                if col < largest_sentence - 2:
                    out.write("*" + str(i) + ":%x[" + off + "," + str(col) + "]/%x[" + off + "," + str(col + 1) + "]/%x[" + off + "," + str(col + 2) + "]\n")
                    i += 1

            out.write("\n")


# Computes and writes patterns (vectorial approach)
def make_vector_patterns(vector):
    print("Making vectorized patterns...")

    progress = ProgressBar()
    with codecs.open(WAPITI_PATTERN_FILE, "w", "utf-8") as out:
        i = 0
        for col in progress(range(0, len(vector))):
            for off in xrange(-2, 3):
                i += 1
                col = str(col)
                off = str(off) if off < 1 else "+" + str(off)

                out.write("b" + str(i) + ":%t[" + off + "," + col + ",\"^1$\"]\n")
            out.write("\n")


# Extracts data from tagged emails (vectorial approach)
def extract_data(source_folder):
    data = []
    vector = set([]) # set of all distinct ngrams in corpus

    print("Extracting data from %s..." % source_folder)

    progress = ProgressBar()

    for i, filename in enumerate(progress(os.listdir(source_folder))):
        if i == 1000:
            break
        with codecs.open(source_folder + filename, "r", "utf-8") as f:
            for line in f:                
                if not line.startswith("#"):
                    tokens = line.split()

                    if len(tokens) > 1:
                        label = tokens.pop(0)
                        ngrams = set(tokens + extract_bigrams(tokens))
                        vector.update(ngrams)
                        data.append((ngrams, label))

        vector = set(vector)
        data.append((None, None))

    return data, vector


# Extracts bigrams
def extract_bigrams(tokens):
    return [x + " " + y for x, y in zip(tokens, tokens[1:])]


# Process argv
def process_argv(argv):
    if len(argv) != 2:
        print("Usage: " + argv[0] + " <source folder> <target file>")
        sys.exit()

    # adding a "/" to the dirpath if not present
    source_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

    if not os.path.isdir(source_folder):
        sys.exit(source_folder + " is not a directory")

    return source_folder


# Launch
if __name__ == "__main__":
    main(sys.argv)
