__author__ = 'rochelle'
#!/usr/bin/env python

import re
import functools

def getFileList():
    fileslist = []

    return fileslist

def generateOutputFilename(input_filename, in_pattern, out_pattern):
    _r_in = re.compile(in_pattern)
    _m = _r_in.match(input_filename)
    # get named parameters from output
    params = re.findall('{\w+}', out_pattern)
    # create new dictionary with parameter and value pairs
    ddict = {}
    for i in params:
        k = i[1:-1] # remove {}
        if _m and k in _m.groupdict():
            ddict[k] = _m.groupdict()[k]
        else:
            ddict[k] = "" # empty string as default
    new_filename = out_pattern.format(**ddict)
    print "old_filename: ", input_filename
    print "new_filename: ", new_filename
    return new_filename

input = "MOD13A3.A2000032.h27v08.005.2006271173414.hdf"
in_p = '^(?P<product>MOD13A3).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<tile>h\d{2}v\d{2}).(?P<version>\d{3})?.*.(?P<extension>\.hdf)'
#out_p = '^(?P<product>MOD\d{2}A\d{1}).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3})(?P<extension>\.hdf$)'
out_p = '{product}.{year}{dayofyear}.{version}{extension}'
f = generateOutputFilename(input, in_p, out_p)