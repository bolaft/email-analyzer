#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    utility.py

:Authors:
    Soufian Salim (soufi@nsal.im)
"""

import time


def timed_print(message):
    """
    Prints a string prefixed by the current date and time
    """

    print("[{0}] {1}".format(time.strftime("%H:%M:%S"), message))


def compute_file_length(path, ignore_empty=False, comment_char="#"):
    """
    Compute the length of a file
    """

    return sum(
        1 for line in open(path) 
        if not line.startswith(comment_char) and (len(line.strip()) > 1 or not ignore_empty)
    )


def float_to_string(f):
    """
    Converts float to string
    """

    return "{0:.2f}".format(float(f) * 100)


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