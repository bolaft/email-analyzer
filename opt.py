#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser

def main(options, args):
	print options
	print args

# Launch
if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--check", dest="check", default=False, action="store_true")
	parser.add_option("-t", "--train", dest="train", default=False, action="store_true")

	options, args = parser.parse_args()
	main(options, args)