#!/usr/bin/env python

__author__ = 'rochelle'

# Import system modules
from os import listdir, path
import arcpy

def calcAverage(fileList, avgFile):
    print "calcAverage: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "MEAN")
    # Save the output
    outRaster.save(avgFile)
    print "saved avg in: ", avgFile
    return 0

def calcMin(fileList, minFile):
    print "calcAverage: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "MINIMUM")
    # Save the output
    outRaster.save(minFile)
    print "saved minimum in: ", minFile
    return 0

def calcMax(fileList, maxFile):
    print "calcAverage: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "MAXIMUM")
    # Save the output
    outRaster.save(maxFile)
    print "saved maximum in: ", maxFile
    return 0

def calcStDev(fileList, sdFile):
    print "calcAverage: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "STD")
    # Save the output
    outRaster.save(sdFile)
    print "saved standard deviation in: ", sdFile
    return 0

def calcSum(fileList, sdFile):
    print "calcSum: ", fileList
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(fileList, "SUM")
    # Save the output
    outRaster.save(sdFile)
    print "saved sum in: ", sdFile
    return 0
