__author__ = 'rochelle'
#!/usr/bin/env python

import datetime
import errno
import glob
import os
import re
from collections import defaultdict
from subprocess import check_call, CalledProcessError

#import arcpy
import rasterio
import numpy as np
import urllib2
from osgeo import gdal
from pymodis import downmodis
import platform

from utilities import directoryUtils
#from directoryUtils import buildFileList
from longTermAverage import calcAverage, calcMin, calcMax, calcStDev
from utilities import filenameUtils
import rasterUtils
#from directoryUtils import getNewFilename
import gdal_calculations

    # MOD11C3.A2016092.005.2016122120501.hdf

modis_patterns = {
    'download_MOD13A3' : '^(?P<product>MOD13A3).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<tile>h\d{2}v\d{2}).(?P<version>\d{3})?.*.(?P<extension>\.hdf$)',
    'download_MOD11C3' : '^(?P<product>MOD11C3).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3})?.*(?P<extension>\.hdf$)',
    'mosaic_in' : '^(?P<product>MOD\d{2}A\d{1}).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<tile>h\d{2}v\d{2}).(?P<version>\d{3})?.*.(?P<extension>\.hdf$)',
        #'^(?P<product>MOD\d{2}A\d{1}).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3})(?P<extension>\.hdf$)',
    'mosaic_out' : '{product}.{year}.{month}.{day}.{version}{extension}',
    'reproject_in' : '^(?P<product>MOD\d{2}A\d{1}).(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2}).(?P<version>\d{3})(?P<extension>\.hdf$)',
    'reproject_out' : '{product}.{year}.{month}.{day}.{version}{extension}',
#    'mosaic_out': '^(?P<product>MOD\d{2}A\d{1}).(?P<year>\d{4})(?P<dayofyear>\d{3})_(?P<version>\d{3})?.*.(?P<extension>\.tif$)',
    'evi_in': '^(?P<product>MOD\d{2}A\d{1}).(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2}).(?P<version>\d{3})(?P<extension>\.hdf$)',
    'evi_out' : '{product}.{year}.{month}.{day}.{version}.tif',
    'ndvi_in': '^(?P<product>MOD\d{2}A\d{1}).(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2}).(?P<version>\d{3})(?P<extension>\.hdf$)',
    'ndvi_out': '{product}.{year}.{month}.{day}.{version}.tif',
    'crop_in' : '^(?P<country>...)(?P<type>...)(?P<product>MOD\d{2}A\d{1}).(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2}).(?P<version>\d{3}).(?P<subset>?.*)(?P<extension>\.tif$)',
    'crop_out': '{country}{type}{product}.{year}.{month}.{day}.{version}{extension}',
    'lst_in': '^(?P<product>MOD\d{2}C\d{1}).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3})?.*(?P<extension>\.hdf$)',
    'lst_out': '{product}.{year}{dayofyear}.{version}.tif',
}

modis_constants = {
    'ndvi_spectral_subset' : [1],
#    'ndvi_spectral_subset' : 'SPECTRAL_SUBSET = ( 1 0 0 0 0 0 0 0 0 0 0 )',
    'ndvi_subset'          : '1_km_monthly_NDVI',
    'evi_spectral_subset'  : [2],
#    'evi_spectral_subset'  : 'SPECTRAL_SUBSET = ( 0 1 0 0 0 0 0 0 0 0 0 )',
    'evi_subset'           : '1_km_monthly_EVI',
    'lst_day_spectral_subset'  : [1],
    'lst_day_subset'           : '',
    'lst_night_spectral_subset'  : [6],
    'lst_night_subset'           : ''
}


#toolspath = "/Volumes/Rochelle External/WFP/MODIS/MODIS Reprojection Tool/bin/"
from cookielib import CookieJar

# Get MODIS tiles and mosaic into one HDF4Image format file.
# No changes to projection are performed.
def getMODISDataFromURL(output_dir, product, tiles, dates, mosaic_dir,
                        tools_dir = "", logger = None):
    files = None
    m_files = []
    if tiles == '':
        tiles=None

    # # new setup to handle authentication
    # username = 'elninoksp'
    # password = 'elninoKSP2016'
    # password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    # password_manager.add_password(None, "https://urs.earthdata.nasa.gov", username, password)
    #
    # cookie_jar = CookieJar()
    #
    # # Install all the handlers.
    #
    # opener = urllib2.build_opener(
    #     urllib2.HTTPBasicAuthHandler(password_manager),
    #     # urllib2.HTTPHandler(debuglevel=1),    # Uncomment these two lines to see
    #     # urllib2.HTTPSHandler(debuglevel=1),   # details of the requests/responses
    #     urllib2.HTTPCookieProcessor(cookie_jar))
    # urllib2.install_opener(opener)
    # end of new setup to handle authentication

    for d in dates:
        if logger: logger.debug("downloading %s", d)
        _month = d + '-01'
        _folder_date = datetime.datetime.strptime(_month, '%Y-%m-%d').strftime('%Y.%m.%d')
        _new_folder = os.path.join(output_dir, _folder_date)
        # create folder if it doesn't already exist
        if not os.path.exists(_new_folder):
            os.makedirs(_new_folder)
        _delta = 1
        modisDown = downmodis.downModis(destinationFolder=_new_folder, tiles=tiles,
                                        product=product, today=_month, delta=_delta, user='elninoksp', password='elninoKSP2016')
        modisDown.connect()
        _check_files = modisDown.getFilesList(_folder_date)
        if logger: logger.debug("check files: %s", _check_files)
        dl_files = modisDown.checkDataExist(_check_files)
        try:
            modisDown.downloadsAllDay(clean=True)
        except Exception, e:
            if logger: logger.error("Error in pymodis.modisDown.downloadsAllDay")
        modisDown.removeEmptyFiles()
        modisDown.closeFilelist()
        _files = glob.glob(os.path.join(_new_folder, '{product}*.hdf'.format(product=product[:-4])))
        if logger: logger.debug("files: %s", _files)
        if logger: logger.debug("dl_files: %s", dl_files)
        if mosaic_dir:
            # mosaic files
            mosaic_file = mosaicTiles(_files, mosaic_dir, tools_dir)
            m_files.append(mosaic_file)

#    # Retrieve the webpage as a string
#    try:
#        response = urllib2.urlopen(url)
#    except urllib2.HTTPError as e:
#        if logger:
#            logger.debug("Could not retrieve file %s. %s", url, BaseHTTPServer.BaseHTTPRequestHandler.responses[e.code][1])
#    else:
#        # parse response to find directory
#        # get list of files
#        print response
##        nfl = ''
##        output_file = os.path.join(output_dir, nfl)
##        open(output_file, 'wb').write(response.read())
    if mosaic_dir:
        return m_files
    return dl_files

def mosaicTiles(files, output_dir, tools_dir="", overwrite = False, subset=[1,1,0,0,0,0,0,0,0,0,0], ofmt='HDF4Image',
                gdal=False, logger = None):
    # use MRTools
    if tools_dir:
        mrtpath = tools_dir
    else:
        mrtpath = "c:\\MODIS\\bin\\"
    filelist = os.path.join(output_dir, "file_list.txt")
    writeMosaicList(filelist, files)
    new_filename = filenameUtils.generateOutputFilename(os.path.basename(files[0]),
                                                        modis_patterns['mosaic_in'],
                                                        modis_patterns['mosaic_out'], False)

    if not os.path.exists(os.path.normpath(os.path.join(output_dir, new_filename))) or overwrite == True:
        mosaicFiles(os.path.normpath(filelist), os.path.normpath(os.path.join(output_dir, new_filename)), os.path.normpath(mrtpath))

        # reproject mosaic to GEO projection
        param_file = os.path.join(output_dir, os.path.basename(new_filename) + ".prm")
        outputname = os.path.join(output_dir, '{0}_r{1}'.format(os.path.basename(new_filename), os.path.splitext(new_filename)[1]))
        generateParamFile(output_dir, param_file, os.path.normpath(os.path.join(output_dir, new_filename)), outputname)
        reprojectMosaic(param_file, os.path.normpath(mrtpath))
        # remove temp file
        os.remove(os.path.normpath(os.path.join(output_dir, new_filename)))
        os.rename(outputname, os.path.normpath(os.path.join(output_dir, new_filename)))
        os.remove(param_file)

    os.remove(filelist)
    if logger: logger.debug("finished mosaic")
    return new_filename


def getMODISYrAndDoY(filename):
    d = filename.split('.', 2)[1]
    return d

def generateParamFile(wdir, pfile, infile, outfile, extras = []):
    # generate parameter file
    pname = os.path.join(wdir, pfile)
    try:
        pfile = open(pname, 'w')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "some default data"
        # Not a permission error.
        raise
    else:
        with pfile:
            pfile.write('INPUT_FILENAME = "' + os.path.normpath(infile) + '"\n')
            pfile.write('OUTPUT_FILENAME = "' + os.path.normpath(outfile) + '"\n')
            pfile.write('OUTPUT_PROJECTION_TYPE = GEO\n')
            pfile.write('DATUM = WGS84\n')
            pfile.write('\n')
            for s in extras:
                pfile.write('{0}\n'.format(s))
            pfile.close()
    return 0

def tranformToWGS84(base_path, output_path, tools_path, filenames = ('MOD13Q1', '.tif'), out_proj = 'EPSG:4326', projection_text = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'):
    f_base = filenames[0] #'MOD13Q1'
    ext = filenames[1] #'.tif'
    all_files = directoryUtils.buildFileList(base_path, ext)
    if not all_files:
        print 'No files found in ' + base_path + ', please check directory and try again'
        return -1
    for ifl in all_files:
        print "checking transform of {0}".format(ifl)
        raster = gdal.Open(ifl)
        projection = raster.GetProjection()
        print projection
        if projection != projection_text:
            # transform
            try:
                ofl = os.path.join(output_path, ifl)
                pf = platform.system()
                if 'Windows' in pf:
                    check_call([tools_path + 'gdalwarp.exe', '-t_srs', out_proj, ifl, ofl])
                elif 'Linux' in pf:
                    check_call([tools_path + 'gdalwarp', '-t_srs', out_proj, ifl, ofl])
            except CalledProcessError as e:
                print("Error in change projection")
                print(e.output)
                raise

    return 0

def reprojectMODISFile(base_path, outWks, patterns, toolDir):
    # reproject mosaic to GEO projection
    if not patterns:
        patterns = (modis_patterns['reproject_in'], modis_patterns['reproject_out'])
    _all_files = directoryUtils.getMatchingFiles(base_path, patterns[0])
    if not _all_files:
        print 'No files found in ' + base_path + ', please check directory and try again'
        return -1
    for f in _all_files:
        param_file = os.path.join(outWks, os.path.basename(f) + ".prm")
        outputname = os.path.join(outWks, '{0}_r{1}'.format(os.path.basename(f), os.path.splitext(f)[1]))
        generateParamFile(outWks, param_file, f, outputname)
        reprojectMosaic(param_file, os.path.normpath(toolDir))
        # remove temp file
        os.remove(os.path.normpath(os.path.join(outWks, f)))
        os.rename(outputname, os.path.normpath(os.path.join(outWks, f)))
        os.remove(param_file)


def reprojectMosaic(param_file, tools_path, overwrite = False):
    # call resample using parameter file
    try:
        check_call([os.path.join(tools_path,'resample'), '-p', param_file])
    except CalledProcessError as e:
        print("Error in resample")
        print(e.output)
        raise
    return 0

def convertToTiff(ifl, ofl, tools_path, nodata=None, overwrite = False):
    pf = platform.system()
    options = []
    try:
#        ofl = os.path.join(output_path, ifl)
        if pf == 'Windows':
            gdal_translate = os.path.join(tools_path, 'gdal_translate.exe')
        elif pf == 'Linux':
            gdal_translate = os.path.join(tools_path, 'gdal_translate')
        options.append(gdal_translate)
        options.append('-sds')
        if nodata:
            options.append('-a_nodata')
            options.append('{0}'.format(nodata))
        options.append(ifl)
        options.append(ofl)
        check_call(options)
    except CalledProcessError as e:
        print("Error in converting to .tif")
        print(e.output)
        raise


def mosaicFiles(infile, outfile, toolspath):
    # call mrtmosaic using input filename
    try:
        pf = platform.system()
        if 'Windows' in pf:
            check_call([os.path.join(toolspath,'mrtmosaic.exe'), '-i', infile, '-o', outfile, '-s', "1 1"])
        elif 'Linux' in pf:
            check_call([os.path.join(toolspath,'mrtmosaic'), '-i', infile, '-o', outfile, '-s', "1 1"])

    except CalledProcessError as e:
        print("Error in mrtmosaic")
        print(e.output)
        return -1
    return 0

def writeMosaicList(fname, files = []):
    if files:
        try:
            pfile = open(fname, 'w')
        except IOError as e:
            if e.errno == errno.EACCES:
                return "Error creating file " + fname
            # Not a permission error.
            raise
        else:
            with pfile:
                for f in files:
                    pfile.write('"' + f + '"')
                    pfile.write('\n')
                pfile.close()
    return 0

# Mosaic all files with same date/day of year in the directory dname
def mosaicMODIS(base_path, output_path, tools_path, work_path, filenames = ('MOD13Q1', '.hdf')):
    f_base = filenames[0] #'MOD13Q1'
    ext = filenames[1] #'.hdf'
    all_files = directoryUtils.buildFileList(base_path, ext)
    if not all_files:
        print 'No files found in ' + base_path + ', please check directory and try again'
        return -1
    param_file = os.path.join(work_path, f_base + ".prm")
    files_dict = defaultdict(list)
    for fl in all_files:
        if fl.endswith(ext):
            # add file to appropriate place in the dictionary
            yr_doy = getMODISYrAndDoY(fl)
            files_dict[yr_doy].append(fl)
    for i,v in files_dict.iteritems():
        # create a list file for mosaic for each day
        file_list = os.path.join(work_path, f_base + "_" + i + ".lst")
        writeMosaicList(file_list, v)
        mosaicname = os.path.join(output_path, '{0}.{1}.005_m{2}'.format(f_base, i, ext))
        # mosaic files for this day
        if mosaicFiles(file_list, mosaicname, tools_path) == -1:
            print 'Error generating mosaic ' + mosaicname
        else:
            outputname = os.path.join(output_path, '{0}.{1}.005{2}'.format(f_base, i, ext))
            generateParamFile(output_path, param_file, mosaicname, outputname)
            reprojectMosaic(param_file, tools_path)
            # remove temp file
            os.remove(mosaicname)
    return 0

def extractNDVI(base_path, output_path, tools_path,
                patterns = None, suffix = modis_constants['ndvi_subset'], overwrite = False, logger = None):
    if not patterns:
        patterns = (modis_patterns['ndvi_in'], modis_patterns['ndvi_out'])
    new_files = extractSubset(base_path, output_path, tools_path, patterns,
                              modis_constants['ndvi_spectral_subset'], suffix, overwrite, logger)
    return new_files



def extractEVI(base_path, output_path, tools_path,
               patterns = None, suffix = modis_constants['evi_subset'], overwrite = False, logger = None):
    if not patterns:
        patterns = (modis_patterns['evi_in'], modis_patterns['evi_out'])
    new_files = extractSubset(base_path, output_path, tools_path, patterns,
                              modis_constants['evi_spectral_subset'], suffix, overwrite, -9999, logger)
    return new_files


def extractSubset(base_path, output_path, tools_path,
                  patterns, subset, subset_name, overwrite = False, nodata=None, logger = None):
    _all_files = directoryUtils.getMatchingFiles(base_path, patterns[0])
    if not _all_files:
        print 'No files found in ' + base_path + ', please check directory and try again'
        return -1
#    _pfl = os.path.join(base_path, 'fileslist' + ".prm")
    new_files = []
#    _params = [subset]
    for _ifl in _all_files:
        # generate parameter file
        _nfl = filenameUtils.generateOutputFilename(os.path.basename(_ifl), patterns[0], patterns[1])
        _ofl = os.path.join(output_path, _nfl)
        _checkfl = "{0}.{1}{2}".format(os.path.splitext(_ofl)[0], subset_name, os.path.splitext(_ofl)[1])
        if not os.path.exists(_checkfl) or overwrite == True:
            try:
                src_ds = gdal.Open(_ifl)
            except RuntimeError, e:
                if logger: logger.debug('Unable to open file')
                return None
            sds = src_ds.GetSubDatasets()
            if logger: logger.debug("Number of bands: %s",src_ds.RasterCount)
#            generateParamFile(base_path, _pfl, _ifl, _ofl, _params)
#            reprojectMosaic(_pfl, tools_path)
            convertToTiff(_ifl, _ofl, tools_path, nodata)
#            ss = [1]
            for idx, sbs in enumerate(sds): #range(src_ds.RasterCount):
                if logger: logger.debug("Subdataset: %s", sbs[0])
                # get subset name (without spaces)
                _n = (sbs[0].rsplit(':', 1)[1]).replace(' ', '_')
#                _n = _n.replace(' ', '_')
                _rf = "{0}.{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], _n, os.path.splitext(_ofl)[1])
#                _cf = "{0}_{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], str(idx+1).zfill(2), os.path.splitext(_ofl)[1])
                # GDAL 1.10
                _cf = "{0}{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], os.path.splitext(_ofl)[1], str(idx+1).zfill(1))
                if not os.path.exists(os.path.join(output_path, _cf)):
                    _cf = "{0}_{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], str(idx+1), os.path.splitext(_ofl)[1])
                if idx+1 not in subset:
                    # remove un-needed files (including .aux & .aux.xml)
                    os.remove(os.path.join(output_path, _cf))
                    _aux_f = os.path.join(output_path,"{0}.aux.xml".format(_cf))
                    if os.path.exists(_aux_f):
                        os.remove(_aux_f)
#            for i in range(2,18):
#                rf = "{0}_{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], str(i).zfill(2), os.path.splitext(_ofl)[1])
#                os.remove(os.path.join(output_path, rf))
                else:
                    # keep this file - rename with subset name
                    os.rename(os.path.join(output_path, _cf), os.path.join(output_path, _rf))
                    _aux_f = os.path.join(output_path,"{0}.aux.xml".format(_cf))
                    if os.path.exists(_aux_f):
                        os.rename(_aux_f, os.path.join(output_path, "{0}.aux.xml".format(_rf)))
                    new_files.append(_rf)
    return new_files


def extractLSTDay(base_path, output_path, tools_path, patterns = None, overwrite = False, suffix = '', logger=None):

    if not patterns:
        patterns = (modis_patterns['lst_in'], modis_patterns['lst_out'])
    new_files = extractSubset(base_path, output_path, tools_path, patterns,
                              modis_constants['lst_day_spectral_subset'], suffix, overwrite, logger=None)

    return new_files

def extractLSTNight(base_path, output_path, tools_path, patterns = None, overwrite = False, suffix = '', logger=None):
    if not patterns:
        patterns = (modis_patterns['lst_in'], modis_patterns['lst_out'])
    new_files = extractSubset(base_path, output_path, tools_path, patterns,
                              modis_constants['lst_night_spectral_subset'], suffix, overwrite, logger=None)
    return new_files

def calcAverageOfDayNight_filter(dayDir, nightDir, outDir, patterns, logger=None):
    # find file from pattern
    day_pattern = patterns[0]
    night_pattern = patterns[1]
    average_pattern = patterns[2]
    day_list = directoryUtils.getMatchingFiles(base_dir=dayDir, filter=day_pattern)
    night_list = directoryUtils.getMatchingFiles(base_dir=nightDir, filter=night_pattern)
    if logger:
        logger.debug("Day files: %s", day_list)
        logger.debug("Night files: %s", night_list)

    for fl in day_list:
        # find matching night file
        # find date stamp in day file
        _r_in = re.compile(day_pattern)
        _r_in_night = re.compile(night_pattern)
        f = os.path.basename(fl)
        _m = _r_in.match(f)
        year = 0
        dayofyear = 0
        if 'year' in _m.groupdict():
            year = _m.groupdict()['year']
        if 'dayofyear' in _m.groupdict():
            dayofyear = _m.groupdict()['dayofyear']

        for nfl in night_list:
            _mn = _r_in_night.match(os.path.basename(nfl))
            if 'year' in _mn.groupdict() and _mn.groupdict()['year'] == year:
                # matched year
                if 'dayofyear' in _mn.groupdict() and _mn.groupdict()['dayofyear'] == dayofyear:
                    # matched day of year
                    avg_fl = filenameUtils.generateOutputFilename(os.path.basename(fl), day_pattern, average_pattern)
                    calcAverageOfDayNight(fl, nfl, os.path.join(outDir, avg_fl))
                    break
    return 0




def calcAverageOfDayNight(dayFile, nightFile, avgFile):
    print "calcAverage: ", dayFile, nightFile
    #an empty array/vector in which to store the different bands
    rasters = []
    #open rasters
    rasters.append(dayFile)
    rasters.append(nightFile)
    outRaster = arcpy.sa.CellStatistics(rasters, "MEAN", "DATA")
    # Save the output
    outRaster.save(avgFile)
    print "saved avg in: ", avgFile
    return 0

def calcAverageOfDayNight_os(dayFile, nightFile, avgFile, gdal_path):
    print "calcAverage: ", dayFile, nightFile
    dst_filename = "{0}.tmp{1}".format(os.path.splitext(avgFile)[0], os.path.splitext(avgFile)[1])
    with rasterio.open(dayFile) as day_r:
        profile = day_r.profile.copy()
#        profile.update(dtype=rasterio.uint32)
        profile.update(NoData=0)
        day_a = day_r.read(1, masked=False)
        with rasterio.open(nightFile) as night_r:
            night_a = night_r.read(1, masked=False)
            dst_r2 = np.where(np.logical_and(day_a==0, night_a==0), 0,
                              np.where(night_a==0, day_a,
                                       np.where(day_a==0, night_a, (day_a + night_a)/2)))
            with rasterio.open(dst_filename, 'w', **profile) as dst:
                dst.write(dst_r2.astype(rasterio.uint16), 1)
            rasterUtils.setRasterNoDataValues(dst_filename, avgFile, gdal_path, -9999, None, 'Int32', True)

def calcAverageOfDayNight_dir(output_dir, dayDir, nightDir, patterns = (None, None)):
    print "calcAverage of Day & Night for directory: ", dayDir, nightDir
    #an empty array/vector in which to store the different bands
    if patterns[0]:
        all_dayfiles = directoryUtils.getMatchingFiles(os.path.dirname(dayDir), patterns[0])
    else:
        all_dayfiles = directoryUtils.buildFileList(os.path.dirname(dayDir), '.tif')
    if patterns[0]:
        all_nightfiles = directoryUtils.getMatchingFiles(os.path.dirname(nightDir), patterns[0])
    else:
        all_nightfiles = directoryUtils.buildFileList(os.path.dirname(nightDir), '.tif')
#    for df in all_dayfiles:

    return 0


def matchDayNightFiles(dayPath, nightPath, outPath, patterns = (None, None), open_src = False, gdal_path=None):
#    dayFiles = list(os.listdir(dayPath))
    nightFiles = set(os.listdir(nightPath))
    if patterns[0]:
        if not os.path.isdir(dayPath):
            dayFiles = directoryUtils.getMatchingFiles(os.path.dirname(dayPath), patterns[0])
        else:
            dayFiles = directoryUtils.getMatchingFiles(dayPath, patterns[0])
    else:
        dayFiles = list(os.listdir(dayPath))
    print "Day files: ", dayFiles
    print "Night files: ", nightFiles

    for fl in dayFiles:
        # find matching night file
        d_fl, ext = os.path.splitext(os.path.basename(os.path.normpath(fl)))
        if (ext == '.tif'):
            d_t = d_fl.rpartition('.')
            n_fl = d_t[0] + d_t[1] + 'LST_Night_CMG' + ext
            if (n_fl) in nightFiles:
                avg_fl = os.path.join(outPath, d_t[0] + d_t[1] + 'avg' + ext)
                dp = os.path.join(dayPath, d_fl+ext)
                np = os.path.join(nightPath, n_fl)
                if open_src:
                    calcAverageOfDayNight_os(dp, np, avg_fl, gdal_path)
                else:
                    calcAverageOfDayNight(dp, np, avg_fl)
    return 0

def performCalculations(fileList, baseName, outputPath, functionList):
    for f in functionList:
        if f == 'AVG':
            newfile = '{0}.avg.tif'.format(baseName)
            ofl = os.path.join(outputPath, newfile)
            calcAverage(fileList, ofl)
        elif f == 'STD':
            newfile = '{0}.std.tif'.format(baseName)
            ofl = os.path.join(outputPath, newfile)
            calcStDev(fileList, ofl)
        elif f == 'MAX':
            newfile = '{0}.max.tif'.format(baseName)
            ofl = os.path.join(outputPath, newfile)
            calcMax(fileList, ofl)
        elif f == 'MIN':
            newfile = '{0}.min.tif'.format(baseName)
            ofl = os.path.join(outputPath, newfile)
            calcMin(fileList, ofl)
        else:
            print f, ' is not a valid function.'
    return 0

def getMonthFromDayOfYear(doy, year):
    ref = datetime.datetime(year, 1, 1)
    m = datetime.datetime.strftime(ref + datetime.timedelta(doy - 1), "%m")
    return m

def calcLongTermAverageTemp(base_path, output_path, functionList = [], filenames = ('idn_cli_MOD11C3', '.tif'), pattern = None):
    # png_cli_MOD11C3.A2000061.005.2007177231646.avg
    ext = filenames[1]
    all_files = directoryUtils.getMatchingFiles(base_path, pattern)
#    all_files = directoryUtils.buildFileList(base_path, ext)
    # do all - get all files, work out what years are included
    yrs = []
    days = []
    daysOfYear = defaultdict(list)
    for fl in all_files:
        # fl includes directory, get just filename
        fn = os.path.basename(fl)
        ydoy = getMODISYrAndDoY(fn)
        y = int(ydoy[1:5])
        d = int(ydoy[-3:])
        if y%4 == 0 and d>60: # leap year and day after Feb 29, subtract one from day
            d = d-1
        daysOfYear[str("{0:03d}".format(d))].append(fl)
        yrs.append(y)

    years = set(yrs)
    syr = min(years) #1981
    eyr = max(years)
    numyrs = eyr - syr

    for dd in daysOfYear.keys():
#        newfilename = '{0}.{1}-{2}.{3}.{4}yrs'.format(filenames[0], syr, eyr, dd, str(numyrs))
        mth = getMonthFromDayOfYear(int(dd), 2001)
        newfilename = '{0}.{1}-{2}.{3}.{4}yrs'.format(filenames[0], syr, eyr, mth, str(numyrs))
        if not functionList:
            # default is to calculate the minimum and maximum
            functionList.append('MIN')
            functionList.append('MAX')
        performCalculations(daysOfYear[dd], newfilename, output_path, functionList)

    return 0