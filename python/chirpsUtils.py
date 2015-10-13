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
from precipitationAnalysis import daysSinceLast
import datetime

ftp_address_CHIRPS = 'chg-ftpout.geog.ucsb.edu'

def getDailyDataFromFTP(localPath, datesList=[]):
    dailyDir = 'pub/org/chg/products/CHIRPS-2.0/global_daily/tifs/p25/'
    chirpsBaseName = 'chirps-v2.0.'
    chirpsExt = '.tif.gz'
    # if have dates, only get those files
    if not datesList:
        # get all files not already in localPath
        getFilesFromFTP(ftp_address_CHIRPS, 'anonymous', 'anonymous@', dailyDir, localPath)
    else:
        sd = datesList[0]
        ed = datesList[1]
        ftp = None
        try:
            ftp = FTP(ftp_address_CHIRPS)
        except:
            print("Error connecting to server ", ftp_address_CHIRPS)
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
    getFilesFromFTP(ftp_address_CHIRPS, 'anonymous', 'anonymous@', dekadDir, localPath)
    return 0

def getPentadDataFromFTP(localPath):
    pentadDir = 'pub/org/chg/products/CHIRPS-2.0/global_pentad/tifs/'
    getFilesFromFTP(ftp_address_CHIRPS, 'anonymous', 'anonymous@', pentadDir, localPath)
    return 0

def getMonthlyDataFromFTP(localPath):
    monthlyDir = 'pub/org/chg/products/CHIRPS-2.0/global_monthly/tifs/'
    getFilesFromFTP(ftp_address_CHIRPS, 'anonymous', 'anonymous@', monthlyDir, localPath)
    return 0

def getSeasonalDataFromFTP(localPath):
    seasonalDir = 'pub/org/chg/products/CHIRPS-2.0/global_3-monthly/tifs/'
    getFilesFromFTP(ftp_address_CHIRPS, 'anonymous', 'anonymous@', seasonalDir, localPath)
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

# idn_cli_chirps-v2.0.1981.01.1.dekad.tif.gz
def getCHIRPSYear(filename):
    yr = filename.split('.', 3)[2]
    return yr

# idn_cli_chirps-v2.0.1981.01.1.dekad.tif.gz
def getCHIRPSMonth(filename):
    mth = filename.split('.', 4)[3]
    return mth

# chirps-v2.0.1981.010203.tif
def getCHIRPSSeason(filename):
    season = filename.split('.', 4)[3]
    return season

def selectDekadFiles(base_path, dekad, months, years, filenames):
    f_base = filenames[0]
    ext = filenames[1]
    all_files = buildFileList(base_path, ext)
    if not years:
        # do all - get all files, work out what years are included
        yrs = []
        for fl in all_files:
            yrs.append(getCHIRPSYear(fl))
        years = set(yrs)
    if not months:
        # do all
        months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

    if not dekad:
        # do all dekads
        dekad = [1, 2, 3]

    files = set(all_files)
    fileList = []
    for m in months:
        mList = []
        for d in dekad:
            yrList = []
            for y in years:
                # create file
                fn = "{0}.{1}.{2}.{3}.dekad{4}".format(f_base, y, m, d, ext)
                if fn in files:
                    if path.isfile(fn):
                        yrList.append(fn)
            yrList.sort()
            t = d, yrList
            mList.append(t)
        mList.sort()
        mt = m, mList
        fileList.append(mt)
    fileList.sort()
    return fileList


# Dekad files have filenames in the format:
# idn_cli_chirps-v2.0.1981.01.1.dekad.tif.gz
#
def calcDekadAverages(base_path, output_path, functionList = [], filenames = ('idn_cli_chirps-v2.0', '.tif')):
    filesList = selectDekadFiles(base_path, [], [], [], filenames)
    syr = 1981
    eyr = 2015
    for m in range(0,12):
        # for each month, calculate long term average of each dekad
        for d in range(0,3):
            #for each dekad
            fl = ((filesList[m])[1])[d]
            mth = fl[0].split('.')[3]
            dd = fl[0].split('.')[4]
#            nfl = 'idn_cli_chirps-v2.0.{0}-{1}.{2}.{3}.avg.tif'.format(syr, eyr, mth, dd)
#            ofl = path.join(output_path, nfl)
            print "Calculating long term average for ", fl
            newfilename = '{0}.{1}-{2}.{3}.{4}'.format(filenames[0], syr, eyr, mth, dd)
            if not functionList:
                # default is to calculate the average
                functionList.append('AVG')
            performCalculations(fl, newfilename, output_path, functionList)

#            calcAverage(fl, ofl)
    return 0

#idn_cli_chirps-v2.0.1999.01.6.tif.gz
def selectPentadFiles(base_path, pentad, months, years, filenames):
    f_base = filenames[0]
    ext = filenames[1]
    all_files = buildFileList(base_path, ext)
    if not years:
        # do all - get all files, work out what years are included
        yrs = []
        for fl in all_files:
            yrs.append(getCHIRPSYear(fl))
        years = set(yrs)
    if not months:
        # do all
        months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

    if not pentad:
        # do all pentads
        pentad = [1, 2, 3, 4, 5, 6]

#    f_base = 'idn_cli_chirps-v2.0.'
    files = set(all_files)
    fileList = []
    for m in months:
        mList = []
        for p in pentad:
            yrList = []
            for y in years:
                # create file
                fn = "{0}{1}.{2}.{3}.{4}{5}".format(base_path, f_base, y, m, p, ext)
                if fn in files:
                    if path.isfile(fn):
                        yrList.append(fn)
            yrList.sort()
            t = p, yrList
            mList.append(t)
        mList.sort()
        mt = m, mList
        fileList.append(mt)
    fileList.sort()
    return fileList

# Pentad files have filenames in the format:
# idn_cli_chirps-v2.0.1981.01.1.tif.gz
#
def calcPentadAverages(base_path, output_path, functionList = [], filenames = ('idn_cli_chirps-v2.0', '.tiff')):
    filesList = selectPentadFiles(base_path, [], [], [], filenames)
    syr = 1981
    eyr = 2015
    for m in range(0,12):
        # for each month, calculate long term average of each pentad
        for p in range(0,6):
            #for each pentad
            fl = ((filesList[m])[1])[p][1]
            mth = fl[0].split('.')[3]
            pd = fl[0].split('.')[4]
#            nfl = 'idn_cli_chirps-v2.0.{0}-{1}.{2}.{3}.avg.tif'.format(syr, eyr, mth, pd)
#            ofl = path.join(output_path, nfl)
            print "Calculating long term average for ", fl
            newfilename = '{0}.{1}-{2}.{3}.{4}'.format(filenames[0], syr, eyr, mth, pd)
            if not functionList:
                # default is to calculate the average
                functionList.append('AVG')
            performCalculations(fl, newfilename, output_path, functionList)
#            calcAverage(fl, ofl)
    return 0

def selectSeasonalFiles(base_path, seasonal, years, filenames):
    f_base = filenames[0]
    ext = filenames[1]
    all_files = buildFileList(base_path, ext)
    seasons = []
    yrs = []
    for fl in all_files:
        yrs.append(getCHIRPSYear(fl))
        seasons.append(getCHIRPSSeason(fl))
    if not years:
        # do all - get all files, work out what years are included
        years = set(yrs)
    if not seasonal:
        # do all
        seasonal = set(seasons) #['010203', '020304', '030405', '040506', '050607', '060708', '070809', '080910', '091011', '101112', '111201', '120102']

    files = set(all_files)
    fileList = []
    for s in seasonal:
        yrList = []
        for y in years:
            # create file
            fn = "{0}{1}.{2}.{3}{4}".format(base_path, f_base, y, s, ext)
            if fn in files:
                if path.isfile(fn):
                    yrList.append(fn)
        if yrList:
            yrList.sort()
            t = s, yrList
            fileList.append(t)
    fileList.sort()
    return fileList

# Seasonal files have filenames in the format:
# chirps-v2.0.1981.010203.tiff.gz
#
def calcSeasonalAverages(base_path, output_path, functionList = [], filenames = ('chirps-v2.0', '.tif')):
    filesList = selectSeasonalFiles(base_path, [], [], filenames)
    if not filesList:
        print "No files to process. Please check the directory and try again."
        return -1
    syr = 1981
    eyr = 2014
    # for each month, calculate long term average of each season
    seasons = ['010203','020304','030405','040506', '050607', '060708', '070809', '080910', '091011', '101112', '111201', '120102']
    for s, val in enumerate(seasons):
        #for each seasonal
        fl = ((filesList[s])[1])
        if fl:
            sea = fl[0].split('.')[3]
            print "Calculating long term average for ", fl
            newfilename = '{0}.{1}-{2}.{3}'.format(filenames[0], syr, eyr, sea)
            if not functionList:
                # default is to calculate the average
                functionList.append('AVG')
            performCalculations(fl, newfilename, output_path, functionList)
        else:
            print 'No files for season ', val
    return 0

def selectDailyFiles(base_path, start_date, numdays, filenames):
    f_base = filenames[0]
    ext = filenames[1]
    all_files = buildFileList(base_path, ext)
    base = start_date
    date_list = [base - datetime.timedelta(days=x) for x in range(0, numdays)]

    files = set(all_files)
    fileList = []
    for d in date_list:
        # create filename
        fn = path.join(base_path, "{0}.{1}{2}".format(f_base, d.strftime("%Y.%m.%d"), ext))
        if fn in files:
            if path.isfile(fn):
                fileList.append(fn)
    return fileList


def calcDailyStatistics(base_path, output_path, temp_path, functionList = [], start_date = date.today(), filenames = ('chirps-v2.0', '.tif'), output_filenames = ('chirps-v2.0', 'tif'), preci_threshold = 0.5, maxdays = 30):
    filesList = selectDailyFiles(base_path, start_date, maxdays, filenames)
    if not filesList:
        print "No files to process. Please check the directory and try again."
        return -1
    if 'DSLW' in functionList:
        # calculate days since last rain
        daysSinceLast(base_path, output_path, temp_path, filesList, output_filenames, preci_threshold, maxdays)
    return 0