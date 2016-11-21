__author__ = 'rochelle'

#import arcpy
import gdal, osr
import numpy as np
import rasterio
from rasterio.warp import reproject, RESAMPLING
import os
import urllib2
import rasterUtils

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

def calcTCI_os(cur_filename, lta_max_filename, lta_min_filename, dst_filename, gdal_path):
    # arcpy-free version
    # calculate Temperature Condition Index
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)

    with rasterio.open(cur_filename) as cur_r:
#        cur_band = cur_r.read(1, masked=True)
        cur_band = cur_r.read(1, masked=False)
        profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_max_filename) as lta_max_r:
            lta_max_a = lta_max_r.read(1, masked=False)
            with rasterio.open(lta_min_filename) as lta_min_r:
                lta_min_a = lta_min_r.read(1, masked=False)
                numerator=(lta_max_a - cur_band)
                denominator = (lta_max_a - lta_min_a)
                res2 = np.where(np.logical_or(cur_band == cur_r.nodatavals[0],
                                             np.logical_or(lta_max_a == lta_max_r.nodatavals[0],
                                             lta_min_a == lta_min_r.nodatavals[0])),
                               cur_r.nodatavals[0], 100*(numerator/denominator))

                profile.update(dtype=rasterio.float32)
                dst_f = "{0}.tmp{1}".format(os.path.splitext(dst_filename)[0], os.path.splitext(dst_filename)[1])
                with rasterio.open(dst_f, 'w', **profile) as dst:
                    dst.write(res2.astype(rasterio.float32), 1)
                rasterUtils.setRasterNoDataValues(dst_f, dst_filename, gdal_path, -9999, None, 'Float32', True)

                    # del newd_f
                # del res
                # del res2
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

def calcVCI_os(cur_filename, evi_max_filename, evi_min_filename, dst_filename, gdal_path=None):
    # arcpy-free version
    # calculate Vegetation Condition Index
    # VCI = 100 x (EVI - EVI_min)/(EVI_max - EVI_min)

    with rasterio.open(cur_filename) as cur_r:
        cur_band = cur_r.read(1, masked=False)
        profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(evi_max_filename) as evi_max_r:
            evi_max_a = evi_max_r.read(1, masked=False)
            with rasterio.open(evi_min_filename) as evi_min_r:
                evi_min_a = evi_min_r.read(1, masked=False)
                numerator = (cur_band - evi_min_a)
                denominator = (evi_max_a - evi_min_a)
                denominator = np.where(denominator == 0, cur_r.nodatavals, denominator)
                res2 = np.where(np.logical_or(cur_band == cur_r.nodatavals[0],
                                              np.logical_or(evi_max_a == evi_max_r.nodatavals[0],
                                                            evi_min_a == evi_min_r.nodatavals[0])),
                                cur_r.nodatavals[0], 100.0 * (numerator.astype(np.float32) / denominator.astype(np.float32)))
                profile.update(dtype=rasterio.float32)
                dst_f = "{0}.tmp{1}".format(os.path.splitext(dst_filename)[0], os.path.splitext(dst_filename)[1])
                with rasterio.open(dst_f, 'w', **profile) as dst:
                    dst.write(res2.astype(rasterio.float32), 1)
                rasterUtils.setRasterNoDataValues(dst_f, dst_filename, gdal_path, -9999, None, 'Float32', True)

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

def calcVHI_os(vci_filename, tci_filename, dst_filename, shpfile, gdal_path=None):
    # arcpy-free version
    # calculate Vegetation Health Index
    # VHI = 0.5 x (VCI + TCI)
#    calcVHI_gdal_calculations(vci_filename, tci_filename, dst_filename, shpfile)

    with rasterio.open(vci_filename) as vci_r:
        vci_a = vci_r.read(1, masked=False)
        # print vci_r.nodatavals
        with rasterio.open(tci_filename) as tci_r:
            tci_a = tci_r.read(1, masked=False)
            profile = tci_r.profile.copy()
            vci_a2 = None
            tci_a2 = None
            # print "initial"
            # print np.max(vci_a)
            # print np.min(vci_a)
            # print np.mean(vci_a)
            if tci_a.shape > vci_a.shape:
                # only use smaller area
                tci_a2 = np.resize(tci_a, vci_a.shape)
                vci_a2 = vci_a
            elif vci_a.shape > tci_a.shape:
                vci_a2 = np.resize(vci_a, tci_a.shape)
                tci_a2 = tci_a
            else:
                vci_a2 = vci_a
                tci_a2 = tci_a

            tci_a2[np.isnan(tci_a2)] = tci_r.nodatavals
            vci_a2[np.isnan(vci_a2)] = vci_r.nodatavals


            vhi = np.zeros(tci_a.shape, np.float32)
            tmp = 0.5*(tci_a2 + vci_a2)
#            vhi = np.where(tci_a == tci_r.nodatavals[0], -9999, 0.5) # * (tci_a2 + vci_a2))
            vhi = np.where(np.logical_and(vci_a2 == vci_r.nodatavals[0],
                                          tci_a2 == tci_r.nodatavals[0]),
                           vci_r.nodatavals,
                           np.where(vci_a2 == vci_r.nodatavals[0], tci_a2,
                                    np.where(tci_a2 == tci_r.nodatavals[0], vci_a2,
                                             np.where(np.logical_and(vci_a2 == 0.0, tci_a2 == 0.0), 0.0,
                                                      np.where(vci_a2 == 0.0, tci_a2,
                                                               np.where(tci_a2 == 0.0, vci_a2,
                                                                        (tci_a2 + vci_a2)*0.5)))
                                             )))
            profile.update(dtype=rasterio.float32)
            dst_f = "{0}.tmp{1}".format(os.path.splitext(dst_filename)[0], os.path.splitext(dst_filename)[1])
            with rasterio.open(dst_f, 'w', **profile) as dst:
                dst.write(vhi.astype(rasterio.float32), 1)
            rasterUtils.setRasterNoDataValues(dst_f, dst_filename, gdal_path, -9999, None, 'Float32', True)

    return 0