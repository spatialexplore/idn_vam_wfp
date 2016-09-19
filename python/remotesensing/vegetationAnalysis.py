__author__ = 'rochelle'

#import arcpy
import gdal, osr
import numpy as np
import rasterio
from rasterio.warp import reproject, RESAMPLING
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

def calcTCI_os(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    # arcpy-free version
    # calculate Temperature Condition Index
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)

    with rasterio.open(cur_filename) as cur_r:
        cur_band = cur_r.read(1, masked=True)
        profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_max_filename) as lta_max_r:
            lta_max_a = lta_max_r.read(1, masked=True)
            with rasterio.open(lta_min_filename) as lta_min_r:
                lta_min_a = lta_min_r.read(1, masked=True)
                dst_f = np.zeros(cur_band.shape)
                newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(cur_band), np.ma.getmask(lta_max_a)),
                                            dst_f)
                numerator=(lta_max_a - cur_band)
                denominator = (lta_max_a - lta_min_a)
                newd_f += (np.divide(numerator, denominator) * 100.0)

                res = newd_f.filled(fill_value=cur_r.nodata)
                res2 = np.ma.masked_where(res == cur_r.nodata, res)

                profile.update(dtype=rasterio.float64)
                with rasterio.open(dst_filename, 'w', **profile) as dst:
                    dst.write(res2.astype(rasterio.float64), 1)
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

def calcVCI_os(cur_filename, evi_max_filename, evi_min_filename, dst_filename):
    # arcpy-free version
    # calculate Vegetation Condition Index
    # VCI = 100 x (EVI - EVI_min)/(EVI_max - EVI_min)
    with rasterio.open(cur_filename) as cur_r:
        cur_band = cur_r.read(1, masked=True)
        profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(evi_max_filename) as evi_max_r:
#            evi_max_a = evi_max_r.read(1, masked=True)
            evi_max_w = evi_max_r.read(1, window=((0, cur_band.shape[0]), (0, cur_band.shape[1])), masked=True)
            with rasterio.open(evi_min_filename) as evi_min_r:
#                evi_min_a = evi_min_r.read(1, masked=True)
                evi_min_w = evi_min_r.read(1, window=((0, cur_band.shape[0]), (0, cur_band.shape[1])), masked=True)
                dst_f = np.zeros(cur_band.shape)
                newd_f = np.ma.masked_where(np.ma.getmask(cur_band),
                                            dst_f)
#                evi_min_ma = np.ma.masked_where(np.ma.getmask(cur_band), evi_min_w)
                # newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(cur_band), np.ma.getmask(evi_max_a)),
                #                             dst_f)
                numerator = (cur_band - evi_min_w)
                denominator = (evi_max_w - evi_min_w)
                with np.errstate(divide='ignore'):
                    newd_f += (np.divide(numerator, denominator) * 100.0)
                res = newd_f.filled(fill_value=cur_r.nodata)
                res2 = np.ma.masked_where(res == cur_r.nodata, res)

                profile.update(dtype=rasterio.float64)
                with rasterio.open(dst_filename, 'w', **profile) as dst:
                    dst.write(res2.astype(rasterio.float64), 1)
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

def calcVHI_os(vci_filename, tci_filename, dst_filename):
    # arcpy-free version
    # calculate Vegetation Health Index
    # VHI = 0.5 x (VCI + TCI)
    with rasterio.open(vci_filename) as vci_r:
        vci_a = vci_r.read(1, masked=True)
        print vci_r.nodatavals
        with rasterio.open(tci_filename) as tci_r:
            tci_a = tci_r.read(1, masked=True)
            profile = tci_r.profile.copy()
            # check that resolution of vci matches resolution of tci
            print vci_a.shape
            print tci_a.shape
            if vci_a.shape[0] > tci_a.shape[0] or vci_a.shape[1] > tci_a.shape[1]:
                # resample vci
                newarr = np.empty(shape=(tci_a.shape[0], tci_a.shape[1]))
                # adjust the new affine transform to the smaller cell size
                aff = vci_r.transform
                newaff = rasterio.Affine(aff[0] / (float(tci_a.shape[0]) / float(vci_a.shape[0])), aff[1], aff[2],
                                aff[3], aff[4] / (float(tci_a.shape[1]) / float(vci_a.shape[1])), aff[5])

                try:
                    reproject(
                        vci_a, newarr,
                        src_transform=aff,
                        dst_transform=newaff,
                        src_crs=vci_r.crs,
                        dst_crs=vci_r.crs,
                        resampling=RESAMPLING.bilinear)
                except Exception, e:
                    print "Error in reproject "
                vci_a = np.ma.masked_where(np.ma.getmask(tci_a), newarr)
#                rasterUtils.resampleRaster(vci_filename, tmp_filename, gdal_path, tci_a.shape[0], tci_a.shape[1])
            elif tci_a.shape[0] > vci_a.shape[0] or tci_a.shape[1] > tci_a.shape[1]:
                # resample tci
                newarr = np.empty(shape=(vci_a.shape[0], vci_a.shape[1]))
                # adjust the new affine transform to the smaller cell size
                aff = tci_a.transform
                newaff = rasterio.Affine(aff.a / (vci_a.shape[0] / tci_a.shape[0]), aff.b, aff.c,
                                         aff.d, aff.e / (vci_a.shape[1] / tci_a.shape[1]), aff.f)
                try:
                    reproject(
                        tci_a, newarr,
                        src_transform=aff,
                        dst_transform=newaff,
                        src_crs=tci_a.crs,
                        dst_crs=tci_a.crs,
                        resample=RESAMPLING.bilinear)
                except Exception, e:
                    print "Error in reproject "
                tci_a = np.ma.masked_where(np.ma.getmask(vci_a), newarr)

            dst_f = np.zeros(vci_a.shape)
            newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(vci_a), np.ma.getmask(tci_a)),
                                        dst_f)
            newd_f += ((vci_a + tci_a) * 0.5)
            res = newd_f.filled(fill_value=vci_r.nodata)
            res2 = np.ma.masked_where(res == vci_r.nodata, res)
            profile.update(dtype=rasterio.float64)
            with rasterio.open(dst_filename, 'w', **profile) as dst:
                dst.write(res2.astype(rasterio.float64), 1)
    return 0