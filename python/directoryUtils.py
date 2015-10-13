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

from os import listdir, path
import gzip

def buildFileList(base_dir, extension='.tif'):
    fileList = []
    if path.exists(base_dir):
        all_files = listdir(base_dir)
        for fname in all_files:
            pth = path.join(base_dir, fname)
            if path.isdir(pth):
                # skip directories
                continue
            else:
                # file
                fn, ext = path.splitext(fname)
                if ext == extension:
                    fileList.append(pth)
    return fileList

def unzipFiles(base_dir, extension='.gz'):
    filesList = buildFileList(base_dir, extension)
    for fl in filesList:
        inF = gzip.open(fl, 'rb')
        outfilename = fl[:-3]
        outF = open(outfilename, 'wb')
        outF.write( inF.read() )
        inF.close()
        outF.close()

    return 0