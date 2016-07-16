#!/usr/bin/env python

__author__ = 'rochelle'

# Import system modules
from os import listdir, path
#import arcpy
import rasterio
import numpy as np

def calcAverage(fileList, avgFile):
    print "calcAverage: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "MEAN")
    # Save the output
    outRaster.save(avgFile)
    print "saved avg in: ", avgFile
    return 0

def calcAverage_os(fileList, avgFile):
    print "calcAverage: ", fileList
    if fileList:
        arrayList = []
        first = True
        profile = None
        for f in fileList:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.vstack(arrayList)
        dst_r = np.mean(dst_a, axis=0)
        with rasterio.open(avgFile, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float64), 1)


def calcMin(fileList, minFile):
    print "calcMin: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "MINIMUM")
    # Save the output
    outRaster.save(minFile)
    print "saved minimum in: ", minFile
    return 0


def calcMin_os(fileList, minFile):
    print "calcMin (open source version): ", fileList
    if fileList:
        arrayList = []
        first = True
        profile = None
        for f in fileList:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.vstack(arrayList)
        dst_r = np.amin(dst_a, axis=0)
        with rasterio.open(minFile, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float64), 1)
            print "saved minimum in: ", minFile


def calcMax(fileList, maxFile):
    print "calcAverage: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "MAXIMUM")
    # Save the output
    outRaster.save(maxFile)
    print "saved maximum in: ", maxFile
    return 0

def calcMax_os(fileList, maxFile):
    print "calcMax (open source version): ", fileList
    if fileList:
        arrayList = []
        first = True
        profile = None
        for f in fileList:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.vstack(arrayList)
        dst_r = np.amax(dst_a, axis=0)
        with rasterio.open(maxFile, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float64), 1)
            print "saved maximum in: ", maxFile


def calcStDev(fileList, sdFile):
    print "calcStDev: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "STD")
    # Save the output
    outRaster.save(sdFile)
    print "saved standard deviation in: ", sdFile
    return 0

def calcStDev_os(fileList, sdFile):
    print "calcStDev (open source version): ", fileList
    if fileList:
        arrayList = []
        first = True
        profile = None
        for f in fileList:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.vstack(arrayList)
        dst_r = np.std(dst_a, axis=0, ddof=1)
        with rasterio.open(sdFile, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float64), 1)
            print "saved standard deviation in: ", sdFile

def calcSum(fileList, sdFile):
    print "calcSum: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "SUM")
    # Save the output
    outRaster.save(sdFile)
    print "saved sum in: ", sdFile
    return 0

def calcSum_os(fileList, sdFile):
    print "calcSum (open source version): ", fileList
    if fileList:
        arrayList = []
        first = True
        profile = None
        for f in fileList:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.vstack(arrayList)
        dst_r = np.sum(dst_a, axis=0, ddof=1)
        with rasterio.open(sdFile, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float64), 1)
            print "saved standard deviation in: ", sdFile

