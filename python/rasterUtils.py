__author__ = 'rochelle'
#!/usr/bin/env python
# Import system modules
from arcpy import env
import os, sys
from subprocess import check_call, CalledProcessError, STDOUT
from directoryUtils import buildFileList

def clipRasterToShp(shpfile, in_raster, out_raster, gdal_path):
    # call gdalwarp to clip to shapefile
    try:
        print(shpfile)
        print(in_raster)
        print(out_raster)
        check_call([gdal_path + 'gdalwarp', '-srcnodata', '-9999', '-dstnodata', '-9999', '-crop_to_cutline', '-cutline', shpfile, in_raster, out_raster])
    except CalledProcessError as e:
        print("Error in gdalwarp")
        print(e.output)
        raise
    return 0

def clipRastersInDirToShape(base_path, output_path, shapefile, filenames, output_filenames, gdal_path):
    filesList = buildFileList(base_path, filenames[1])
    for ras in filesList:
    #    newras = os.path.join(outfolder, ras + "_Clip")
        ras_fn = os.path.split(ras)[1]
        newras = os.path.join(output_path, "{0}{1}".format(str.replace(os.path.splitext(ras_fn)[0], filenames[0], output_filenames[0]), output_filenames[1]))
        if os.path.isfile(newras) == False:
            print "clipping: " + ras + " to " + newras
            clipRasterToShp(shapefile, ras, newras, gdal_path)
#        clippedRasters.append(newras)
    print("successfully clipped rasters")
    return 0