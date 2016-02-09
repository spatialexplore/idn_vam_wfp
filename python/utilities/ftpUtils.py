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
import logging
import ftplib

logger = logging.getLogger('ftpUtils')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def openFTP(address, userName = 'anonymous', password = 'anonymous@'):
    ftp = None
    try:
        ftp = FTP(address)
    except ftplib.all_errors, e:
        logger.debug('Error connecting to server %s' % address)
        logger.debug(e.msg)
    ftp.login(userName,password)
    return ftp

def closeFTP(ftp):
    ftp.close()

def getFileFromFTP(ftp, srcname, destname, replace = False):
    exists = path.isfile(destname)
    if exists and not replace:
        logger.debug('Error file already exists')
    else:
        fileObj = open(destname, 'wb')
        try:
            # Download the file a chunk at a time using RETR
            ftp.retrbinary('RETR ' + srcname, destname.write)
        except ftplib.all_errors, e:
            logger.debug('Error getting file %s' % srcname)
            logger.debug(e.msg)
        fileObj.close()
        logger.debug('Retreived %s' % srcname)


def getFilesFromFTP(address, userName, passWord, remotePath, localPath, replace=False, filesList = None):
    ftp = None
    try:
        ftp = FTP(address)
    except ftplib.all_errors, e:
        logger.debug('Error connecting to server %s' % address)
        logger.debug(e.msg)
    ftp.login(userName,passWord)
    try:
        ftp.cwd(remotePath)
    except ftplib.all_errors, e:
        logger.debug('Error changing directory to %s' % remotePath)
        logger.debug(e.msg)
    if not filesList:
        # get all files in directory
        transferList = ftp.nlst()
    else:
        transferList = filesList
    logger.debug('List of files to transfer: %s' % transferList)

    for fl in transferList:
        # create a full local filepath
        localFile = path.join(localPath, fl)
        grabFile = True
        if path.isfile(localFile) and not replace:
            grabFile = False
        if grabFile:
            logger.debug('Downloading %s' % fl)
            #open a the local file
            fileObj = open(localFile, 'wb')
            try:
                # Download the file a chunk at a time using RETR
                ftp.retrbinary('RETR ' + fl, fileObj.write)
            except ftplib.all_errors, e:
                logger.debug('Error getting file %s' % fl)
                logger.debug(e.msg)
            # Close the file
            fileObj.close()
            logger.debug('Retreived %s' % localFile)
    ftp.close()
    ftp = None
    return 0

