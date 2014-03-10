#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    html_converter.py

:Authors:
    Soufian Salim (soufi@nsal.im)

:Date:
    march 6, 2014 (creation)

:Description:
    converts a sample of tokens extracted from tagged emails into a single html file
    (see https://github.com/bolaft/email-analyzer)
"""

from progressbar import ProgressBar

import sys
import codecs
import os


# Constants
human_filepath = "var/human.html"
comparative_filepath = "var/comparative.html"
result_filepath = "var/result"
limit = 100

locale = "en"
stylesheet = "style.css"
encoding = "UTF-8"
title = "Data"


# Main
def main(argv):
    make_comparative_file()

    # make_human_file()


def make_comparative_file():
    print("Converting data from %s" % result_filepath)

    progress = ProgressBar()

    with codecs.open(comparative_filepath, "w", "utf-8") as out:
        out.write("<!doctype html>")
        out.write("<html lang=\"%s\">" % locale)
        out.write("<head>")
        out.write("<link rel=\"stylesheet\" href=\"%s\" type=\"text/css\">" % stylesheet)
        out.write("<meta charset=\"%s\">" % encoding)
        out.write("<title>%s</title>" % title)
        out.write("</head>")
        out.write("<body>")
        out.write("<table>")

        with codecs.open(result_filepath, "r", "utf-8") as f:
            for line in f:
                line = line.strip()
                tokens = line.split()
                if len(tokens) > 2:
                    out.write("<tr><td>%s</td><td class=\"td %s\"></td><td class=\"td %s\"></td></tr>" % (tokens[0], tokens[-2], tokens[-1]))

        out.write("</table></body></html>")


def make_human_file(source_folder):
    print("Converting data from %s..." % source_folder)

    progress = ProgressBar()

    with codecs.open(human_filepath, "w", "utf-8") as out:
        out.write("<!doctype html>")
        out.write("<html lang=\"%s\">" % locale)
        out.write("<head>")
        out.write("<link rel=\"stylesheet\" href=\"%s\" type=\"text/css\">" % stylesheet)
        out.write("<meta charset=\"%s\">" % encoding)
        out.write("<title>%s</title>" % title)
        out.write("</head>")
        out.write("<body>")

        for i, filename in enumerate(progress(os.listdir(source_folder))):
            if i == limit:
                break

            with codecs.open(source_folder + filename, "r", "utf-8") as f:
                out.write("<div class=\"mail\">")
                for line in f:                
                    if not line.startswith("#"):
                        tokens = line.split()

                        if len(tokens) > 1:
                            label = tokens.pop(0)
                            out.write("<div class=\"line %s\">" % label)
                            out.write("<p>%s</p>" % " ".join(tokens))
                            out.write("</div>")

                out.write("</div>")

        out.write("</body></html>")


# Process argv
# def process_argv(argv):
#     if len(argv) != 2:
#         print("Usage: " + argv[0] + " <source folder>")
#         sys.exit()

#     # adding a "/" to the dirpath if not present
#     source_folder = argv[1] + "/" if not argv[1].endswith("/") else argv[1]

#     if not os.path.isdir(source_folder):
#         sys.exit(source_folder + " is not a directory")

#     return source_folder


# Launch
if __name__ == "__main__":
    main(sys.argv)
