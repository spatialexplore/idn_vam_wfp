#!/usr/bin/env python
"""
SYNOPSIS

    ProcessRSData [-h,--help] [-v,--verbose] [--version]

DESCRIPTION

    This script reads a Yaml config file and processes the
    contents. The config file may contain a set of one or
    more 'run' instructions for processing of remote
    sensing data.

EXAMPLES

    TODO: Show some examples of how to use this script.

EXIT STATUS

    TODO: List exit codes

AUTHOR

    Rochelle O'Hagan <spatialexplore@gmail.com>

LICENSE

    This script is in the public domain, free from copyrights or restrictions.

VERSION

    $Id$
"""

import logging
import optparse
import os
import sys
import time
import traceback
from datetime import date

import arcpy
import yaml

import arcPyUtils
from remotesensing import ndviUtils, eviUtils, modisUtils, chirpsUtils#, trmmUtils #.calcLongTermAverageNDVI

#from eviUtils import calcLongTermAverageEVI, calcMonthlyLongTermAverageEVI
#from modisUtils import mosaicMODIS, cropMODIS, extractNDVI, extractEVI, calcLongTermAverageTemp, tranformToWGS84, getMODISDataFromURL
#import chirpsUtils
import rasterUtils
#import trmmUtils
from utilities import directoryUtils
from precipitationAnalysis import calcRainfallAnomaly, daysSinceLast
from vegetationAnalysis import calcVCI, calcTCI, calcTCI_os, calcVHI

logger = logging.getLogger('ProcessRSData')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def configFileError(msg, e):
    print "Error in config file {0} : {1}".format(msg, str(e))
    return 0

def processExtract(process, config):
    if 'input_dir' in process:
        inw = process['input_dir']
    if 'output_dir' in process:
        outw = process['output_dir']
    if 'input_extension' in process:
        ext = process['input_extension']
    if 'input_prefix' in process:
        prefix = process['input_prefix']
    if 'output_ext' in process:
        output_ext = process['output_ext']
    if 'output_prefix' in process:
        output_prefix = process['output_prefix']
    if 'shapefile' in process:
        shapefile = process['shapefile']
    gdal_path = config['EXTRACT']['directory']['GDAL']
    if ext.endswith(".gz"):
        # need to unzip first
        directoryUtils.unzipFiles(inw, ".gz")
        ext = ext[:-3]
    filenames = (prefix, ext)
    output_filenames = (output_prefix, output_ext)
    rasterUtils.clipRastersInDirToShape(inw, outw, shapefile, filenames, output_filenames, gdal_path)
    return 0

def processCHIRPS(process, cfg):
# legacy variables - these need to be refactored
    prefix = cfg['CHIRPS']['filenames']['input_prefix']
    ext = cfg['CHIRPS']['filenames']['input_extension']
    if 'input_extension' in process:
        ext = process['input_extension']
    if 'input_prefix' in process:
        prefix = process['input_prefix']
    filenames = (prefix, ext)
    if 'input_dir' in process:
        inWks = process['input_dir']
    else:
        inWks = None
    if 'output_dir' in process:
        outWks = process['output_dir']
    else:
        outWks = None
    temp_path = cfg['directory']['temp']
    arcpy.env.workspace = inWks
    if 'functions' in process:
        funcs = process['functions']
    else:
        funcs = None
    if process['type'] == 'longterm_average':
        if process['interval'] == 'monthly':
            print "Processing CHIRPS monthly data"
            chirpsUtils.calcMonthlyAverages(inWks, outWks, funcs, filenames)
        elif process['interval'] == 'seasonal':
            print "Processing CHIRPS seasonal data"
            chirpsUtils.calcSeasonalAverages(inWks, outWks, funcs, filenames)
        elif process['interval'] == 'pentad':
            print "Processing CHIRPS pentad data"
            chirpsUtils.calcPentadAverages(inWks, outWks, funcs, filenames)
        elif process['interval'] == 'dekad':
            print "Processing CHIRPS dekad data"
            chirpsUtils.calcDekadAverages(inWks, outWks, funcs, filenames)
        elif process['interval'] == 'dekad_range':
            print "Processing CHIRPS dekad data for custom date range"
            startDate = []
            endDate = []
            if 'start_dekad_month' in process:
                startDate = process['start_dekad_month']
            if 'end_dekad_month' in process:
                endDate = process['end_dekad_month']
            years = []
            if 'years_between' in process:
                years = process['years_between']
            chirpsUtils.calcLongTermAverage_Dekad_Dates(inWks, outWks, startDate, endDate, years, funcs, filenames)
    elif process['type'] == 'accumulation':
        if process['interval'] == 'dekad_range':
            print "Processing CHIRPS dekad data for custom date range"
            start = []
            end = []
            if 'start_dekad_month_year' in process:
                st = process['start_dekad_month_year']
                start = [int(st[0]), int(st[1]), int(st[2])]
            else:
                print "Error: start_dekad_month_year is missing"
                raise
            if 'end_dekad_month_year' in process:
                e = process['end_dekad_month_year']
                end = [int(e[0]), int(e[1]), int(e[2])]
            else:
                print "Error: start_dekad_month_year is missing"
                raise
            chirpsUtils.calcDekadAccumulation_Dates(inWks, outWks, start, end, filenames)
    elif process['type'] == 'daily':
        print "Processing CHIRPS daily data"
        threshold = cfg['CHIRPS']['thresholds']['precipitation_threshold']
        ndays = cfg['CHIRPS']['thresholds']['max_days_to_process']
        chirpsUtils.calcDailyStatistics(inWks, outWks, temp_path, funcs, date(2015,06,30), filenames, filenames, threshold, ndays)
    elif process['type'] == 'download':
        if process['interval'] == 'monthly':
            print "Downloading CHIRPS monthly data"
            try:
                dates = process['dates']
            except Exception, e:
                dates = ""
            # if 'start_date' in process:
            #     startDate = process['start_date']
            # else:
            #     startDate = None
            # if 'end_date' in process:
            #     endDate = process['end_date']
            # else:
            #     endDate = None
            chirpsUtils.downloadMonthlyDataFromFTP(outWks, dates)
        elif process['interval'] == 'seasonal':
            try:
                dates = process['dates']
            except Exception, e:
                dates = ""
            print "Downloading CHIRPS seasonal data"
            chirpsUtils.downloadSeasonalDataFromFTP(outWks, dates)
        elif process['interval'] == 'pentad':
            print "Downloading CHIRPS pentad data"

        elif process['interval'] == 'dekad':
            try:
                dates = process['dates']
            except Exception, e:
                dates = ""
            print "Downloading CHIRPS dekad data"
            chirpsUtils.downloadDekadDataFromFTP(outWks, dates)
        elif process['interval'] == 'daily':
            try:
                dates = process['dates']
            except Exception, e:
                dates = ""
            print "Downloading CHIRPS daily data"
            chirpsUtils.downloadDailyDataFromFTP(outWks, dates)



    elif process['type'] == 'crop':
        print "Cropping raster to boundary"
        if 'input_file' in process:
            inFile = process['input_file']
        else:
            inFile = None
        if 'output_file' in process:
            outFile = process['output_file']
        else:
            outFile = None
        if 'boundary_file' in process:
            shpfile = process['boundary_file']
        else:
            shpfile = None
        if inFile and outFile and shpfile:
            if os.path.splitext(inFile)[1] == '.gz':
                # need to unzip file first
                inFile = directoryUtils.unzipFile(inFile)
            gdal_path = cfg['directory']['GDAL']
            rasterUtils.clipRasterToShp(shpfile, inFile, outFile, gdal_path)
    return 0

def processTEMP(process, cfg):
    inWks = process['input_dir']
    outWks = process['output_dir']
    arcpy.env.workspace = inWks
    funcs = process['functions']
    filenames = (process['input_prefix'], process['input_ext'])
    if not funcs:
        funcs = ['MIN', 'MAX']
    modisUtils.calcLongTermAverageTemp(inWks, outWks, funcs, filenames)
    return 0

def processNDVI(process, cfg):
    print 'Calculate NDVI Long Term Averages'
    inWks = process['input_dir']
    outWks = process['output_dir']
    arcpy.env.workspace = inWks
    if 'functions' in process:
        funcs = process['functions']
    else:
        funcs = ['AVG, MIN, MAX']
    if 'EVI' in cfg and 'filenames' in cfg['EVI'] and 'prefix' in cfg['EVI']['filenames']:
        out_prefix = cfg['EVI']['filenames']['prefix']
    if 'EVI' in cfg and 'filenames' in cfg['EVI'] and 'extension' in cfg['EVI']['filenames']:
        out_ext = cfg['EVI']['filenames']['extension']
    if 'output_prefix' in process:
        out_prefix = process['output_prefix']
    if 'output_ext' in process:
        out_ext = process['output_ext']
    filenames = (out_prefix, out_ext)

    ndviUtils.calcLongTermAverageNDVI(inWks, outWks, funcs, filenames)
    return 0

def processEVI(process, cfg):
    print 'Calculate EVI Long Term Averages'
    inWks = process['input_dir']
    outWks = process['output_dir']
    arcpy.env.workspace = inWks
    if 'interval' in process:
        interval = process['interval']
    else:
        interval = 'MONTHLY'
    if 'functions' in process:
        funcs = process['functions']
    else:
        funcs = ['AVG, MIN, MAX']
    if 'EVI' in cfg and 'filenames' in cfg['EVI'] and 'prefix' in cfg['EVI']['filenames']:
        out_prefix = cfg['EVI']['filenames']['prefix']
    if 'EVI' in cfg and 'filenames' in cfg['EVI'] and 'extension' in cfg['EVI']['filenames']:
        out_ext = cfg['EVI']['filenames']['extension']
    if 'output_prefix' in process:
        out_prefix = process['output_prefix']
    if 'output_ext' in process:
        out_ext = process['output_ext']
    filenames = (out_prefix, out_ext)

    if interval == 'MONTHLY':
        eviUtils.calcMonthlyLongTermAverageEVI(inWks, outWks, funcs, filenames)
    else:
        eviUtils.calcLongTermAverageEVI(inWks, outWks, funcs, filenames)
    return 0

def processMODIS(process, cfg):
    if process['type'] == 'mosaic':
        logger.debug("Mosaic MODIS data")
        inWks = process['input_dir']
        outWks = process['output_dir']
        toolDir = None
        try:
            workDir = cfg['MODIS']['directory']['working']
        except Exception, e:
            workDir = outWks
        if 'MRT_dir' in process:
            toolDir = process['MRT_dir']
        elif 'directory' in cfg:
            if 'MRT' in cfg['directory']:
                toolDir = cfg['directory']['MRT']
        filenames = (cfg['MODIS']['filenames']['prefix'], cfg['MODIS']['filenames']['extension'])
        modisUtils.mosaicMODIS(inWks, outWks, toolDir, workDir, filenames)
    # elif process['type'] == 'crop':
    #     logger.debug("Crop MODIS data")
    #     try:
    #         prefix = process['prefix']
    #     except Exception, e:
    #         prefix = cfg['MODIS']['filenames']['prefix']
    #
    #     try:
    #         extension = process['extension']
    #     except Exception, e:
    #         extension = cfg['MODIS']['filenames']['extension']
    #     try:
    #         toolDir = cfg['directory']['GDAL']
    #     except Exception, e:
    #         print "No GDAL directory set. Using {0}".format(toolDir)
    #
    #     if 'file_pattern' in process:
    #         pattern = process['file_pattern']
    #     else:
    #         pattern = r'^(?P<prefix>MOD\d{2}.\d.)(?P<datestamp>\d{4}[.]\d{2}[.]\d{2})(?P<ext>.*)'
    #     if 'output_pattern' in process:
    #         out_pattern = process['output_pattern']
    #     else:
    #         out_pattern = r'{prefix}{mod_prefix}{datestamp}.{suffix}'
    #     patterns = (pattern, out_pattern)
    #
    #     try:
    #         inWks = process['input_dir']
    #     except Exception, e:
    #         print "No input directory 'input_dir' set."
    #         raise
    #     try:
    #         outWks = process['output_dir']
    #     except Exception, e:
    #         print "No output directory 'output_dir' set."
    #         raise
    #     try:
    #         boundFile = process['boundary_file']
    #     except Exception, e:
    #         print "No boundary file 'boundary_file' set."
    #         raise
    #     filenames = (prefix, extension)
    #     if 'output_prefix':
    #         out_prefix = process['output_prefix']
    #     else:
    #         out_prefix = cfg['MODIS']['filenames']['output']
    #     if 'output_extension':
    #         output_extension = '.tif'
    #     else:
    #         output_extension = cfg['MODIS']['filenames']['output_ext']
    #     out_filenames = (out_prefix, output_extension)
    #
    #     modisUtils.cropMODIS(inWks, outWks, boundFile, toolDir, filenames, out_filenames, patterns)
    elif process['type'] == 'extract':
        logger.debug("Extract layer from MODIS data")
        try:
            inWks = process['input_dir']
        except Exception, e:
            print "No input directory 'input_dir' set."
            raise
        try:
            outWks = process['output_dir']
        except Exception, e:
            print "No output directory 'output_dir' set."
            raise
        if 'file_pattern' in process:
            pattern = process['file_pattern']
        else:
            pattern = None #r'^(?P<datestamp>\d{4}[.]\d{2}[.]\d{2})?.*'
        if 'output_pattern' in process:
            out_pattern = process['output_pattern']
        else:
            out_pattern = None #r'{prefix}.{datestamp}_005{ext}'
        if pattern == None or out_pattern == None:
            patterns = None
        else:
            patterns = (pattern, out_pattern)
        toolDir = None
        try:
            toolDir = cfg['directory']['GDAL']
        except Exception, e:
            configFileError("GDAL directory", e)
        if process['layer'] == 'NDVI':
            modisUtils.extractNDVI(inWks, outWks, toolDir, patterns,logger=logger)
        elif process['layer'] == 'EVI':
            modisUtils.extractEVI(inWks, outWks, toolDir, patterns, logger=logger)
        elif process['layer'] == 'LST_Day':
            if 'GDAL_dir' in process:
                toolDir = process['GDAL_dir']
            elif 'directory' in cfg:
                try:
                    toolDir = cfg['directory']['GDAL']
                except Exception, e:
                    logger.error("No GDAL directory specified.")
                    raise
#                if 'GDAL' in cfg['directory']:
#                    toolDir = cfg['directory']['GDAL']

            modisUtils.extractLSTDay(inWks, outWks, toolDir, patterns, logger=logger)
        elif process['layer'] == 'LST_Night':
            if 'GDAL_dir' in process:
                toolDir = process['GDAL_dir']
            elif 'directory' in cfg:
                try:
                    toolDir = cfg['directory']['GDAL']
                except Exception, e:
                    logger.error("No GDAL directory specified.")
                    raise
            modisUtils.extractLSTNight(inWks, outWks, toolDir, patterns, logger=logger)
    elif process['type'] == 'temperature':
        print "Compute long-term average from MODIS Temperature data"
        inWks = process['input_dir']
        outWks = process['output_dir']
        out_prefix = cfg['MODIS']['filenames']['prefix']
        out_ext = cfg['MODIS']['filenames']['extension']
        if 'output_prefix' in process:
            out_prefix = process['output_prefix']
        if 'output_ext' in process:
            out_ext = process['output_ext']
        filenames = (out_prefix, out_ext)
        funcs = []
        if 'functions' in process:
            funcs = process['functions']
        if not funcs:
            funcs = ['MIN', 'MAX']
        if 'file_pattern' in process:
            pattern = process['file_pattern']
        modisUtils.calcLongTermAverageTemp(inWks, outWks, funcs, filenames, pattern)
    elif process['type'] == 'day_night_average':
        print "Calculate Average temperature from Day & Night"
        if 'filename_day' in process:
            day_file = process['filename_day']
        else:
            day_file = None
        if 'day_pattern' in process:
            day_pattern = process['day_pattern']
        else:
            day_pattern = None
        if 'filename_night' in process:
            night_file = process['filename_night']
        else:
            night_file = None
        if 'night_pattern' in process:
            night_pattern = process['night_pattern']
        else:
            night_pattern = None
        if 'output_filename' in process:
            out_filename = process['output_filename']
        else:
            out_filename = None
        if 'output_pattern' in process:
            out_pattern = process['output_pattern']
        modisUtils.calcAverageOfDayNight(day_file, night_file, out_filename)
    elif process['type'] == 'average_temperature':
        print "Calculate average of day & night temperature"
        day_dir = process['directory_day']
        night_dir = process['directory_night']
        output_dir = process['directory_output']
        if 'day_pattern' in process:
            day_pattern = process['day_pattern']
        else:
            day_pattern = None
        if 'night_pattern' in process:
            night_pattern = process['night_pattern']
        else:
            night_pattern = None
        if 'output_pattern' in process:
            output_pattern = process['output_pattern']
        else:
            output_pattern = None
        patterns = (day_pattern, night_pattern, output_pattern)
        modisUtils.calcAverageOfDayNight_filter(day_dir, night_dir, output_dir, patterns)
    elif process['type'] == 'temp_average':
        print "Calculate Average temperature from Day & Night for directory"
        day_dir = process['directory_day']
        night_dir = process['directory_night']
        output_dir = process['directory_output']
        if 'input_pattern' in process:
            input_pattern = process['input_pattern']
        else:
            input_pattern = None
        if 'output_pattern' in process:
            output_pattern = process['output_pattern']
        else:
            output_pattern = None
        patterns = (input_pattern, output_pattern)
#        modisUtils.calcAverageOfDayNight_dir(output_dir, day_dir, night_dir, patterns)
        modisUtils.matchDayNightFiles(day_dir, night_dir, output_dir)
    elif process['type'] == 'download':
        logger.debug("Downloading MODIS data")
        outWks = process['output_dir']
        try:
            product = process['product']
        except Exception, e:
            product = 'MOD13A3.005'
        try:
            tiles = process['tiles']
        except Exception, e:
#            tiles = "h27v08, h27v09, h27v10, h28v08, h28v09, h28v10, h29v08, h29v09, h29v10, h30v08, h30v09, h30v10, h31v08, h31v09, h31v10, h32v08, h32v09, h32v10"
            tiles = ""
        try:
            dates = process['dates']
        except Exception, e:
            dates = ""
        try:
            mosaic_dir = process['mosaic_dir']
        except Exception, e:
            mosaic_dir = ""
        try:
            url_base = process['url_base']
        except Exception, e:
            url_base = 'http://e4ftl01.cr.usgs.gov/MOLT/' + product
        if 'MRT_dir' in process:
            toolDir = process['MRT_dir']
        elif 'directory' in cfg:
            if 'MRT' in cfg['directory']:
                toolDir = cfg['directory']['MRT']
        modisUtils.getMODISDataFromURL(outWks, product, tiles, dates, mosaic_dir, toolDir, logger)
    return 0

def processAnalysis(process, cfg):
    if process['type'] == 'rainfall_anomaly':
        print "Compute monthly rainfall anomaly"
        cur_file = process['current_file']
        lta_file = process['longterm_avg_file']
        out_file = process['output_file']
        calcRainfallAnomaly(cur_file, lta_file, out_file)
    elif process['type'] == 'VCI':
        print "Compute Vegetation Condition Index"
        cur_file = process['current_file']
        evi_max_file = process['EVI_max_file']
        evi_min_file = process['EVI_min_file']
        out_file = process['output_file']
        calcVCI(cur_file, evi_max_file, evi_min_file, out_file)
    elif process['type'] == 'TCI':
        print "Compute Temperature Condition Index"
        cur_file = process['current_file']
        lst_max_file = process['LST_max_file']
        lst_min_file = process['LST_min_file']
        out_file = process['output_file']
        if 'open_source' in process:
            calcTCI_os(cur_file, lst_max_file, lst_min_file, out_file)
        else:
            calcTCI(cur_file, lst_max_file, lst_min_file, out_file)
    elif process['type'] == 'VHI':
        print "Compute Vegetation Health Index"
        vci_file = process['VCI_file']
        tci_file = process['TCI_file']
        out_file = process['output_file']
        calcVHI(vci_file, tci_file, out_file)
    return 0

def processRaster(process, cfg):
    if process['type'] == 'projection':
        inWks = process['input_dir']
        outWks = process['output_dir']
        out_prefix = cfg['MODIS']['filenames']['prefix']
        out_ext = cfg['MODIS']['filenames']['extension']
        if 'output_prefix' in process:
            out_prefix = process['output_prefix']
        if 'output_ext' in process:
            out_ext = process['output_ext']
        filenames = (out_prefix, out_ext)
        try:
            projection = process['projection']
        except Exception, e:
            projection = 'EPSG:4326'
        try:
            projection_text = process['projection_text']
        except Exception, e:
            projection_text = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'
        try:
            toolDir = cfg['directory']['GDAL']
        except Exception, e:
            print "No GDAL directory set. Using {0}".format(toolDir)

        modisUtils.tranformToWGS84(inWks, outWks, toolDir, filenames, projection, projection_text)
    elif process['type'] == 'crop':
        print "Crop raster data"
        # try:
        #     prefix = process['prefix']
        # except Exception, e:
        #     prefix = "test"
        #
        # try:
        #     extension = process['extension']
        # except Exception, e:
        #     extension = cfg['MODIS']['filenames']['extension']
        #
        # try:
        #     output = process['output_prefix']
        # except Exception, e:
        #     output = "test_output"
        #
        # try:
        #     output_ext = process['output_extension']
        # except Exception, e:
        #     output_ext = cfg['MODIS']['filenames']['extension']

        try:
            toolDir = cfg['directory']['GDAL']
        except Exception, e:
            print "No GDAL directory set. Using {0}".format(toolDir)

        if 'file_pattern' in process:
            pattern = process['file_pattern']
        else:
            pattern = None #r'^(?P<prefix>MOD\d{2}.\d.)(?P<datestamp>\d{4}[.]\d{2}[.]\d{2})(?P<ext>.*)'
        if 'output_pattern' in process:
            out_pattern = process['output_pattern']
        else:
            out_pattern = None #r'{prefix}{mod_prefix}{datestamp}.{suffix}'
        if pattern == None or out_pattern == None:
            patterns = None
        else:
            patterns = (pattern, out_pattern)

        inWks = process['input_dir']
        outWks = process['output_dir']
        boundFile = process['boundary_file']
#         filenames = (prefix, extension)
#         out_filenames = (output, output_ext)
# #        rasterUtils.clipRastersInDirToShape(inWks, outWks, boundFile, filenames, out_filenames, toolDir, )
        rasterUtils.cropFiles(inWks, outWks, boundFile, toolDir, patterns)
    return 0

def processTRMM(process, cfg):
    if process['type'] == 'dslr':
        inWks = process['input_dir']
        outWks = process['output_dir']
        tmpWks = process['temp_dir']

        daysSinceLast(inWks, outWks, tmpWks)
    elif process['type'] == 'download':
        outWks = process['output_dir']
        if 'start_date' in process:
            startDate = process['start_date']
        else:
            startDate = None
        if 'end_date' in process:
            endDate = process['end_date']
        else:
            endDate = None
        trmmUtils.getDailyTRMM(outWks,[startDate, endDate])
    elif process['type'] == 'convert':
        outWks = process['output_dir']
        fname = process['filename']
        trmmUtils.trmmNetCDFToTiff(fname, outWks)
    return 0

def main (config):

    global options, args

    if config:
        # parse config file
        with open(config, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
    if arcPyUtils.useSpatialAnalyst() == -1:
        os._exit(1)
#     if arcpy.GetParameterAsText(0) != '':
#         inWks = arcpy.GetParameterAsText(0)
#     else:
# #        inWks = r's:/WFP/CHIRPS/Pentad/'
# #        inWks = r's:/WFP/CHIRPS/Seasonal/'
#         inWks = r's:/WFP/MODIS/NDVI/'
#     if arcpy.GetParameterAsText(1) != '':
#         outWks = arcpy.GetParameterAsText(1)
#     else:
#         outWks = r's:/WFP/MODIS/NDVI/LTAvg/'
#        outWks = r's:/WFP/CHIRPS/Seasonal/LTAvg/'
#        outWks = r's:/WFP/CHIRPS/Pentad/LTAvg/'

#    testDekadAverage(inWks, outWks)
#    testPentadAverage(inWks, outWks)
#    testDaily(inWks, outWks)
#    testSeasonal(inWks, outWks)

    processList = cfg['run']
    print processList
    for i,p in enumerate(processList):
        try:
            if p['process'] == 'EXTRACT':
                processExtract(p, cfg)
        except Exception, e:
            configFileError("running process EXTRACT", e)
        try:
            if p['process'] == 'NDVI':
                print "Processing NDVI data"
                processNDVI(p, cfg)
        except Exception, e:
            configFileError("running process NDVI", e)
        try:
            if p['process'] == 'EVI':
                print "Processing EVI data"
                processEVI(p, cfg)
        except Exception, e:
            configFileError("running process EVI", e)
        try:
            if p['process'] == 'CHIRPS':
                print "Processing CHIRPS data"
                processCHIRPS(p, cfg)
        except Exception, e:
            configFileError("running process CHIRPS", e)
        try:
            if p['process'] == 'TEMPERATURE':
                print "Processing TEMPERATURE data"
                processTEMP(p, cfg)
        except Exception, e:
            configFileError("running process TEMPERATURE", e)

        try:
            if p['process'] == 'MODIS':
                print "Processing MODIS data"
#                inWks = cfg['MODIS']['directory']['working']
#                outWks = cfg['MODIS']['directory']['output_mosaic']
                processMODIS(p, cfg)
        except Exception, e:
            configFileError("running process MODIS", e)
        try:
            if p['process'] == 'Analysis':
                print "Performing data analysis"
                processAnalysis(p, cfg)
        except Exception, e:
            configFileError("performing data analysis", e)
        try:
            if p['process'] == 'Raster':
                print "Performing raster analysis"
                processRaster(p, cfg)
        except Exception, e:
            configFileError("performing raster analysis", e)
        try:
            if p['process'] == 'TRMM':
                print "Performing TRMM analysis"
                processTRMM(p, cfg)
        except Exception, e:
            configFileError("performing TRMM analysis", e)



if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        parser.add_option ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option ('-c', '--config', dest='config_file', action='store', help='config filename')
        (options, args) = parser.parse_args()
        #if len(args) < 1:
        #    parser.error ('missing argument')
        if options.verbose: print time.asctime()
        config_f = ""
        if options.config_file:
            config_f = options.config_file
            print 'config file=', config_f
        main(config_f)
        if options.verbose: print time.asctime()
        if options.verbose: print 'TOTAL TIME IN MINUTES:',
        if options.verbose: print (time.time() - start_time) / 60.0
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)
