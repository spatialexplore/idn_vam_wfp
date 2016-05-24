#!/usr/bin/env python
"""
SYNOPSIS

    TODO helloworld [-h,--help] [-v,--verbose] [--version]

DESCRIPTION

    TODO This describes how to use this script. This docstring
    will be printed by the script if there is an error or
    if the user requests help (-h or --help).

EXAMPLES

    TODO: Show some examples of how to use this script.

EXIT STATUS

    TODO: List exit codes

AUTHOR

    TODO: Name <name@example.org>

LICENSE

    This script is in the public domain, free from copyrights or restrictions.

VERSION

    $Id$
"""
__author__ = 'rochelle'

import os
#from os import listdir, path
import gzip
import re

def listMatchingFiles(base_dir, pattern):
    # build list of files matching pattern
    fileList = []
    if not pattern:
        pattern = '.*'
    if os.path.exists(base_dir):
        _all_files = os.listdir(base_dir)
        for _fn in _all_files:
            _pth = os.path.join(base_dir, _fn)
            if not os.path.isdir(_pth):
                if re.match(pattern, _fn):
                    fileList.append(_pth)
    return fileList

def buildFileList(base_dir, extension='.tif'):
    fileList = []
    if os.path.exists(base_dir):
        all_files = os.listdir(base_dir)
        for fname in all_files:
            pth = os.path.join(base_dir, fname)
            if os.path.isdir(pth):
                # skip directories
                continue
            else:
                # file
                fn, ext = os.path.splitext(fname)
                if ext == extension:
                    fileList.append(pth)
    return fileList

def getMatchingFiles(base_dir, filter):
    fileList = []
    if os.path.exists(base_dir):
        all_files = os.listdir(base_dir)
        for f in all_files:
            pth = os.path.join(base_dir, f)
            if not os.path.isdir(pth):
                # check file against filter
                if re.match(filter, f):
                    fileList.append(pth)
    return fileList

def getNewFilename(filename, prefix, ext, pattern, new_pattern):

    f= os.path.basename(filename)
    m = re.match(pattern, f)
    new_filename = re.sub(pattern,
                         lambda match: new_pattern.format(
                             prefix = prefix,
                             datestamp = match.group('datestamp'),
                             ext = ext)
                         if match.group('datestamp') else f, f)

    return os.path.join(os.path.dirname(filename), new_filename)

def unzipFiles(base_dir, extension='.gz'):
    filesList = buildFileList(base_dir, extension)
    for fl in filesList:
        if not os.path.isdir(fl):
            with gzip.open(fl, 'rb') as in_file:
                s = in_file.read()
            # Now store the uncompressed data
            path_to_store = fl[:-3]  # remove the '.gz' from the filename
            # store uncompressed file data from 's' variable
            with open(path_to_store, 'wb') as f:
                f.write(s)
    return 0

def unzipFile(fname, extension='.gz'):
    inF = gzip.open(fname, 'rb')
    outfilename = fname[:-3]
    outF = open(outfilename, 'wb')
    outF.write( inF.read() )
    inF.close()
    outF.close()
    return outfilename