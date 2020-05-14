# Autograder Script

## Synopsis

`autograder.py [options] file1 [file2 [file3...]]`

## Overview

A short python script designed to help automate grading of programming
assignments.  **[Full documentation is available here!][aghome]**

## Details

	usage: ag.py [-h] [-d MAINDIR] [-t TOOLONG] [-l LOGFILE] [-m MAKESTR]
				 [-s TESTSCRIPT] [-k DELIMITER] [-o SCORESFILE] [-a]
				 implfiles [implfiles ...]

	positional arguments:
	  implfiles             Name of students' implementation file(s), e.g.
							'hello.cpp'.

	optional arguments:
	  -h, --help 			show this help message and exit
	  -d DIR, --maindir=DIR	The main directory containing student directories.
							Default: the current directory.
	  -t TIMEOUT, --toolong=TIMEOUT
							No. of seconds before program is determined non-
							responsive.  Default: 5.
	  -l LOGFILE, --logfile=LOGFILE
							Temporary file to store compiler output.
							Default: "clog"
	  -m MAKECMD, --makestr=MAKECMD
							Command to run in order to build students' code.
							Default: "/usr/bin/make"
	  -s TESTSCRIPT, --testscript=TESTSCRIPT
							Test script to produce delimited output of tests.
							Default: "./test.sh"
	  -k DELIM, --delimiter=DELIM
							Delimiter used to separate tests in the output files.
							Default: "@"
	  -o SCORES, --scoresfile=SCORES
							Filename to store the tab-delimited scores.
							Default: "scores"
	  -p, --missingok		Attempt to grade, even if some implementation files
	  						are missing.
	  --exclude EXCLUDE [EXCLUDE ...]
	                        List of directories (relative to maindir) to exclude.
	  -f, --force 			Force regrade, even if files are up to date.
							Note: this can also be accomplished by changing the
							output file: --o="aNewFile"
	  


[aghome]: http://www-cs.ccny.cuny.edu/~wes/autograder/readme.html
