__author__ = 'rochelle'
#!/usr/bin/env python
# Import system modules
import os
from subprocess import check_call, CalledProcessError

import directoryUtils
import filenameUtils


def clipRasterToShp(shpfile, in_raster, out_raster, gdal_path, logger=None):
    # call gdalwarp to clip to shapefile
    try:
        if logger: logger.debug("%s",shpfile)
        if logger: logger.debug("%s",in_raster)
        if logger: logger.debug("%s",out_raster)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        check_call([gdal_exe, '-srcnodata', '-9999', '-dstnodata', '-9999', '-crop_to_cutline', '-cutline', shpfile, in_raster, out_raster])
    except CalledProcessError as e:
        if logger: logger.error("Error in gdalwarp")
        if logger: logger.error("%s",e.output)
        raise
    return 0

# def clipRastersInDirToShape(base_path, output_path, shapefile, filenames, output_filenames, gdal_path):
#     filesList = directoryUtils.buildFileList(base_path, filenames[1])
#     for ras in filesList:
#     #    newras = os.path.join(outfolder, ras + "_Clip")
#         ras_fn = os.path.split(ras)[1]
#         newras = os.path.join(output_path, "{0}{1}".format(str.replace(os.path.splitext(ras_fn)[0], filenames[0], output_filenames[0]), output_filenames[1]))
#         if os.path.isfile(newras) == False:
#             print "clipping: " + ras + " to " + newras
#             clipRasterToShp(shapefile, ras, newras, gdal_path)
# #        clippedRasters.append(newras)
#     print("successfully clipped rasters")
#     return 0

def cropFiles(base_path, output_path, bounds, tools_path, patterns = None, overwrite = False, logger = None):
#    import re
    fileslist = []
    if not patterns[0]:
        # if no pattern, try all files
        _p = '*'
    else:
        _p = patterns[0]

    _all_files = directoryUtils.getMatchingFiles(base_path, _p)

    for ifl in _all_files:
        _f= os.path.basename(os.path.basename(ifl))
#        m = re.match(_p, _f)
        new_filename = filenameUtils.generateOutputFilename(_f, _p, patterns[1])
        out_raster = os.path.join(output_path, new_filename)

        if not os.path.exists(out_raster) or overwrite == True:
            # crop file here
            if logger: logger.debug("Cropping file: %s",ifl)
            if os.path.splitext(ifl)[1] == '.gz':
                # unzip first
                directoryUtils.unzipFile(ifl)
                ifl = ifl[:-3] # remove .gz from filename
            clipRasterToShp(bounds, ifl, out_raster, tools_path)
            fileslist.append(new_filename)
    return fileslist

def rasterToNPArray(rasterName):
    return 0
