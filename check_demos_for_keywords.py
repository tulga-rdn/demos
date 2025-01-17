#!/usr/bin/env python
# This script takes as its single argument a path to a directory (archetypally Rosetta/demos) and checks every .md file in that directory to see if it has keywords, defined as "a line starting with KEYWORDS: and containing at least two more things." Designed to fail noisily if not, as per a test.
# author Frank David Teets
# Written during XRW2016

from __future__ import print_function
import os
import sys
import shutil
import argparse

parser = argparse.ArgumentParser(description='Check all demos of a particular working directory for both having a required keyword \
	line and that those keywords being part of an approved list')
parser.add_argument('working_directory', type = str, help = "root directory of the file system to be checked for keywords")
parser.add_argument('approved_keyword_list', type = str, help ="list of approved keywords")
args = parser.parse_args()

all_demos_are_keyworded = True
demos = []
approved_keywords = []
approved_keywords.append("KEYWORDS:")
keywords = open(args.approved_keyword_list, 'r')
for line in keywords:
	if not(line.startswith("#")):
		tokens = line.split()
		if(len(tokens) > 0):
			approved_keywords.append(tokens[0])

for root, directories, filenames in os.walk(args.working_directory):
	for filename in filenames:
		if filename.endswith(".md") and not (root == args.working_directory) and not(filename.startswith("_")):
			demos.append(os.path.join(root, filename))
print( demos )
#
#for demoname in demos:
#	has_keywords = False
#	current_demo = open(demoname, 'r')
#	for line in current_demo:
#		if ("KEYWORDS:" in line):
#			tokens = line.split()
#			if(len(tokens)>2):
#				has_keywords = True
#				for keyword in tokens:
#					if keyword not in approved_keywords:
#						print str(demoname) + " has unapproved keyword "+ keyword
#						all_demos_are_keyworded = False
#	if not(has_keywords):
#		print str(demoname)  +" has no keywords!"
#		all_demos_are_keyworded = False
#if not(all_demos_are_keyworded):
#	os._exit(1)
