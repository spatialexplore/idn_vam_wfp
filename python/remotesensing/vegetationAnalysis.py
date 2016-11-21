__author__ = 'rochelle'

#import arcpy
import gdal, osr
import numpy as np
import rasterio
from rasterio.warp import reproject, RESAMPLING
import os
import urllib2
import rasterUtils
import gdal_calculations

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

def calcTCI_gdal_calculations(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    gdal_calculations.Env.resampling = 'BILINEAR'
    gdal_calculations.Env.reproject = True
    gdal_calculations.Env.overwrite = True
    gdal_calculations.Env.cellsize = 'MINOF'
    gdal_calculations.Env.srs = 4326
    gdal_calculations.Env.nodata = True
    gdal.UseExceptions()
    cur_ds = gdal_calculations.Dataset(cur_filename)
    cur_ds.SetNoDataValue(0)
    ltamax_ds = gdal_calculations.Dataset(lta_max_filename)
    ltamin_ds = gdal_calculations.Dataset(lta_min_filename)
    tci1 = gdal_calculations.Float64(ltamax_ds[0]) - gdal_calculations.Float64(cur_ds[0])
    tci1.SetNoDataValue(-9999)
    tci1.save("/home/parallels/Vampire/data/tci1.tif")
    tci2 = gdal_calculations.Float64(ltamax_ds[0]) - gdal_calculations.Float64(ltamin_ds[0])
    tci2.SetNoDataValue(-9999)
    tci2.save("/home/parallels/Vampire/data/tci2.tif")
    tci = gdal_calculations.Float64(tci1[0]) / gdal_calculations.Float64(tci2[0]) * 100.0
    tci.SetNoDataValue(-9999)
    tci.save(dst_filename)
    return 0

def calcTCI_os_qgis(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    import qgis.core
    import qgis.analysis
    import sys

    qgis.core.QgsApplication.setPrefixPath("/usr/bin/qgis", True)
    qgs = qgis.core.QgsApplication([], False)
    qgs.initQgis()
    sys.path.append("/usr/share/qgis/python/plugins")

    fileInfo = qgis.QtCore.QFileInfo(cur_filename)
    baseName = fileInfo.baseName()
    cur_layer = qgis.core.QgsRasterLayer(cur_filename, baseName)
    if not cur_layer.isValid():
        print "Current layer failed to load"
    fileInfo = qgis.QtCore.QFileInfo(lta_max_filename)
    baseName = fileInfo.baseName()
    lta_max_layer = qgis.core.QgsRasterLayer(lta_max_filename, baseName)
    if not lta_max_layer.isValid():
        print "Current layer failed to load"
    fileInfo = qgis.QtCore.QFileInfo(lta_min_filename)
    baseName = fileInfo.baseName()
    lta_min_layer = qgis.core.QgsRasterLayer(lta_min_filename, baseName)
    if not lta_min_layer.isValid():
        print "Current layer failed to load"

    entries_ = []
    ras = qgis.analysis.QgsRasterCalculatorEntry()
    ras.ref = 'curlyr@1'
    ras.raster = cur_layer
    ras.bandNumber = 1
    entries_.append(ras)
    ras2 = qgis.analysis.QgsRasterCalculatorEntry()
    ras2.ref = 'tmax_lyr@1'
    ras2.raster = lta_max_layer
    ras2.bandNumber = 1
    entries_.append(ras2)
    ras3 = qgis.analysis.QgsRasterCalculatorEntry()
    ras3.ref = 'tmin_lyr@1'
    ras3.raster = lta_min_layer
    ras3.bandNumber = 1
    entries_.append(ras3)
    crs = qgis.core.QgsCoordinateReferenceSystem("EPSG:4326")
    calc = qgis.analysis.QgsRasterCalculator('100 * (tmax_lyr@1 - curlyr@1) / (tmax_lyr@1 - tmin_lyr@1)',
                                             dst_filename, 'GTiff', cur_layer.extent(), crs,
                                             cur_layer.width(), cur_layer.height(), entries_)
    calc.processCalculation()
#    qgs.exitQgis()


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


            # lta_max_a = lta_max_r.read(1, masked=True)
            # with rasterio.open(lta_min_filename) as lta_min_r:
            #     lta_min_a = lta_min_r.read(1, masked=True)
            #     dst_f = np.zeros(cur_band.shape)
            #     newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(cur_band), np.ma.getmask(lta_max_a)),
            #                                 dst_f)
            #     numerator=(lta_max_a - cur_band)
            #     denominator = (lta_max_a - lta_min_a)
            #     del lta_max_a
            #     del lta_min_a
            #     newd_f += (np.divide(numerator, denominator) * 100.0)
            #     del numerator
            #     del denominator
            #     res = newd_f.filled(fill_value=cur_r.nodata)
            #     res2 = np.ma.masked_where(res == cur_r.nodata, res)
            #
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

    #             #            evi_max_a = evi_max_r.read(1, masked=True)
#             evi_max_w = evi_max_r.read(1, window=((0, cur_band.shape[0]), (0, cur_band.shape[1])), masked=True)
#             with rasterio.open(evi_min_filename) as evi_min_r:
# #                evi_min_a = evi_min_r.read(1, masked=True)
#                 evi_min_w = evi_min_r.read(1, window=((0, cur_band.shape[0]), (0, cur_band.shape[1])), masked=True)
#                 dst_f = np.zeros(cur_band.shape, np.float32)
#                 newd_f = np.ma.masked_where(np.ma.getmask(cur_band),
#                                             dst_f)
# #                evi_min_ma = np.ma.masked_where(np.ma.getmask(cur_band), evi_min_w)
#                 # newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(cur_band), np.ma.getmask(evi_max_a)),
#                 #                             dst_f)
#                 numerator = (cur_band - evi_min_w)
#                 denominator = (evi_max_w - evi_min_w)
#                 del cur_band
#                 del evi_min_w
#                 del evi_max_w
#
#                 try:
#                     with np.errstate(divide='ignore'):
#                         newd_f += (np.divide(numerator, denominator) * 100.0)
#                 except Exception, e:
#                     print "Error in VCI calculation"
#                     raise
#                 res = newd_f.filled(fill_value=cur_r.nodata)
#                 res2 = np.ma.masked_where(res == cur_r.nodata, res)
#
#                 profile.update(dtype=rasterio.float32)
#                 with rasterio.open(dst_filename, 'w', **profile) as dst:
#                     dst.write(res2.astype(rasterio.float32), 1)
#                 del newd_f, res, res2
    return 0

def calcVCI_os_qgis(cur_filename, evi_max_filename, evi_min_filename, dst_filename):
    import qgis.core
    import qgis.analysis
    import sys

    qgis.core.QgsApplication.setPrefixPath("/usr/bin/qgis", True)
    qgs = qgis.core.QgsApplication([], False)
    qgs.initQgis()
    sys.path.append("/usr/share/qgis/python/plugins")

    fileInfo = qgis.QtCore.QFileInfo(cur_filename)
    baseName = fileInfo.baseName()
    cur_layer = qgis.core.QgsRasterLayer(cur_filename, baseName)
    if not cur_layer.isValid():
        print "Current layer failed to load"
    fileInfo = qgis.QtCore.QFileInfo(evi_max_filename)
    baseName = fileInfo.baseName()
    evi_max_layer = qgis.core.QgsRasterLayer(evi_max_filename, baseName)
    if not evi_max_layer.isValid():
        print "Current layer failed to load"
    fileInfo = qgis.QtCore.QFileInfo(evi_min_filename)
    baseName = fileInfo.baseName()
    evi_min_layer = qgis.core.QgsRasterLayer(evi_min_filename, baseName)
    if not evi_min_layer.isValid():
        print "Current layer failed to load"

    entries_ = []
    ras = qgis.analysis.QgsRasterCalculatorEntry()
    ras.ref = 'curlyr@1'
    ras.raster = cur_layer
    ras.bandNumber = 1
    entries_.append(ras)
    ras2 = qgis.analysis.QgsRasterCalculatorEntry()
    ras2.ref = 'emax_lyr@1'
    ras2.raster = evi_max_layer
    ras2.bandNumber = 1
    entries_.append(ras2)
    ras3 = qgis.analysis.QgsRasterCalculatorEntry()
    ras3.ref = 'emin_lyr@1'
    ras3.raster = evi_min_layer
    ras3.bandNumber = 1
    entries_.append(ras3)
    crs = qgis.core.QgsCoordinateReferenceSystem("EPSG:4326")
    calc = qgis.analysis.QgsRasterCalculator('100 * (curlyr@1 - emin_lyr@1) / (emax_lyr@1 - emin_lyr@1)',
                                             dst_filename, 'GTiff', cur_layer.extent(), crs,
                                             cur_layer.width(), cur_layer.height(), entries_)
    calc.processCalculation()
#    qgs.exitQgis()


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

def calcVHI_gdal_calculations(vci_filename, tci_filename, dst_filename, shpfile):
    gdal_calculations.Env.resampling = 'BILINEAR'
    gdal_calculations.Env.reproject = True
    gdal_calculations.Env.overwrite = True
    gdal.UseExceptions()
    ds1 = gdal_calculations.Dataset(vci_filename)
    ds2 = gdal_calculations.Dataset(tci_filename)
    vci = ds1[0].astype(np.float32)
    tci = ds2[0].astype(np.float32)
    vhi = vci + tci
#    vhi = gdal_calculations.Float32(vhi1[0]) * 0.5
    vhi.save(dst_filename)
    return 0

def calcVHI_os_qgis(vci_filename, tci_filename, dst_filename, shpfile, gdal_path=None):
    import qgis.core
    import qgis.analysis
    import sys

    qgis.core.QgsApplication.setPrefixPath("/usr/bin/qgis", True)
    qgs = qgis.core.QgsApplication([], False)
    qgs.initQgis()
    sys.path.append("/usr/share/qgis/python/plugins")

    fileInfo = qgis.QtCore.QFileInfo(vci_filename)
    baseName = fileInfo.baseName()
    vci_layer = qgis.core.QgsRasterLayer(vci_filename, baseName)
    if not vci_layer.isValid():
        print "Current layer failed to load"

    fileInfo = qgis.QtCore.QFileInfo(tci_filename)
    baseName = fileInfo.baseName()
    tci_layer = qgis.core.QgsRasterLayer(tci_filename, baseName)
    if not tci_layer.isValid():
        print "Current layer failed to load"

    entries_ = []
    ras = qgis.analysis.QgsRasterCalculatorEntry()
    ras.ref = 'vcilyr@1'
    ras.raster = vci_layer
    ras.bandNumber = 1
    entries_.append(ras)
    ras2 = qgis.analysis.QgsRasterCalculatorEntry()
    ras2.ref = 'tcilyr@1'
    ras2.raster = tci_layer
    ras2.bandNumber = 1
    entries_.append(ras2)

    crs = qgis.core.QgsCoordinateReferenceSystem("EPSG:4326")
    calc = qgis.analysis.QgsRasterCalculator('0.5 * (vcilyr@1 + tcilyr@1)',
                                             dst_filename, 'GTiff', tci_layer.extent(), crs,
                                             tci_layer.width(), tci_layer.height(), entries_)
    calc.processCalculation()
#    qgs.exitQgis()


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
            # dst_a = np.where(np.logical_and(vci_a2 == 0, tci_a2 == 0), 0,
            #                   np.where(vci_a2 == 0, tci_a2,
            #                            np.where(tci_a2 == 0, vci_a2, vhi)))
            # print "vhi"
            # print np.max(vhi)
            # print np.min(vhi)
            # print np.mean(vhi)
            profile.update(dtype=rasterio.float32)
            dst_f = "{0}.tmp{1}".format(os.path.splitext(dst_filename)[0], os.path.splitext(dst_filename)[1])
            with rasterio.open(dst_f, 'w', **profile) as dst:
                dst.write(vhi.astype(rasterio.float32), 1)
            rasterUtils.setRasterNoDataValues(dst_f, dst_filename, gdal_path, -9999, None, 'Float32', True)


            #         vci_a = vci_r.read(1, masked=True)
#         print vci_r.nodatavals
#         with rasterio.open(tci_filename) as tci_r:
#             tci_a = tci_r.read(1, masked=True)
#             profile = tci_r.profile.copy()
#             # check that resolution of vci matches resolution of tci
#             print vci_a.shape
#             print tci_a.shape
#             if vci_a.shape[0] > tci_a.shape[0] or vci_a.shape[1] > tci_a.shape[1]:
#                 print "Error: VCI and TCI files have different sizes"
#                 tci_shape = tci_a.shape
#                 tci_a = np.resize(tci_a, vci_a.shape)
#                 tci_a[:][tci_shape[1]:vci_a.shape[1]] = tci_r.nodata
#                 tci_a[tci_shape[0]:vci_a.shape[0]][:] = tci_r.nodata
#                 # resample tci
#                 # resample_filename = "{0}_resample.tif".format(os.path.splitext(tci_filename)[0])
#                 # rasterUtils.resampleRaster(tci_filename, resample_filename, gdal_path, 597.6845533053, 597.6845533053)
#                 # newtci_filename = "{0}_new.tif".format(os.path.splitext(tci_filename)[0])
#                 # rasterUtils.clipRasterToShp(shpfile,resample_filename, newtci_filename, gdal_path)
#                 # with rasterio.open(newtci_filename) as tci_r:
#                 #     tci_a = tci_r.read(1, masked=True)
#                 #     profile = tci_r.profile.copy()
# #
# #                 newarr = np.empty(shape=(tci_a.shape[0]*5.43529411764706,
# #                                          tci_a.shape[1]*5.38569880823402))
# #                 # adjust the new affine transform to the smaller cell size
# #                 aff = tci_r.transform
# #
# # #                newaff = rasterio.Affine(aff[0] / (float(tci_a.shape[0]) / float(vci_a.shape[0])), aff[1], aff[2],
# # #                                         aff[3], aff[4] / (float(tci_a.shape[1]) / float(vci_a.shape[1])), aff[5])
# #                 newaff = rasterio.Affine(aff[0] / (5.43529411764706), aff[1], aff[2],
# #                                 aff[3], aff[4] / (5.38569880823402), aff[5])
# #
# #                 try:
# #                     reproject(
# #                         tci_a, newarr,
# #                         src_transform=aff,
# #                         dst_transform=newaff,
# #                         src_crs=tci_r.crs,
# #                         dst_crs=tci_r.crs,
# #                         resampling=RESAMPLING.bilinear)
# #                 except Exception, e:
# #                     print "Error in reproject "
# #                tci_a = np.ma.masked_where(np.ma.getmask(vci_a), newarr)
# #                rasterUtils.resampleRaster(vci_filename, tmp_filename, gdal_path, tci_a.shape[0], tci_a.shape[1])
#             elif tci_a.shape[0] > vci_a.shape[0] or tci_a.shape[1] > tci_a.shape[1]:
#                 # resample tci
#                 newarr = np.empty(shape=(vci_a.shape[0], vci_a.shape[1]))
#                 # adjust the new affine transform to the smaller cell size
#                 aff = tci_a.transform
#                 newaff = rasterio.Affine(aff.a / (vci_a.shape[0] / tci_a.shape[0]), aff.b, aff.c,
#                                          aff.d, aff.e / (vci_a.shape[1] / tci_a.shape[1]), aff.f)
#                 try:
#                     reproject(
#                         tci_a, newarr,
#                         src_transform=aff,
#                         dst_transform=newaff,
#                         src_crs=tci_a.crs,
#                         dst_crs=tci_a.crs,
#                         resample=RESAMPLING.bilinear)
#                 except Exception, e:
#                     print "Error in reproject "
#                 tci_a = np.ma.masked_where(np.ma.getmask(vci_a), newarr)
#
#             print vci_a.shape
#             print tci_a.shape
#             dst_f = np.zeros(vci_a.shape, np.float32)
#             newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(vci_a), np.ma.getmask(tci_a)),
#                                         dst_f)
#             newd_f += ((vci_a + tci_a) * 0.5)
#             res = newd_f.filled(fill_value=vci_r.nodata)
#             res2 = np.ma.masked_where(res == tci_r.nodata, res)
#             profile.update(dtype=rasterio.float32, nodata=-9999)
#             with rasterio.open(dst_filename, 'w', **profile) as dst:
#                 dst.write(res2.astype(rasterio.float32), 1)
    return 0