#!/usr/bin/env python
__author__ = 'rochelle'
import os

#import arcpy
import numpy
import numpy.ma
from osgeo import gdal
import rasterio
#from arcpy.sa import Con, IsNull, SetNull, HighestPosition, BooleanAnd, BooleanNot, Raster, CellStatistics, \
#    Divide


# Find the last day with precipitation greater than threshold in the list of rasters
# returns a raster of number of days since last rain
# Reclassify raster to 1 if >= 0.5mm rainfall, 0 otherwise (wet days)
def reclassifyWetDay(in_raster, out_raster, threshold):
    arcpy.env.extent="MAXOF"
    arcpy.env.cellSize="MAXOF"
    ras = arcpy.sa.Raster(in_raster)

    ds = gdal.Open(in_raster)
    ras_array = numpy.array(ds.GetRasterBand(1).ReadAsArray())
    ras_array[ras_array == -9999] = numpy.nan
    ras_array[ras_array < threshold] = 0
    ras_array[ras_array >= threshold] = 1
    out_ras = arcpy.NumPyArrayToRaster(ras_array, x_cell_size = ras.meanCellWidth,
                                                 y_cell_size = ras.meanCellHeight)
    out_ras.save(out_raster)

#    ras = arcpy.sa.Raster(in_raster)
#    ras.save("s:/WFP/MODIS/Scratch/rasout.tif")
##    out_con = arcpy.CopyRaster_management(ras, out_raster, "DEFAULTS", "", "-9999", "", "", "32_BIT_UNSIGNED")
##    out_con = arcpy.sa.Reclassify(out_con, "Value", arcpy.sa.RemapRange([[0.0, 0.5, 0], [0.5, 9999, 1]]) )
#    out_con = Con(Raster(in_raster) >= threshold, 1.0, 0.0)
##    out_con = Con(ras, 1, 0, "VALUE >= 0.5")
#    out_con.save(out_raster)
    return 0

# Reclassify raster to 1 if < 0.5mm rainfall, 0 otherwise (dry days)
def reclassifyDryDay(in_raster, out_raster, threshold):
    arcpy.env.extent="MAXOF"
    arcpy.env.cellSize="MAXOF"
    ras = arcpy.sa.Raster(in_raster)
    out_con = Con(ras < threshold, 1, 0)
    out_con.save(out_raster)
    return 0


#calculate number of days since last wet day
def lastWetDay(rasters, outraster, maxdays):

    counter = 0
    # initialise masks - noDataMask is 1 where there is No Data, 0 otherwise
    # dryMask is 1 if rainfall is 0, and -999 if No Data
    noDataMask = Con(IsNull(rasters[0]), 1, 0)
    dryMask = Con(rasters[0], 1, 0, "VALUE <= 0")
    dryMask = Con(IsNull(dryMask), -999, dryMask)

    #collect X=numDays consecutive rasters
    # rasters still contain NoData values
    lastXRasters = []
    # make sure we have enough data
    if counter+maxdays > len(rasters):
        maxdays = len(rasters)-counter
    #
    for i in range(counter,(counter+maxdays)):
        # create NoData mask where *all* rasters have NoData
        noDataMask = BooleanAnd(noDataMask, Con(IsNull(rasters[i]), 1, 0))
        # temporarily set No Data values to -999 so the grid cell isn't ignored
        tempRaster = Con(IsNull(rasters[i]), -999, rasters[i])
        # dryMask is 1 if dry day (<0.5mm rain) OR No Data
        dryMask = BooleanAnd(dryMask, Con(tempRaster, 1, 0, "VALUE <= 0"))
        #remove NoData
        rasters[i] = Con(IsNull(rasters[i]), 0, rasters[i])
        lastXRasters.append(rasters[i])

    # create raster with number of days since last rain
    outHighestPosition = HighestPosition(lastXRasters)

#    noDataMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/noDataMask.tif")
    dryMask = Con(IsNull(dryMask), -999, dryMask)
 #   dryMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/dryMask.tif")
#    outHighestPosition.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/hp.tif")
    # reset NoData
    outFinal = SetNull(noDataMask, outHighestPosition, "VALUE >= 1")
  #  outFinal.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/outFinal.tif")
    outFinal2 = Con(dryMask, -999, outFinal, "VALUE >= 1")

    # Save the output
    outFinal2.save(outraster)
    return 0

#calculate number of days since the last wet (dslw) or dry (dsld) day
# assumes input raster is 1 for wet and 0 for dry
# for example to calculate the number of days since last wet day, all days classified as "wet"
# will be 1 and the rest 0. Days with no data should be No Data
def calcNumDaysSince(rasters, dslw_fn, dsld_fn, maxdays):

    counter = 0
    # initialise masks - noDataMask is 1 where there is No Data across all rasters, 0 otherwise
    # since some regions will have No Data for some days, but valid data on other days. Need to
    # include these regions ALL the time.
    noDataMask = Con(IsNull(rasters[0]), 1, 0)
    # Highest Position provides position for all cell values - we need to mask out the dry cells
    # dryMask is 1 if rainfall is 0 (dry), and -999 if No Data
    # wetMask is 1 if rainfall is 1 (wet), and -999 if No Data
    dryMask = Con(rasters[0], 1, 0, "VALUE <= 0")
    wetMask = BooleanNot(dryMask)
    dryMask = Con(IsNull(dryMask), -999, dryMask)
    wetMask = Con(IsNull(wetMask), -999, wetMask)

    #collect X=numDays consecutive rasters
    # rasters still contain NoData values
    lastXRasters = []
    lastDryRasters = []
    # make sure we have enough data
    if counter+maxdays > len(rasters):
        maxdays = len(rasters)-counter
    #
    for i in range(counter,(counter+maxdays)):
        # create NoData mask where *all* rasters have NoData
        noDataMask = BooleanAnd(noDataMask, Con(IsNull(rasters[i]), 1, 0))
        # temporarily set No Data values to -999 so the grid cell isn't ignored
        # in calculations
        tempRaster = Con(IsNull(rasters[i]), -999, rasters[i])
        # dryMask is 1 if dry day (<0.5mm rain) OR No Data
        dryMask = BooleanAnd(dryMask, Con(tempRaster, 1, 0, "VALUE <= 0"))
        wetMask = BooleanAnd(wetMask, Con(tempRaster, 1, 0, "VALUE <> 0"))
        # raster[i] is 1 if wet, 0 if dry. inverseRaster = 0 if wet, 1 if dry
        inverseRaster = BooleanNot(rasters[i])
        #remove NoData
        rasters[i] = Con(IsNull(rasters[i]), 0, rasters[i])
        inverseRaster = Con(IsNull(inverseRaster), 0, inverseRaster)
        lastXRasters.append(rasters[i])
        lastDryRasters.append(inverseRaster)

    # create raster with number of days since last rain
    daysSinceLastWet = HighestPosition(lastXRasters)
    daysSinceLastDry = HighestPosition(lastDryRasters)
#    daysSinceLastDry.save(env.workspace + "/lwd/output/dsld.tif")

#    noDataMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/noDataMask.tif")
    dryMask = Con(IsNull(dryMask), -999, dryMask)
    wetMask = Con(IsNull(wetMask), -999, wetMask)
#    wetMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/wetMask.tif")
#    dryMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/dryMask.tif")
#    outHighestPosition.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/hp.tif")
    # reset NoData
    outFinal = SetNull(noDataMask, daysSinceLastWet, "VALUE >= 1")
    outFinal3 = SetNull(noDataMask, daysSinceLastDry, "VALUE >= 1")
#    outFinal.save(env.workspace + "/lwd/output/outdslw.tif")
#    outFinal3.save(env.workspace + "/lwd/output/outdsld.tif")
    outFinal2 = Con(dryMask, -999, outFinal, "VALUE >= 1")
    outFinal4 = Con(wetMask, -999, outFinal3, "VALUE >= 1")

    # Save the output
    outFinal2.save(dslw_fn)
    outFinal4.save(dsld_fn)
    return 0

def daysSinceLast(base_path, output_path, temp_path, rasters, output_filenames = ('idn_phy_MOD13Q1', '.tif'), threshold=0.5, maxdays=30):
    # reclassify rasters to wet or dry - >0.5 = 1 (wet), <0.5 = 0 (dry)
    reclassRasters = []
    rastersList = arcpy.ListRasters()
    count = 0
    for ras in rasters:
        # only look at last 'maxdays' rasters
        if count < maxdays:
            newras = os.path.join(temp_path, '{0}_wd{1}'.format((os.path.splitext(os.path.basename(ras))[0])[:9], output_filenames[1]))
#            newras = os.path.join(temp_path, '{0}_wd{1}'.format(os.path.splitext(os.path.basename(ras))[0], output_filenames[1]))
    ##        newras = temp_path + '/' + os.path.splitext(os.path.basename(ras))[0] + '_wd' + '.tif'
            # check if file exists
            if os.path.isfile(newras) == False:
                reclassifyWetDay(ras, newras, threshold)
            reclassRasters.append(newras)
            count += 1
        else:
            break
    print("successfully reclassified rasters")
    reclassRasters.sort(reverse=True)
    print(reclassRasters)

    # calculate last wet day
#    dslwfile = env.workspace + "/lwd/output/dslw25_29.tif"
    dslwfile = os.path.join(output_path, '{0}_dslw{1}'.format(output_filenames[0], output_filenames[1]))
#    dsldfile = env.workspace + "/lwd/output/dsld25_29.tif"
    dsldfile = os.path.join(output_path, '{0}_dsld{1}'.format(output_filenames[0], output_filenames[1]))
    #lastWetDay(reclassRasters, outputfile, len(reclassRasters))
    calcNumDaysSince(reclassRasters, dslwfile, dsldfile, count)
    print("successfully calculated last wet day")

    # calculate number of wet days
    cellStats = CellStatistics(reclassRasters, "SUM")
    fname = os.path.join(output_path, '{0}_nwd{1}'.format(output_filenames[0], output_filenames[1]))
    cellStats.save(fname)
    # calculate total rainfall
    fname = os.path.join(output_path, '{0}_tot_precip{1}'.format(output_filenames[0], output_filenames[1]))
    cellStats = CellStatistics(rasters, "SUM")
    cellStats.save(fname)
    return 0

# calculate a rainfall anomaly surface as int(100 * (current rainfall/long-term average rainfall) )
def calcRainfallAnomaly(cur_filename, lta_filename, dst_filename):
    cur_Raster = Raster(cur_filename)
    lta_Raster = Raster(lta_filename)
    dst_f = arcpy.sa.Divide(cur_Raster, lta_Raster)
    dst_100f = arcpy.sa.Times(dst_f, 100)
    dst = arcpy.sa.Int(dst_100f)
    dst.save(dst_filename)
    return 0

# calculate a rainfall anomaly surface as int(100 * (current rainfall/long-term average rainfall) )
def calcRainfallAnomaly_os(cur_filename, lta_filename, dst_filename):
    # arcpy-free version
    with rasterio.open(cur_filename) as cur_r:
        cur_band = cur_r.read(1, masked=True)
        profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_filename) as lta_r:
            lta_a = lta_r.read(1, masked=True)
            dst_f = numpy.zeros(cur_band.shape)
            newd_f = numpy.ma.masked_where(numpy.ma.mask_or(numpy.ma.getmask(cur_band), numpy.ma.getmask(lta_r)), dst_f)
            newd_f += numpy.divide(cur_band, lta_a) * 100.0
            newd_f.astype(int)
            res = newd_f.filled(fill_value=cur_r.nodata)
            res2 = numpy.ma.masked_where(res==cur_r.nodata, res)
            profile.update(dtype=rasterio.int32)
            with rasterio.open(path=dst_filename, mode='w', **profile) as dst:
                dst.write(res2.astype(rasterio.int32), 1)
    return 0
