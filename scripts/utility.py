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


def compute_file_length(path, ignore_empty=False):
    """
    Compute the length of a file
    """

    return sum(1 for line in open(path) if not line.startswith("#") and (len(line.strip()) > 1 or not ignore_empty))