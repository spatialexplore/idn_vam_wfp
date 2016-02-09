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
from os import path
from fnmatch import filter
import collections

from python.utilities.directoryUtils import buildFileList
from python.longTermAverage import calcAverage, calcMin, calcMax, calcStDev


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


# MOD13Q1.A2002033.h27v08.005.2008293034945.hdf
def getEVIYear(filename):
    d = filename.split('.', 2)[1]
    yr = (d[:5])[-4:]
    return yr

# MOD13Q1.A2002033.h27v08.005.2008293034945.hdf
def getEVIDoY(filename):
    d = filename.split('.', 2)[1]
    doy = d[-3:]
    return doy

def selectEVIFiles(base_path, doy, years, filenames):
    f_base = filenames[0] #'idn_phy_MOD13Q1'
    ext = filenames[1] #'.tif'
    all_files = buildFileList(base_path, ext)
    yrs = []
    dy = []
    for fl in all_files:
        yrs.append(getEVIYear(fl))
        dy.append(getEVIDoY(fl))

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
def calcEVIAverages(base_path, output_path, functionList = [], filenames = ('idn_phy_MOD13Q1', '.tif')):
    resultsList = selectEVIFiles(base_path, [], [], filenames)
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
            newfilename = '{0}.A{1}-{2}{3}.005.250m_16_days_EVI'.format(filenames[0], syr, eyr, d[0])
            if not functionList:
                # default is to calculate the average
                functionList.append('AVG')
            performCalculations(fl, newfilename, output_path, functionList)
    return 0

def calcLongTermAverageEVI(base_path, output_path, functionList = [], filenames = ('idn_cli_MOD13A3', '.tif')):
    # tls_phy_MOD13A3.A2014182_005.1_km_monthly_EVI.tif
    ext = filenames[1]
    all_files = buildFileList(base_path, ext)
    # do all - get all files, work out what years are included
    yrs = []
    daysOfYear = collections.defaultdict(list)
    suffix = all_files[0].rsplit('.', 3)[2]

    for fl in all_files:
        p, f = path.split(fl)
        ydoy = f.split('.', 2)[1]
        y = int(ydoy[1:5])
        d = int(ydoy[-7:-4])
        if y%4 == 0 and d>60: # leap year and day after Feb 29, subtract one from day
            d = d-1
        daysOfYear[str("{0:03d}".format(d))].append(fl)
        yrs.append(y)

    years = set(yrs)
    syr = min(years) #1981
    eyr = max(years)
    numyrs = eyr - syr

    for dd in daysOfYear.keys():
        newfilename = '{0}.{1}-{2}.{3}.{4}.{5}yrs'.format(filenames[0], syr, eyr, dd, suffix, str(numyrs))
        if not functionList:
            # default is to calculate the minimum and maximum
            functionList.append('MIN')
            functionList.append('MAX')
        performCalculations(daysOfYear[dd], newfilename, output_path, functionList)

    return 0
