#!/usr/bin/env python
"""
Autograder.  Compiles and runs student programs, comparing
output with a standard output file.
"""

# use print() instead of plain print
from __future__ import print_function 
import os
import shutil as SH
import subprocess
import signal
import time
import argparse as ap


# Setup the arguments to the script

parser = ap.ArgumentParser(description='Autograder script.')
parser.add_argument('-d','--maindir',dest='maindir', default='./',
        help='The main directory containing student directories.')
parser.add_argument('-t','--toolong',dest='toolong', type=int, default=5,
        help='No. of seconds before program is determined non-responsive.')
parser.add_argument('-l','--logfile',dest='logfile', default='clog',
        help='Temporary file to store compiler output.')
parser.add_argument('-m','--makestr',dest='makestr', default='/usr/bin/make',
        help="Command to run in order to build students' code.")
parser.add_argument('-s','--testscript',dest='testscript', default='./test.sh',
        help='Test script to produce delimited output of tests.')
parser.add_argument('-k','--delimiter',dest='delimiter', default='@',
        help='Delimiter used to separate tests in the output files.')
parser.add_argument('-o','--scoresfile',dest='scoresfile', default='',
        help="Filename to store the tab-delimited scores.")
parser.add_argument('-p','--missingok',dest='missingok', default=0,
        help="Attempt to grade, even if some implementation files \
        are missing.", action='count')
parser.add_argument('-f','--force',dest='force', default=0, action='count',
        help="Force a regrade, even if '_result.txt' is up to date.")
parser.add_argument('--exclude',dest='exclude', nargs='+', default=[],
        help="List of directories (relative to maindir) to exclude.")
parser.add_argument('implfiles', nargs='+',
        help="Name of students' implementation file(s), e.g. 'hello.cpp'.")
args = parser.parse_args()

implFiles = args.implfiles
mainFile = args.implfiles[0]
mainDir = args.maindir
tooLong = args.toolong
logFile = args.logfile
makestr = args.makestr
testScript = args.testscript
delim = args.delimiter if args.delimiter != "" else None
scoresFile = args.scoresfile if args.scoresfile != "" else mainFile + "_scores"
missingok = args.missingok
forceRegrade = args.force
excludes = args.exclude

# if a makestring and log file are supplied, redirect output of make command:
if makestr != "" and logFile != "":
    makestr = makestr + " &> " + logFile

# TODO: test.
# TODO: not very happy with the way that processes are currently killed.
# When the test script is complicated, and say involves piping things around
# to different programs, it is not enough to just kill the test script, should
# it go into an infinite loop; there may be child processes left behind, which
# at best take up resources, and at worst prevent the compilation of other
# student's code (the executable can get locked).  Current method: pgrep for
# the group id and kill everything but the python interpreter (which is
# usually a member of the group @_@)

# Also, there is no wait with timeout in the current version of python, so
# we resort to polling the process (see pollFreq below).
# The proper way to do it will be included in python 3.3, which is not yet
# released:
# http://docs.python.org/dev/library/subprocess.html
# http://bugs.python.org/issue5673

pollFreq = 5 # how many times per second to poll the testscript process.


def main():
    # we may need to write forceRegrade here, so import from global scope:
    global forceRegrade
    os.chdir(mainDir)
    # create / read dictionary for scores:
    scores = {}
    if os.path.exists(scoresFile):
        with open(scoresFile,'r') as f:
            scores = dict(map(str.split,f.readlines()))
    else:
        forceRegrade = 1
        # if the scores file is missing, it seems recomputation is needed.

    # make a copy of the environment, which we will modify and send to
    # the test script, with some of our own variables added.
    cenv = os.environ.copy()
    # now walk the top level directories:
    for d in os.listdir("."):
        if (not os.path.isdir(d)) or (d in excludes):
            continue
        resultMsg = ""
        fatalerr = False  # to check what happened in the finally clause.
        # run tests, and update the grades.
        # move files one by one to the current directory (if they exist)
        # and run the test script on each one.  To prevent the previous
        # student's work from affecting the test, remove the old output
        # and make sure the interpreter does not produce compiled
        # bytecode.
        try:
            # clear the log and the output file:
            f = open(logFile,'w')
            f.close()
            f = open("output",'w')
            f.close()
            # try to run make clean; if it fails, just move on
            if makestr != "":
                os.spawnl(os.P_WAIT,makestr,"make","clean")
        except:
            pass
        print("Processing " + d)
        try:
            # record the time the result was last created
            resultFile = os.path.join(d,mainFile + "_result.txt")
            rmtime = 0 # this would be really old.
            if os.path.exists(resultFile):
                rmtime = os.path.getmtime(resultFile)
            up2date = True
            for ifile in implFiles:
                # get rid of the old one:
                if os.path.exists(ifile):
                    os.remove(ifile)
                # try to copy the new one:
                sfile = os.path.join(d,ifile)
                if os.path.exists(sfile):
                    SH.copyfile(sfile,ifile)
                    if os.path.getmtime(sfile) > rmtime:
                        up2date = False
                elif not missingok:
                    print(d + " didn't do their work")
                    resultMsg = "Assignment not turned in."
                    raise UserWarning
                else:
                    print("Warning: " + sfile + " missing.")

            # skip this file if we've already done it:
            if up2date and not forceRegrade:
                print("Skipping; grade already up to date")
                continue
            # now, if applicable, try to build the program using the
            # specified make string:
            if makestr != "":
                retcode = subprocess.call(makestr, shell=True)
                if retcode:
                    print(d + " failed to build x_x")
                    resultMsg = "Failed to build x_x"
                    raise UserWarning

            # now run the test script and compare output vs. soutput
            # we want something simple, like the following:
            # subprocess.call(testScript)
            # however, this is no good when people's programs break,
            # or run into infinite loops.  So we must monitor the thread
            # in which it runs, and kill it after too much time has passed.

            cenv["AG_current_dir"] = d
            sproc = subprocess.Popen(testScript, env=cenv)
            # testScript should have access to the current student's
            # directory via the AG_current_dir variable.
            ranForever = True
            for i in xrange(tooLong*pollFreq):
                if not sproc.poll() is None:
                    ranForever = False
                    break
                time.sleep(1.0/pollFreq)

            if ranForever:
                print ("infinite loop. killing test script...")
                killSubGroup(os.getpid())
                sproc.communicate() # wait for process to shut down.
                time.sleep(.5) # hack; I feel like child processes
                               # don't always get to close in time.
                resultMsg = "Program ran too long. Infinite loop?\n"
                raise UserWarning
            else:
                resultMsg,nRight,nTotal = compare("")
        except UserWarning:
            # something went horribly wrong, so set the score to be 0:
            nRight = 0
            nTotal = 1
            # if needed, we can get some error info here?
            # Note: nothing special about UserWarning; it sounded
            # nice and I needed an exception.  That's all.
        except IOError as err:
            # score was not succesfully computed
            fatalerr = True
            print("IO Error x_x")
            print(err.message)
            print("Grading incomplete; after resolving the errors, it " +
                    "is recommended you run with the --force option " +
                    "to recompute.")
            # this is probably serious, and could affect the other grades;
            # hence we will check for ioerrors in the finally clause, and
            # break the loop if any are found.  This will still write
            # whatever results we did manage to compute successfully.
        except Exception as err: # handle any other generic errors.
            print(err)
            fatalerr = True
        finally:
            # if some fatal error happened, don't write anything
            if fatalerr:
                break
            # write a report of whatever happened.
            if not up2date or forceRegrade:
                scores[d] = int(round((float(nRight)/nTotal)*100))
                with open(os.path.join(d,mainFile + "_result.txt"),'w') as f:
                    f.write(resultMsg + "\n\n")
                    f.write("Compiler output:\n\n")
                    with open(logFile,'r') as fs:
                        f.write(fs.read())
                    f.write("Score: " + str(nRight) + " out of " + \
                            str(nTotal) + " = " + str(scores[d]) + "%\n\n")
                    f.write("*************Original submission*************")
                    # there might not be a file here, so just ignore any
                    # errors that are raised.
                    try:
                        for ifile in implFiles:
                            sfile = os.path.join(d,ifile)
                            f.write("\n\n###########  " +
                                    ifile + "  ###########\n\n")
                            with open(sfile,'r') as fs:
                                f.write(fs.read())
                    except:
                        pass

    with open(scoresFile,'w') as fscores:
        for k in sorted(scores.keys()):
            fscores.write(k + "\t" + str(scores[k]) + "\n")
    print ("Scores written to " + scoresFile)
    return

def declare_path():
    """This function is currently a dummy but can later be used to grade a
    whole set of student work, one directory per student in the same path.
    """
    
    # "the_student" is name of a directory in the path
    the_path = the_student = ''
    return the_path + the_student

def compare(full_path):
    """Evaluate student's output file against authenticated output file
    and report the results.
    """

    solutionOutput = "soutput"
    output = "output"
    # First evaluate tests and store results.
    # "counter" will hold True/False in each index, each representing a test
    counter = [] 
    try:
        # remember, U recognizes all newlines
        with open(full_path + solutionOutput, 'U') as filename: 
            off_content = filename.read().split(delim)
            off_length = len(off_content)
        with open(full_path + output, 'U') as filename:
            stu_content = filename.read().split(delim)
            stu_length = len(stu_content)
    except IOError:
        print('\nIOError reported; exiting. \n\nAre the files "output"'
            'and "soutput" in the right place?\n\nPath was given as',
            full_path)
        return "Program failed to produce output",0,1
    # print('\nDetected', off_length, 'tests in authenticated output file.')
    # pad the student output if necessary
    for i in xrange(off_length - stu_length):
        stu_content.append(delim) # this should never be a right answer.
    ignores = ' \t\n\r'
    counter = [off_content[i].strip(ignores) == stu_content[i].strip(ignores) for i in xrange(off_length)]
    
    # Now report results.
    resultstr = ""
    if all(counter):
        resultstr = 'Summary: All tests passed.'
    else:
        # must make plural noun agree with counter
        failure_spelling = ' failure' + ('s ' if counter.count(False) > 1 else ' ')
        resultstr = '\nSummary: Student output has ' + \
                str(counter.count(False)) + failure_spelling + \
                'in ' + str(len(counter)) + ' tests.\n\nDetailed report:\n'
        for i in xrange(len(counter)):
            if counter[i]==False:
                resultstr += '\nTest ' + str(i) + ' failed:\n   Student had:\t' + \
                        stu_content[i] + '\n   Should have:\t' + off_content[i]
    return resultstr,counter.count(True),off_length

def killSubGroup(pid):
    """This function will kill all members of pid's group, except
    for the pid process specified.  The idea is to kill all processes
    started with subprocess.popen, except for the python interpreter
    itself, which usually belongs to the same group."""
    # use pgrep to filter, then kill all but pid.
    pgl = os.popen("pgrep -g " + str(os.getpgid(pid))).readlines()
    doomed = [p for p in map(int,pgl) if p!=pid]
    # now kill them:
    for p in doomed:
        print ("killing " + str(p))
        try:
            os.kill(p,signal.SIGTERM)
        except OSError:
            pass


if __name__ == '__main__':
  main()
