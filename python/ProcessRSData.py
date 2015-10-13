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

import sys, os, traceback, optparse
import time
import arcpy
import yaml
import arcPyUtils
from datetime import date
from directoryUtils import unzipFiles
from ndviUtils import calcNDVIAverages
from modisUtils import mosaicMODIS, cropMODIS, extractNDVI, extractEVI
import chirpsUtils
import rasterUtils

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
    filenames = (prefix, ext)
    output_filenames = (output_prefix, output_ext)
    rasterUtils.clipRastersInDirToShape(inw, outw, shapefile, filenames, output_filenames, gdal_path)
    return 0

def processCHIRPS(process, cfg):
    prefix = cfg['CHIRPS']['filenames']['input_prefix']
    ext = cfg['CHIRPS']['filenames']['input_extension']
    if 'input_extension' in process:
        ext = process['input_extension']
    if 'input_prefix' in process:
        prefix = process['input_prefix']
    filenames = (prefix, ext)
    inWks = process['input_dir']
    outWks = process['output_dir']
    temp_path = cfg['directory']['temp']
    arcpy.env.workspace = inWks
    funcs = process['functions']
    if process['type'] == 'monthly':
        print "Processing CHIRPS monthly data"
    elif process['type'] == 'seasonal':
        print "Processing CHIRPS seasonal data"
        chirpsUtils.calcSeasonalAverages(inWks, outWks, funcs, filenames)
    elif process['type'] == 'pentad':
        print "Processing CHIRPS pentad data"
        chirpsUtils.calcPentadAverages(inWks, outWks, funcs, filenames)
    elif process['type'] == 'dekad':
        print "Processing CHIRPS dekad data"
        chirpsUtils.calcDekadAverages(inWks, outWks, funcs, filenames)
    elif process['type'] == 'daily':
        print "Processing CHIRPS daily data"
        threshold = cfg['CHIRPS']['thresholds']['precipitation_threshold']
        ndays = cfg['CHIRPS']['thresholds']['max_days_to_process']
        chirpsUtils.calcDailyStatistics(inWks, outWks, temp_path, funcs, date(2015,06,30), filenames, filenames, threshold, ndays)
    return 0

def processNDVI(process, cfg):
    print 'Calculate NDVI Long Term Averages'
    inWks = process['input_dir']
    outWks = process['output_dir']
    arcpy.env.workspace = inWks
    funcs = process['functions']
    filenames = (cfg['NDVI']['filenames']['prefix'], cfg['NDVI']['filenames']['extension'])
    if not funcs:
        funcs = ['AVG']
    calcNDVIAverages(inWks, outWks, funcs, filenames)
    return 0

def processEVI(process, cfg):
    print 'Calculate EVI Long Term Averages'
    inWks = process['input_dir']
    outWks = process['output_dir']
    arcpy.env.workspace = inWks
    funcs = process['functions']
    filenames = (cfg['EVI']['filenames']['prefix'], cfg['EVI']['filenames']['extension'])
    if not funcs:
        funcs = ['AVG']
    calcNDVIAverages(inWks, outWks, funcs, filenames)
    return 0

def processMODIS(inw, outw, process, cfg):
    try:
        toolDir = cfg['MODIS']['directory']['tools']
    except Exception, e:
        configFileError("MODIS Tools directory", e)
    if process['type'] == 'mosaic':
        print "Mosaic MODIS data"
        inWks = process['input_dir']
        outWks = process['output_dir']
        try:
            workDir = cfg['MODIS']['directory']['working']
        except Exception, e:
            workDir = outWks
        filenames = (cfg['MODIS']['filenames']['prefix'], cfg['MODIS']['filenames']['extension'])
        mosaicMODIS(inWks, outWks, toolDir, workDir, filenames)
    elif process['type'] == 'crop':
        print "Crop MODIS data"
        try:
            prefix = process['prefix']
        except Exception, e:
            prefix = cfg['MODIS']['filenames']['prefix']

        try:
            extension = process['extension']
        except Exception, e:
            extension = cfg['MODIS']['filenames']['extension']

        try:
            toolDir = cfg['directory']['GDAL']
        except Exception, e:
            print "No GDAL directory set. Using {0}".format(toolDir)
        inWks = process['input_dir']
        outWks = process['output_dir']
        boundFile = process['boundary_file']
        filenames = (prefix, extension)
        out_filenames = (cfg['MODIS']['filenames']['output'], cfg['MODIS']['filenames']['output_ext'])
        cropMODIS(inWks, outWks, boundFile, toolDir, filenames, out_filenames)
    elif process['type'] == 'extract':
        print "Extract layer from MODIS data"
        inWks = process['input_dir']
        outWks = process['output_dir']
        filenames = (cfg['MODIS']['filenames']['prefix'], cfg['MODIS']['filenames']['extension'])
        try:
            out_prefix = process['output']
        except Exception, e:
            out_prefix = cfg['MODIS']['filenames']['output']
        try:
            out_ext = process['output_ext']
        except Exception, e:
            out_ext = cfg['MODIS']['filenames']['output_ext']
        out_filenames = (out_prefix, out_ext)
        if process['layer'] == 'NDVI':
            extractNDVI(inWks, outWks, toolDir, filenames, out_filenames)
        elif process['layer'] == 'EVI':
            extractEVI(inWks, outWks, toolDir, filenames, out_filenames)

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
            if p['process'] == 'MODIS':
                print "Processing MODIS data"
                inWks = cfg['MODIS']['directory']['working']
                outWks = cfg['MODIS']['directory']['output_mosaic']
                processMODIS(inWks, outWks, p, cfg)
        except Exception, e:
            configFileError("running process MODIS", e)


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
