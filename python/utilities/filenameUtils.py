__author__ = 'rochelle'
#!/usr/bin/env python

import re
import functools
import datetime
import dateutil
import calendar

def getFileList():
    fileslist = []

    return fileslist

def _getMonthFromDayOfYear(doy, year):
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy)
    month = '%s'%date.strftime('%m')
    return month

def _getDayFromDayOfYear(doy, year, ignore_leap_year = True):
    if calendar.isleap(year) and ignore_leap_year and doy > 60:
        doy = doy-1
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy)
    day = '%s'%date.strftime('%d')
    return day

def generateOutputFilename(input_filename, in_pattern, out_pattern, ignore_leap_year= True, logger=None):
    _r_in = re.compile(in_pattern)
    _m = _r_in.match(input_filename)
    # get named parameters from output
    params = re.findall('{\w+}', out_pattern)
    # create new dictionary with parameter and value pairs
    ddict = {}
    if not _m:
        new_filename = input_filename
    else:
        for i in params:
            k = i[1:-1] # remove {}
            if k in _m.groupdict():
                ddict[k] = _m.groupdict()[k]
            else:
                # check if need to convert day of year into month, day
                if k == 'month' and 'dayofyear' in _m.groupdict():
                    ddict[k] = str(_getMonthFromDayOfYear(int(_m.groupdict()['dayofyear']), int(_m.groupdict()['year']))).zfill(2)
                elif k == 'day' and 'dayofyear' in _m.groupdict():
                    ddict[k] = str(_getDayFromDayOfYear(int(_m.groupdict()['dayofyear']), int(_m.groupdict()['year']), ignore_leap_year)).zfill(2)
                else:
                    ddict[k] = "" # empty string as default
        new_filename = out_pattern.format(**ddict)
    if logger:
        logger.debug("old_filename: %s", input_filename)
        logger.debug("new_filename: %s", new_filename)
    return new_filename

input = "MOD13A3.A2000032.h27v08.005.2006271173414.hdf"
in_p = '^(?P<product>MOD13A3).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<tile>h\d{2}v\d{2}).(?P<version>\d{3})?.*.(?P<extension>\.hdf)'
#out_p = '^(?P<product>MOD\d{2}A\d{1}).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3})(?P<extension>\.hdf$)'
out_p = '{product}.{year}{dayofyear}.{version}{extension}'
f = generateOutputFilename(input, in_p, out_p)