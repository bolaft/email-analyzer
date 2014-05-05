#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    dataset_builder.py

:Authors:
    Soufian Salim (soufi@nsal.im)
"""

import codecs
import doctest
import math
import os

from nltk import pos_tag
from nltk.stem.wordnet import WordNetLemmatizer
from optparse import OptionParser
from progressbar import ProgressBar
from utility import timed_print, compute_file_length

# Default parameters

OCCURRENCE_THRESHOLD_QUOTIENT = 0.075 / 150 # words that appear less than (quotient * total tokens) times are ignored

# Default paths

DATA_FOLDER = "../data/email.message.tagged/" # folder where heuristically labelled emails are stored
TT_FOLDER = "../data/TT/ubuntu-users/" # folder where emails labelled by text-tiling are stored
NGRAMS_FILE = "var/ngrams" # file containing relevant ngrams

WAPITI_TRAIN_FILE = "var/wapiti_train.tsv"
WAPITI_TEST_FILE = "var/wapiti_test.tsv"
WAPITI_GOLD_FILE = "var/wapiti_gold.tsv"
WAPITI_ORIGIN_FILE = "var/wapiti_origin.tsv"

WEKA_ARFF_FILE = "var/weka.arff"

# Constants

LABELS = ["T", "F"]


def build_datasets(opts):
    """
    Build a datasets
    """
    
    # filenames
    data_folder_files = os.listdir(opts.data_folder)

    ########################################
    
    timed_print("extracting ngrams from list...")

    ngrams = [ngram.strip() for ngram in codecs.open(opts.ngrams_file, "r").readlines()]

    print("# {0} ngrams extracted".format(len(ngrams)))

    ########################################

    timed_print("computing maximum file length...")

    max_file_length = compute_max_file_length(
        [opts.data_folder + filename for filename in data_folder_files]
    )

    print("# maximum file length: {0} lines".format(max_file_length))

    ########################################

    timed_print("selecting source files...")

    selected_files = select_data_files(
        opts.data_folder,
        data_folder_files,
        max_file_length=max_file_length,
        only_initial=opts.only_initial, only_utf8=opts.only_utf8, only_text_plain=opts.only_text_plain
    )

    print("# {0} source files selected".format(len(selected_files)))

    ########################################
    
    # number of lines in datasets
    instances = 0

    # names of numeric stylistic features (that require an average value for discretization)
    numeric_feature_names = [
        "position",
        "number_of_tokens",
        "number_of_chars",
        "number_of_quote_symbols",
        "average_token_length",
        "proportion_of_uppercase_chars",
        "proportion_of_alphabetic_chars",
        "proportion_of_numeric_chars"
    ]

    # sums of stylistic features values
    stylistic_features_sums = {f:0.0 for f in numeric_feature_names}

    token_counter = {}
    total_token_count = 0

    ########################################

    timed_print("computing stylistic features' sums, counting tokens, counting file lengths...")
    
    progress = ProgressBar()

    for file_data in progress(parse_data_files(
        opts.data_folder, opts.text_tiling_folder, selected_files
    )):
        for line, tokens, label, tt_label, line_number, total_lines in file_data:
            # updating stylistic features' sums
            stylistic_features_sums, instances = update_stylistic_features_sums(
                stylistic_features_sums, instances, line, tokens, line_number, total_lines
            )

            # updating the token counter
            token_counter, total_token_count = update_token_count(
                token_counter, total_token_count, tokens
            )

    ########################################

    timed_print("computing average stylistic features...")

    progress = ProgressBar()

    average_stylistic_features = {f:stylistic_features_sums[f] / instances for f in progress(numeric_feature_names)}

    ########################################

    timed_print("computing features...")

    wnl = WordNetLemmatizer()

    min_occurrences = total_token_count * opts.occurrence_threshold_quotient

    # datasets format:
    # [ # one email
    #   [ # one message
    #       ( # one line
    #           label, 
    #           line, 
    #           [(value, name, type), ...]
    #       ),
    #       ...
    #   ],
    #   ...
    # ]
    
    datasets = []

    progress = ProgressBar()

    for file_data in progress(parse_data_files(
        opts.data_folder, opts.text_tiling_folder, selected_files
    )):
        dataset = []
        
        for line, tokens, label, tt_label, line_number, total_lines in file_data:
            # tokens with required frequency
            relevant_tokens = [t for t in tokens if token_counter[t.lower()] > min_occurrences]

            # [tag]
            tags = [tag for token, tag in  pos_tag(tokens)]

            # [(token, lemma, tag)]
            tokens_lemmas_tags = [
                (token, wnl.lemmatize(token.lower(), "v" if tag.startswith("V") else "n"), tag)
                    for token, tag in pos_tag(relevant_tokens)
            ]

            # building syntactic features (hinge tokens)
            syntactic_features = make_syntactic_features(tokens_lemmas_tags)

            # building stylistic features (hand-written features)
            stylistic_features = make_stylistic_features(line, tokens, tags, line_number, total_lines)

            # building lexical features (ngrams)
            lexical_features = make_lexical_features(ngrams, line)

            # building thematic features (Text Tiling)
            thematic_features = [(tt_label, "text_tiling_boundary", "{S,O}")]

            dataset.append((
                label,
                line,
                syntactic_features + stylistic_features + lexical_features + thematic_features
            ))

        datasets.append(dataset)
    
    ########################################

    timed_print("exporting Wapiti datafiles...")

    export_wapiti_datafiles(
        datasets, 
        average_stylistic_features, 
        opts.wapiti_train_file, opts.wapiti_test_file, opts.wapiti_gold_file, opts.wapiti_origin_file
    )
    
    ########################################

    timed_print("exporting Weka .arff file...")

    export_weka_arff(datasets, opts.weka_arff_file, LABELS)


def export_weka_arff(datasets, arff_file, labels):
    """
    Exports the dataset to a Weka ARFF file
    """

    with codecs.open(arff_file, "w") as out:
        # write header
        out.write("@relation segmenter\n\n")

        # writing attributes
        features_0 = datasets[0][0][2] # first line's features
        attributes = [(name, attribute_type) for value, name, attribute_type in features_0]

        for feature_name, feature_type in attributes:
            out.write("@attribute {0} {1}\n".format(feature_name, feature_type))

        # writing labels
        out.write("@attribute class {")
        out.write(",".join(labels))
        out.write("}\n\n")

        # writing data
        out.write("@data\n")

        for dataset in datasets:
            for label, line, features in dataset:
                for i, (raw_value, name, attribute_type) in enumerate(features):
                    if attribute_type == "{TRUE, FALSE}": 
                        # {TRUE, FALSE}
                        value = "TRUE" if raw_value else "FALSE" 
                    elif attribute_type == "string": 
                        # strings are quoted and quotes are escaped
                        value = "'{0}'".format(raw_value.replace("'", "\\'")) 
                    else: 
                        # other values are cast to string
                        value = str(raw_value) 
                    
                    out.write("{0},".format(value))

                    if i == len(features) - 1:
                        out.write(label)

                out.write("\n")


def export_wapiti_datafiles(datasets, averages, train_file, test_file, gold_file, origin_file):
    """
    Exports wapiti train, test and gold files
    """
    
    with codecs.open(train_file, "w") as train_out:
        with codecs.open(test_file, "w") as test_out:
            with codecs.open(gold_file, "w") as gold_out:
                with codecs.open(origin_file, "w") as origin_out:

                    for dataset in datasets:
                        for label, line, features in dataset:
                            for value, name, attribute_type in features:
                                for out in [train_out, test_out]:
                                    out.write("{0}\t".format(
                                        # wapiti requires discrete features only
                                        discretize_feature(averages, name, value) 
                                    ))

                            for out in [train_out, gold_out]:
                                # writes label to train and gold
                                out.write(label)

                            # writes the original line
                            origin_out.write(line)

                            for out in [train_out, test_out, gold_out, origin_out]:
                                # newline to all files
                                out.write("\n")

                        # (prevents multiple empty lines)
                        if len(dataset) > 0:
                            for out in [train_out, test_out, gold_out, origin_out]:
                                # empty line in  between message sequences
                                out.write("\n")


def make_syntactic_features(tokens_lemmas_tags):
    """
    Featurize first and last three tokens' corresponding surface forms, lemmas and parts-of-speech
    """

    features = []

    for position in [0, 1, 2, -3, -2, -1]:
        if position >= len(tokens_lemmas_tags) or position < len(tokens_lemmas_tags) * -1:
            features += [
                ("NULL.TOKEN", "hinge_{0}_{1}".format(position, form), "string") 
                    for form in ["token", "lemma", "tag"]
            ]
        else:
            token, lemma, tag = tokens_lemmas_tags[position]

            features += [
                (value, "hinge_{0}_{1}".format(position, form), "string") 
                    for form, value in [("token", token), ("lemma", lemma), ("tag", tag)]
            ]

    return features


def make_lexical_features(ngrams, line):
    """
    Featurize the presence or absence of relevant ngrams
    """

    return [
        (True, "ngram_{0}".format(i + 1), "{TRUE, FALSE}") 
        if line.count(ngram) > 0 
        else (False, "ngram_{0}".format(i + 1), "{TRUE, FALSE}") 
        for i, ngram in enumerate(ngrams)
    ]


def make_stylistic_features(line, tokens, tags, line_number, total_lines):
    """
    Featurize line and tokens' aspect
    """

    features = []

    line_lower = line.lower()
   
    # position
    features.append((
        float(line_number) / total_lines, "position", "integer"
    ))

    # number of tokens
    features.append((
        len(tokens), "number_of_tokens", "integer"
    ))

    # number of chars
    features.append((
        len(line), "number_of_chars", "integer"
    ))

    # number of quote symbols
    features.append((
        line.count(">"), "number_of_quote_symbols", "integer"
    ))

    # average token length
    features.append((
        sum(map(len, tokens)) / len(tokens), "average_token_length", "real"
    ))

    # proportion of uppercase chars
    features.append((
        float(sum(x.isupper() for x in line)) / len(line), "proportion_of_uppercase_chars", "real"
    ))

    # proportion of alphabetic chars
    features.append((
        float(sum(x.isalpha() for x in line)) / len(line), "proportion_of_alphabetic_chars", "real"
    ))

    # proportion of numeric chars
    features.append((
        float(sum(x.isdigit() for x in line)) / len(line), "proportion_of_numeric_chars", "real"
    ))

    # has question mark
    features.append((
        line.count("?") > 0, "has_question_mark", "{TRUE, FALSE}"
    ))

    # ends with question mark
    features.append((
        line.endswith("?"), "ends_with_question_mark", "{TRUE, FALSE}"
    ))

    # has colon
    features.append((
        line.count(":") > 0, "has_colon", "{TRUE, FALSE}"
    ))

    # ends with colon
    features.append((
        line.endswith(":"), "ends_with_colon", "{TRUE, FALSE}"
    ))

    # has semicolon
    features.append((
        line.count(";") > 0, "has_semicolon", "{TRUE, FALSE}"
    ))

    # ends with semicolon
    features.append((
        line.endswith(";"), "ends_with_semicolon_mark", "{TRUE, FALSE}"
    ))

    # has early punctuation
    first_punctuation_position = 999

    for i, token in enumerate(tokens):
        if token in [".", ";", ":", "?", "!", ","]:
            first_punctuation_position = i

    features.append((
        first_punctuation_position < 4, "has_early_punctuation", "{TRUE, FALSE}"
    ))

    # has interrogating word
    features.append((
        not set([token.lower() for token in tokens]).isdisjoint(
            ["who", "when", "where", "what", "which", "what", "how"]
        ), "has_interrogating_word", "{TRUE, FALSE}"
    ))

    # starts with interrogating form
    features.append((
        tokens[0].lower() in [
            "who", "when", "where", "what", "which", "what", "how", 
            "is", "are", "am", "will", "do", "does", "have", "has"
        ], "starts_with_interrogating_form", "{TRUE, FALSE}"
    ))

    # first verb form
    first_verb_form = "NO_VERB"

    for tag in tags:
        if tag in ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]:
            first_verb_form = tag
            break

    features.append((
        first_verb_form, "first_verb_form", "string"
    ))

    # first personal pronoun
    first_personal_pronoun = "NO_PERSONAL_PRONOUN"

    for token in tokens:
        if token.lower() in ["i", "you", "he", "she", "we", "they"]:
            first_personal_pronoun = token.upper()

    features.append((
        first_personal_pronoun, "first_personal_pronoun", "string"
    ))

    # contains modal word
    features.append((
        any(ngram in line_lower for ngram in [
            "may", "must", "musn" "shall", "shan" "will", "might", "should", "would", "could"
        ]), "contains_modal_word", "{TRUE, FALSE}"
    ))

    # contains plan phrase
    features.append((
        any(ngram in line_lower for ngram in [
            "i will", "i am going to", "we will", "we are going to", "i plan to", "we plan to"
        ]), "contains_plan_phrase", "{TRUE, FALSE}"
    ))

    # contains first person mark
    features.append((
        any(ngram in line_lower for ngram in [
            "me", "us", "i", "we", "my", "mine", "myself", "ourselves"
        ]), "contains_first_person_mark", "{TRUE, FALSE}"
    ))

    # contains second person mark
    features.append((
        any(ngram in line_lower for ngram in [
            "you", "your", "yours", "yourself", "yourselves"
        ]), "contains_second_person_mark", "{TRUE, FALSE}"
    ))

    # contains third person mark
    features.append((
        any(ngram in line_lower for ngram in [
            "he", "she", "they", "his", "their", "hers", "him", "her", "them"
        ]), "contains_third_person_mark", "{TRUE, FALSE}"
    ))

    return features


def update_stylistic_features_sums(sums, instances, line, tokens, line_number, total_lines):
    """
    Update stylistic features' sums
    """

    sums["position"] += float(line_number) / total_lines
    sums["number_of_tokens"] += len(tokens)
    sums["number_of_chars"] += len(line)
    sums["number_of_quote_symbols"] += line.count(">")
    sums["average_token_length"] += sum(map(len, tokens)) / len(tokens)
    sums["proportion_of_uppercase_chars"] += float(sum(char.isupper() for char in line)) / len(line)
    sums["proportion_of_alphabetic_chars"] += float(sum(char.isalpha() for char in line)) / len(line)
    sums["proportion_of_numeric_chars"] += float(sum(char.isdigit() for char in line)) / len(line)

    return sums, instances + 1


def update_token_count(counter, total, tokens):
    """
    Updates a dictionary of token counts
    """

    for token in tokens:
        token_lower = token.lower()
        counter[token_lower] = counter[token_lower] + 1 if token_lower in counter else 1

    return counter, total + len(tokens)


def parse_data_files(folder, text_tiling_folder, filenames):
    """
    Returns tokens, line number and total number of lines for each file in the given set 
    """

    data = []

    for filename in filenames:
        line_data = []

        lines = codecs.open(folder + filename, "r").readlines()
        tt_lines = codecs.open(text_tiling_folder + filename, "r").readlines()

        line_number = 0 # position of the line in the message

        for raw_line in lines:
            line = raw_line.strip()
            tokens = line.split()

            if len(tokens) > 0 and tokens[0] == "#":
                continue # ignore comments

            line_number += 1 # comments don't count towards line number, but empty lines do

            if len(tokens) < 2:
                continue # ignore empty lines

            # original labels: "B", "BE", "I" or "E" (BIO)
            raw_label = tokens.pop(0)

            # binary labels: "T" or "F" (isBoundary)
            label = "T" if raw_label == "B" or raw_label == "BE" else "F"

            # Text Tiling labels: "S", "O" (isBoundary)
            tt_label = tt_lines[line_number - 1].strip().split().pop(0) if line_number - 1 < len(tt_lines) else "O"

            line_data.append((
                line, tokens, label, tt_label, line_number, compute_file_length(folder + filename, ignore_empty=True)
            ))

        data.append(line_data)

    return data


def discretize_feature(averages, name, value):
    """
    Transforms a feature value into a discrete string
    """

    if name in averages:
        average_value = averages[name]

        value = float(value)
        tier = "high"

        if value > average_value * 1.5:
            tier = "highest"
        elif value < average_value:
            tier = "low"
        elif value < average_value / 2:
            tier = "lowest"

        return "{0}_{1}".format(name, tier)
    elif type(value) is bool:
        return "{0}_{1}".format(name, value)
    else:
        return str(value)


def compute_max_file_length(paths):
    """
    Return the integer sum of average length and standard length deviation for the given files
    """

    file_lengths = [compute_file_length(path) for path in paths]

    return int(math.ceil(
        average(file_lengths) + standard_deviation(file_lengths)
    ))


def average(l):
    """
    Compute the average value of the list
    """

    return sum(l, 0.0) / len(l)
    

def variance(l):
    """
    Compute the variance of the list
    """

    return average([(x - average(l)) ** 2 for x in l])


def standard_deviation(l):
    """
    Compute the standard deviation in the list
    """

    return variance(l) ** 0.5


def select_data_files(
    folder, filenames, 
    limit=-1,
    max_file_length=False, 
    only_initial=False, only_utf8=False, only_text_plain=False
):
    """
    Select relevant email files from the corpus
    """

    selection = []

    max_selection_length = len(filenames) if len(filenames) < limit and limit >= 0 else limit
    
    progress = ProgressBar(maxval=max_selection_length)

    for filename in progress(filenames):
        if len(selection) == limit:
            break

        lines = codecs.open(folder + filename, "r").readlines()

        if max_file_length and len(lines) > max_file_length:
            continue # skip lines in files that are too long (probable log or bash dump)

        for line in lines:
            if line.startswith("#"): # "#" prefixed lines contain metadata
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

                    if (
                        (is_initial != "true" and only_initial)
                        or (encoding != "UTF-8" and only_utf8)
                        or (mime != "text/plain" and only_text_plain)
                    ):
                        break # this file is not in scope

                    selection.append(filename)

                    break # all necessary metadata has been gathered for this file
            else:
                break # there should be no more metadata in the file

    return selection


def parse_args():
    """
     Parse command line opts and arguments 
    """

    op = OptionParser(usage="usage: %prog [opts]")

    ########################################
    
    op.add_option("-i", "--initial",
        dest="only_initial",
        default=False,
        action="store_true",
        help="keeps only first messages in threads")

    op.add_option("-u", "--utf8",
        dest="only_utf8",
        default=False,
        action="store_true",
        help="keeps only utf-8 encoded messages")

    op.add_option("-t", "--text",
        dest="only_text_plain",
        default=False,
        action="store_true",
        help="keeps only plain text messages")

    ########################################

    op.add_option("--occurrence_threshold_quotient",
        dest="occurrence_threshold_quotient",
        type="float",
        default=OCCURRENCE_THRESHOLD_QUOTIENT,
        help="words that appear less than (quotient * total tokens) times are ignored")

    ########################################

    op.add_option("--data_folder",
        dest="data_folder",
        default=DATA_FOLDER,
        type="string",
        help="path to the data folder")

    op.add_option("--text_tiling_folder",
        dest="text_tiling_folder",
        default=TT_FOLDER,
        type="string",
        help="path to the text tiling folder")

    op.add_option("--ngrams_file",
        dest="ngrams_file",
        default=NGRAMS_FILE,
        type="string",
        help="path to the ngrams file")

    ########################################

    op.add_option("--wapiti_train_file",
        dest="wapiti_train_file",
        default=WAPITI_TRAIN_FILE,
        type="string",
        help="output wapiti train file")

    op.add_option("--wapiti_test_file",
        dest="wapiti_test_file",
        default=WAPITI_TEST_FILE,
        type="string",
        help="output wapiti test file")

    op.add_option("--wapiti_gold_file",
        dest="wapiti_gold_file",
        default=WAPITI_GOLD_FILE,
        type="string",
        help="output wapiti gold file")

    op.add_option("--wapiti_origin_file",
        dest="wapiti_origin_file",
        default=WAPITI_ORIGIN_FILE,
        type="string",
        help="output wapiti origin file")

    ########################################

    op.add_option("--weka_arff_file",
        dest="weka_arff_file",
        default=WEKA_ARFF_FILE,
        type="string",
        help="output weka arff file")

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

    ########################################

    if not options.data_folder.endswith("/"):
        options.data_folder += "/"

    if not options.text_tiling_folder.endswith("/"):
        options.text_tiling_folder += "/"

    ########################################

    if options.test:
        doctest.testmod() # unit testing
    else:
        build_datasets(options)