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

from ftplib import FTP
from os import path

def getFilesFromFTP(address, userName, passWord, remotePath, localPath, replace=False):
    ftp = None
    try:
        ftp = FTP(address)
    except:
        print("Error connecting to server ", address)
    ftp.login(userName,passWord)
    ftp.cwd(remotePath)

    transferList = ftp.nlst()
    print "File list: ", transferList

    for fl in transferList:
        # create a full local filepath
        localFile = path.join(localPath, fl)
        grabFile = True
        if path.isfile(localFile) and not replace:
            grabFile = False
        if grabFile:
            print "grabbing ", fl
            #open a the local file
            fileObj = open(localFile, 'wb')
            # Download the file a chunk at a time using RETR
            ftp.retrbinary('RETR ' + fl, fileObj.write)
            # Close the file
            fileObj.close()
            print "retreived ", localFile
    ftp.close()
    ftp = None
    return 0

