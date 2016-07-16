#!/usr/bin/env python
"""
SYNOPSIS

    configProcessor [-h,--help] [-v,--verbose] [--version]

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
import yaml

from remotesensing import modisUtils, chirpsUtils, rasterUtils, precipitationAnalysis, vegetationAnalysis

logger = logging.getLogger('configProcessor')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def __configFileError(msg, e):
    print "Error in config file {0} : {1}".format(msg, str(e))
    return 0

def __processCHIRPS(process, cfg):
    try:
        outWks = process['output_dir']
    except Exception, e:
        __configFileError("No ouput directory 'output_dir' specified.", e)

    if process['type'] == 'download':
        dates = ""
        if 'dates' in process:
            dates = process['dates']
        if process['interval'] == 'monthly':
            logger.debug("Downloading CHIRPS monthly data")
            chirpsUtils.downloadMonthlyDataFromFTP(outWks, dates)
        elif process['interval'] == 'seasonal':
            logger.debug( "Downloading CHIRPS seasonal data")
            chirpsUtils.downloadSeasonalDataFromFTP(outWks, dates)
        elif process['interval'] == 'pentad':
            logger.debug( "Downloading CHIRPS pentad data")

        elif process['interval'] == 'dekad':
            logger.debug( "Downloading CHIRPS dekad data")
            chirpsUtils.downloadDekadDataFromFTP(outWks, dates)
        elif process['interval'] == 'daily':
            logger.debug( "Downloading CHIRPS daily data")
            chirpsUtils.downloadDailyDataFromFTP(outWks, dates)
    return 0

def __processMODIS(process, cfg):
    if process['type'] == 'download':
        logger.debug("Downloading MODIS data")
        try:
            outWks = process['output_dir']
        except Exception, e:
            __configFileError("No output directory specified. An 'output_dir' is required.", e)
            raise
        # default product is MOD13A3
        product = 'MOD13A3.005'
        if 'product' in process:
            product = process['product']
        # default to no tiles
        tiles = ""
        if 'tiles' in process:
            tiles = process['tiles']
        dates = ""
        if 'dates' in process:
            dates = process['dates']
        mosaic_dir = ""
        if 'mosaic_dir' in process:
            mosaic_dir = process['mosaic_dir']
        if 'MRT_dir' in process:
            toolDir = process['MRT_dir']
        elif 'directory' in cfg:
            if 'MRT' in cfg['directory']:
                toolDir = cfg['directory']['MRT']

        modisUtils.getMODISDataFromURL(outWks, product, tiles, dates, mosaic_dir, toolDir, logger)

    elif process['type'] == 'extract':
        logger.debug("Extract layer from MODIS data")
        try:
            inWks = process['input_dir']
        except Exception, e:
            __configFileError("No input directory 'input_dir' set.", e)
            raise
        try:
            outWks = process['output_dir']
        except Exception, e:
            __configFileError("No output directory 'output_dir' set.", e)
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
        if 'GDAL_dir' in process:
            toolDir = process['GDAL_dir']
        elif 'directory' in cfg:
            try:
                toolDir = cfg['directory']['GDAL']
            except Exception, e:
                __configFileError("GDAL directory", e)
                raise
        if process['layer'] == 'NDVI':
            modisUtils.extractNDVI(inWks, outWks, toolDir, patterns,logger=logger)
        elif process['layer'] == 'EVI':
            modisUtils.extractEVI(inWks, outWks, toolDir, patterns, logger=logger)
        elif process['layer'] == 'LST_Day':
            modisUtils.extractLSTDay(inWks, outWks, toolDir, patterns, logger=logger)
        elif process['layer'] == 'LST_Night':
            modisUtils.extractLSTNight(inWks, outWks, toolDir, patterns, logger=logger)

    elif process['type'] == 'calc_average':
        if 'layer' in process:
            if process['layer'] == 'day_night_temp':
                logger.debug("Calculate Average temperature from Day & Night for files matching pattern")
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
                open_src = False
                if 'open_source' in process:
                    open_src = True

                modisUtils.matchDayNightFiles(day_dir, night_dir, output_dir, patterns, open_src)
    return 0

def __processAnalysis(process, cfg):
    if process['type'] == 'rainfall_anomaly':
        logger.debug("Compute monthly rainfall anomaly")
        try:
            cur_file = process['current_file']
        except Exception, e:
            __configFileError("No current file 'current_file' specified.", e)
            raise
        try:
            lta_file = process['longterm_avg_file']
        except Exception, e:
            __configFileError("No long term average file 'longterm_avg_file' specified.", e)
            raise
        try:
            out_file = process['output_file']
        except Exception, e:
            __configFileError("No output file 'output_file' specified.", e)
            raise
        if 'open_source' in process:
            precipitationAnalysis.calcRainfallAnomaly_os(cur_file, lta_file, out_file)
        else:
            precipitationAnalysis.calcRainfallAnomaly(cur_file, lta_file, out_file)

    elif process['type'] == 'VCI':
        logger.debug("Compute Vegetation Condition Index")
        try:
            cur_file = process['current_file']
        except Exception, e:
            __configFileError("No current file 'current_file' specified.", e)
            raise
        try:
            evi_max_file = process['EVI_max_file']
        except Exception, e:
            __configFileError("No EVI maximum file 'EVI_max_file' specified.", e)
            raise
        try:
            evi_min_file = process['EVI_min_file']
        except Exception, e:
            __configFileError("No EVI minimum file 'EVI_min_file' specified.", e)
            raise
        try:
            out_file = process['output_file']
        except Exception, e:
            __configFileError("No output file 'output_file' specified.", e)
            raise

        if 'open_source' in process:
            vegetationAnalysis.calcVCI_os(cur_file, evi_max_file, evi_min_file, out_file)
        else:
            vegetationAnalysis.calcVCI(cur_file, evi_max_file, evi_min_file, out_file)

    elif process['type'] == 'TCI':
        logger.debug("Compute Temperature Condition Index")
        try:
            cur_file = process['current_file']
        except Exception, e:
            __configFileError("No current file 'current_file' specified.", e)
            raise
        try:
            lst_max_file = process['LST_max_file']
        except Exception, e:
            __configFileError("No LST maximum file 'LST_max_file' specified.", e)
            raise
        try:
            lst_min_file = process['LST_min_file']
        except Exception, e:
            __configFileError("No LST minimum file 'LST_min_file' specified.", e)
            raise
        try:
            out_file = process['output_file']
        except Exception, e:
            __configFileError("No output file 'output_file' specified.", e)
            raise

        if 'open_source' in process:
            vegetationAnalysis.calcTCI_os(cur_file, lst_max_file, lst_min_file, out_file)
        else:
            vegetationAnalysis.calcTCI(cur_file, lst_max_file, lst_min_file, out_file)

    elif process['type'] == 'VHI':
        logger.debug("Compute Vegetation Health Index")
        try:
            vci_file = process['VCI_file']
        except Exception, e:
            __configFileError("No VCI file 'VCI_file' specified.", e)
            raise
        try:
            tci_file = process['TCI_file']
        except Exception, e:
            __configFileError("No TCI file 'TCI_file' specified.", e)
            raise
        try:
            out_file = process['output_file']
        except Exception, e:
            __configFileError("No output file 'output_file' specified.", e)
            raise

        if 'open_source' in process:
            vegetationAnalysis.calcVHI_os(vci_file, tci_file, out_file)
        else:
            vegetationAnalysis.calcVHI(vci_file, tci_file, out_file)

    return 0

def __processRaster(process, cfg):
    if process['type'] == 'crop':
        logger.debug("Crop raster data to boundary")
        try:
            toolDir = cfg['directory']['GDAL']
        except Exception, e:
            __configFileError("No GDAL directory set. Using {0}".format(toolDir), e)
            raise

        if 'file_pattern' in process:
            pattern = process['file_pattern']
        else:
            pattern = None
        if 'output_pattern' in process:
            out_pattern = process['output_pattern']
        else:
            out_pattern = None
        if pattern == None or out_pattern == None:
            patterns = None
        else:
            patterns = (pattern, out_pattern)

        try:
            inWks = process['input_dir']
        except Exception, e:
            __configFileError("No input directory 'input_dir' set.", e)
            raise
        try:
            outWks = process['output_dir']
        except Exception, e:
            __configFileError("No output directory 'output_dir' set.", e)
            raise
        try:
            boundFile = process['boundary_file']
        except Exception, e:
            __configFileError("No boundary file specified." ,e)
            raise
        rasterUtils.cropFiles(inWks, outWks, boundFile, toolDir, patterns)
    return 0


def processConfig (config):

    global options, args

    try:
        if config:
            # parse config file
            with open(config, 'r') as ymlfile:
                cfg = yaml.load(ymlfile)
        else:
            logger.error("A config file is required. Please specify a config file on the command line.")
            return -1
    except Exception, e:
        logger.error("Cannot load config file.")
        raise

    processList = cfg['run']
    logger.debug(processList)

    for i,p in enumerate(processList):
        try:
            if p['process'] == 'CHIRPS':
                print "Processing CHIRPS data"
                __processCHIRPS(p, cfg)
        except Exception, e:
            __configFileError("running process CHIRPS", e)
            raise
        try:
            if p['process'] == 'MODIS':
                print "Processing MODIS data"
                __processMODIS(p, cfg)
        except Exception, e:
            __configFileError("running process MODIS", e)
            raise
        try:
            if p['process'] == 'Analysis':
                print "Performing data analysis"
                __processAnalysis(p, cfg)
        except Exception, e:
            __configFileError("performing data analysis", e)
            raise
        try:
            if p['process'] == 'Raster':
                print "Performing raster analysis"
                __processRaster(p, cfg)
        except Exception, e:
            __configFileError("performing raster analysis", e)
            raise
