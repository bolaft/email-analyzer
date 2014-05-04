#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Name:
    utility.py

:Authors:
    Soufian Salim (soufi@nsal.im)
"""

import re
import time


def timed_print(message):
	"""
	Prints a string prefixed by the current date and time
	"""
	print("[{0}] {1}".format(time.strftime("%H:%M:%S"), message))