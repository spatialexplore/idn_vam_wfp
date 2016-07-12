__author__ = 'rochelle'

import arcpy
import gdal, osr


def calcTCI(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    # calculate Temperature Condition Index
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)
    cur_Raster = arcpy.Raster(cur_filename)
    lta_max_Raster = arcpy.Raster(lta_max_filename)
    lta_min_Raster = arcpy.Raster(lta_min_filename)
    denominator = arcpy.sa.Minus(lta_max_Raster, lta_min_Raster)
    numerator = arcpy.sa.Minus(lta_max_Raster, cur_Raster)
    dst_f = arcpy.sa.Divide(numerator, denominator)
    dst = arcpy.sa.Times(dst_f, 100)
    dst.save(dst_filename)
    return 0

def _getNoDataValue(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.GetNoDataValue()


def _raster2array(raster_file):
    raster = gdal.Open(raster_file)
    band = raster.GetRasterBand(1)
    return band.ReadAsArray()

def _array2raster(rasterfn,newRasterfn,array):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = raster.RasterXSize
    rows = raster.RasterYSize

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

def calcTCI_os(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    #  calculate Temperature Condition Index using open-source functionality
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)
    cur_RasterArray = _raster2array(cur_filename)
    cur_nodata = _getNoDataValue(cur_filename)
    lta_max_RasterArray = _raster2array(lta_max_filename)
    lta_max_nodata = _getNoDataValue(lta_max_filename)
    lta_min_RasterArray = _raster2array(lta_min_filename)
    lta_min_nodata = _getNoDataValue(lta_min_filename)

    denominator = lta_max_RasterArray[lta_max_RasterArray != lta_max_nodata] - lta_min_RasterArray[lta_min_RasterArray != lta_min_nodata]
    numerator = lta_max_RasterArray - cur_RasterArray
    dst_f = numerator / denominator * 100.0
    _array2raster(cur_filename, dst_filename, dst_f)
    return 0


def calcVCI(cur_filename, evi_max_filename, evi_min_filename, dst_filename):
     # calculate Vegetation Condition Index
    # VCI = 100 x (EVI - EVI_min)/(EVI_max - EVI_min)
    cur_Raster = arcpy.Raster(cur_filename)
    evi_max_Raster = arcpy.Raster(evi_max_filename)
    evi_min_Raster = arcpy.Raster(evi_min_filename)
    cur_scaled = arcpy.sa.Times(cur_Raster, 0.0001)
    evi_max_scaled = arcpy.sa.Times(evi_max_Raster, 0.0001)
    evi_min_scaled = arcpy.sa.Times(evi_min_Raster, 0.0001)
    denominator = arcpy.sa.Minus(evi_max_scaled, evi_min_scaled)
    numerator = arcpy.sa.Minus(cur_scaled, evi_min_scaled)
    dst_f = arcpy.sa.Divide(numerator, denominator)
    dst = arcpy.sa.Times(dst_f, 100)
    dst.save(dst_filename)
    return 0

def calcVHI(vci_filename, tci_filename, dst_filename):
     # calculate Vegetation Health Index
    # VHI = 0.5 x (VCI + TCI)
    arcpy.env.cellSize = "MINOF"
    vci_Raster = arcpy.Raster(vci_filename)
    tci_Raster = arcpy.Raster(tci_filename)
    dst_f = arcpy.sa.Plus(vci_Raster, tci_Raster)
    dst = arcpy.sa.Times(dst_f, 0.5)
    dst.save(dst_filename)
    return 0