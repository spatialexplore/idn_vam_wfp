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

from directoryUtils import buildFileList
from os import path, listdir
from longTermAverage import calcAverage, calcMin, calcMax, calcStDev
from ftplib import FTP
from ftpUtils import getFilesFromFTP
from datetime import timedelta, date
from glob import glob
from fnmatch import fnmatch, filter

ftp_address_NDVI = 'chg-ftpout.geog.ucsb.edu'

def getDailyDataFromFTP(localPath, datesList=[]):
    dailyDir = 'pub/org/chg/products/CHIRPS-2.0/global_daily/tifs/p25/'
    chirpsBaseName = 'chirps-v2.0.'
    chirpsExt = '.tif.gz'
    # if have dates, only get those files
    if not datesList:
        # get all files not already in localPath
        getFilesFromFTP(ftp_address_NDVI, 'anonymous', 'anonymous@', dailyDir, localPath)
    else:
        sd = datesList[0]
        ed = datesList[1]
        ftp = None
        try:
            ftp = FTP(ftp_address_NDVI)
        except:
            print("Error connecting to server ", ftp_address_NDVI)
        ftp.login('anonymous','anonymous@')

        while sd <= ed:
            yrs = '{0}'.format(sd.year)
            yrDir = path.join(dailyDir, yrs)
            fname = sd.strftime("chirps-v2.0.%Y.%m.%d.tif.gz")
            print 'Looking for: ', fname, ' in ', yrDir
            localFile = path.join(localPath, fname)
            fileObj = open(localFile, 'wb')
            # try to find file in directory
            fn = yrDir + '/' + fname
            # Download the file a chunk at a time using RETR
            ftp.retrbinary('RETR ' + fn, fileObj.write)
            # Close the file
            fileObj.close()
            print "retreived ", localFile

            sd = sd + timedelta(days=1)
        ftp.close()
    return 0

def getDekadDataFromFTP(localPath):
    dekadDir = 'pub/org/chg/products/CHIRPS-2.0/global_dekad/tifs/'
    getFilesFromFTP(ftp_address_NDVI, 'anonymous', 'anonymous@', dekadDir, localPath)
    return 0

def getPentadDataFromFTP(localPath):
    pentadDir = 'pub/org/chg/products/CHIRPS-2.0/global_pentad/tifs/'
    getFilesFromFTP(ftp_address_NDVI, 'anonymous', 'anonymous@', pentadDir, localPath)
    return 0

def getMonthlyDataFromFTP(localPath):
    monthlyDir = 'pub/org/chg/products/CHIRPS-2.0/global_monthly/tifs/'
    getFilesFromFTP(ftp_address_NDVI, 'anonymous', 'anonymous@', monthlyDir, localPath)
    return 0

def getSeasonalDataFromFTP(localPath):
    seasonalDir = 'pub/org/chg/products/CHIRPS-2.0/global_3-monthly/tifs/'
    getFilesFromFTP(ftp_address_NDVI, 'anonymous', 'anonymous@', seasonalDir, localPath)
    return 0

def getCHIRPSData(address, userName, passWord, remotePath, localPath, years, onlyDiff=True):
    ftp = None
    try:
        ftp = FTP(address)
    except:
        print("Error connecting to server ", address)
    ftp.login(userName,passWord)
    ftp.cwd(remotePath)

    for i, val in enumerate(years):
        ftp.cwd(val)
        localPathYear = path.join(localPath, val)
        print("local path for ", val, ": ", localPathYear)
        if onlyDiff:
            lFileSet = set(listdir(localPathYear))
            rFileSet = set(ftp.nlst())
            transferList = list(rFileSet - lFileSet)
            print "Missing: " + str(len(transferList))
        else:
            transferList = ftp.nlst()
            print "File list: ", transferList

        filesMoved = 0
        for fl in transferList:
            # create a full local filepath
            localFile = path.join(localPathYear, fl)
            print "new file: ", localFile
            grabFile = True
            if grabFile:
                #open a the local file
                fileObj = open(localFile, 'wb')
                # Download the file a chunk at a time using RETR
                ftp.retrbinary('RETR ' + fl, fileObj.write)
                # Close the file
                fileObj.close()
                filesMoved += 1
        print(transferList)
        ftp.cwd('..')

    ftp.close()
    ftp = None
    return 0

def performCalculations(fileList, baseName, outputPath, functionList):
    for f in functionList:
        if f == 'AVG':
            newfile = '{0}.avg.tif'.format(baseName)
            ofl = path.join(outputPath, newfile)
            calcAverage(fileList, ofl)
        elif f == 'STD':
            newfile = '{0}.std.tif'.format(baseName)
            ofl = path.join(outputPath, newfile)
            calcStDev(fileList, ofl)
        elif f == 'MAX':
            newfile = '{0}.max.tif'.format(baseName)
            ofl = path.join(outputPath, newfile)
            calcMax(fileList, ofl)
        elif f == 'MIN':
            newfile = '{0}.min.tif'.format(baseName)
            ofl = path.join(outputPath, newfile)
            calcMin(fileList, ofl)
        else:
            print f, ' is not a valid function.'
    return 0

def matchDayNightFiles(dayPath, nightPath, outPath):
    dayFiles = list(listdir(dayPath))
    nightFiles = set(listdir(nightPath))

    print "Day files: ", dayFiles
    print "Night files: ", nightFiles

    for fl in dayFiles:
        # find matching night file
        d_fl, ext = path.splitext(path.basename(path.normpath(fl)))
        if (ext == '.tif'):
            d_t = d_fl.rpartition('.')
            # night files end in 06, day files end in 01
            n_fl = d_t[0] + d_t[1] + '06' + ext
            if (n_fl) in nightFiles:
                avg_fl = path.join(outPath, d_t[0] + d_t[1] + 'avg' + ext)
                dp = path.join(dayPath, d_fl+ext)
                np = path.join(nightPath, n_fl)
                calcAverage([dp, np], avg_fl)
    return 0

# MOD13Q1.A2002033.h27v08.005.2008293034945.hdf
def getNDVIYear(filename):
    d = filename.split('.', 2)[1]
    yr = (d[:5])[-4:]
    return yr

# MOD13Q1.A2002033.h27v08.005.2008293034945.hdf
def getNDVIDoY(filename):
    d = filename.split('.', 2)[1]
    doy = d[-3:]
    return doy

def getNDVIGrid(filename):
    loc = filename.split('.', 3)[2]
    gridLoc = (loc[:3])[-2:], loc[-2:]
    return gridLoc

def selectNDVIFiles(base_path, doy, years, filenames):
    f_base = filenames[0] #'idn_phy_MOD13Q1'
    ext = filenames[1] #'.tif'
    all_files = buildFileList(base_path, ext)
    yrs = []
    dy = []
    for fl in all_files:
        yrs.append(getNDVIYear(fl))
        dy.append(getNDVIDoY(fl))

    if not years:
        # do all - get all files, work out what years are included
        years = set(yrs)
    if not doy:
        # do all
        days = set(dy)

    files = set(all_files)
    fileList = []
    for d in days:
        yrList = []
        for y in years:
            # create file
            fn = "{0}{1}.A{2}{3}.005.*{4}".format(base_path, f_base, y, d, ext)
            filtered = filter(files, fn)
            if filtered:
                if path.isfile(filtered[0]):
                    yrList.append(filtered[0])
        yrList.sort()
        t = d, yrList
        fileList.append(t)
    fileList.sort()
    return [fileList, days, years]


# NDVI files have filenames in the format:
# idn_phy_MOD13Q1.A2002033.005.NDVI.tif
#
def calcNDVIAverages(base_path, output_path, functionList = [], filenames = ('idn_phy_MOD13Q1', '.tif')):
    resultsList = selectNDVIFiles(base_path, [], [], filenames)
    filesList = resultsList[0]
    days = resultsList[1]
    years = resultsList[2]
    syr = min(years)
    eyr = max(years)
    for i,d in enumerate(filesList):
        # for each day of the year with data, calculate long term average
        fl = filesList[i][1]
        if fl:
            print "Calculating long term average for ", fl
            newfilename = '{0}.A{1}-{2}{3}.005.250m_16_days_NDVI'.format(filenames[0], syr, eyr, d[0])
            if not functionList:
                # default is to calculate the average
                functionList.append('AVG')
            performCalculations(fl, newfilename, output_path, functionList)
    return 0

