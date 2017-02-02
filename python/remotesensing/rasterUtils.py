__author__ = 'rochelle'
#!/usr/bin/env python
# Import system modules
import os
import subprocess
#from subprocess import call, check_call, check_output, Popen, CalledProcessError, STDOUT

import utilities

def clipRasterToShp(shpfile, in_raster, out_raster, gdal_path, nodata=False,
                    srcnodata=None, dstnodata=None, logger=None):
    # call gdalwarp to clip to shapefile
    try:
        if logger: logger.debug("%s",shpfile)
        if logger: logger.debug("%s",in_raster)
        if logger: logger.debug("%s",out_raster)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        options = [gdal_exe]
        options.append('--config')
        options.append('GDALWARP_IGNORE_BAD_CUTLINE')
        options.append('YES')
        options.append('-t_srs')
        options.append('EPSG:4326')
        if nodata:
            options.append('-srcnodata')
            options.append('-9999')
            options.append('-dstnodata')
            options.append('-9999')
        if srcnodata:
            options.append('-srcnodata')
            options.append('{0}'.format(srcnodata))
        if dstnodata:
            options.append('-dstnodata')
            options.append('{0}'.format(dstnodata))
        options.append('-overwrite')
        options.append('-crop_to_cutline')
        options.append('-cutline')
        options.append(shpfile)
        options.append(in_raster)
        options.append(out_raster)
#        cal = '~/Downloads/gdal-1.10.1+dfsg/apps/gdalwarp -t_srs EPSG:4326 -srcnodata -3000 -dstnodata -9999 -overwrite -crop_to_cutline -cutline {0} {1} {2}'.format(shpfile, in_raster, out_raster)
#        retcode = subprocess.call(cal, stderr=subprocess.STDOUT, shell=True)
        retcode = subprocess.call(args=options, stderr=subprocess.STDOUT)
#            print "gdalwarp -overwrite', '-t_srs', 'EPSG:4326', '-crop_to_cutline', '-cutline' {0}, {1}, {2}".format(shpfile, in_raster, out_raster)
        if logger: logger.debug("gdalwarp return code is %s", retcode)
    except subprocess.CalledProcessError as e:
        if logger: logger.error("Error in gdalwarp")
        if logger: logger.error("%s",e.output)
#        raise
    except Exception, e:
        if logger: logger.error("Warning in gdalwarp")
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

def cropFiles(base_path, output_path, bounds, tools_path, patterns = None,
              overwrite = False, nodata=True, dstnodata=None, srcnodata=None, logger = None):
#    import re
    fileslist = []
    if not patterns[0]:
        # if no pattern, try all files
        _p = '*'
    else:
        _p = patterns[0]

    _all_files = utilities.directoryUtils.getMatchingFiles(base_path, _p)

    for ifl in _all_files:
        _f= os.path.basename(os.path.basename(ifl))
#        m = re.match(_p, _f)
        new_filename = utilities.filenameUtils.generateOutputFilename(_f, _p, patterns[1])
        out_raster = os.path.join(output_path, new_filename)

        if not os.path.exists(out_raster) or overwrite == True:
            # crop file here
            if logger: logger.debug("Cropping file: %s",ifl)
            if os.path.splitext(ifl)[1] == '.gz':
                # unzip first
                utilities.directoryUtils.unzipFile(ifl)
                ifl = ifl[:-3] # remove .gz from filename
            if srcnodata or dstnodata:
                nodata = False
            clipRasterToShp(shpfile=bounds, in_raster=ifl, out_raster=out_raster, gdal_path=tools_path,
                            nodata=nodata, srcnodata=srcnodata, dstnodata=dstnodata)
            fileslist.append(new_filename)
    return fileslist

def resampleRaster(in_raster, out_raster, gdal_path,
                   outX_pc=None, outY_pc=None, trX=None, trY=None,
                   src_nodata=None, dst_nodata=None, logger=None):
    try:
        if logger: logger.debug("%s", in_raster)
        if logger: logger.debug("%s", out_raster)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        options = [gdal_exe]

        # output size (percentage) specified
        if outX_pc:
            options.append('-outsize')
            options.append("{0}%".format(outX_pc))
            if outY_pc:
                options.append("{0}%".format(outY_pc))
            else:
                options.append("100.0%")
        elif outY_pc:
            options.append('-outsize')
            options.append("100%")
            options.append("{0}%".format(outY_pc))

        # target resolution specified
        if trX:
            options.append('-r')
            options.append('bilinear')
            options.append('-tr')
            options.append('{0}'.format(trX))
            if trY:
                options.append('{0}'.format(trY))
            else:
                options.append('{0}'.format(trX))
        elif trY:
            options.append('-r')
            options.append('bilinear')
            options.append('-tr')
            options.append('{0}'.format(trY))
            options.append('{0}'.format(trY))

        # no data specified
        if src_nodata:
            options.append('-srcnodata')
            options.append('{0}'.format(src_nodata))
        if dst_nodata:
            options.append('-dstnodata')
            options.append('{0}'.format(dst_nodata))

        options.append(in_raster)
        options.append(out_raster)
        retcode = subprocess.call(options)
#        [gdal_exe, '-outsize', xPc, yPc, '-r', 'bilinear', in_raster,
#         out_raster])
        if logger: logger.debug("gdalwarp return code is %s", retcode)
    except subprocess.CalledProcessError as e:
        if logger: logger.error("Error in gdalwarp")
        if logger: logger.error("%s", e.output)
        #        raise
    except Exception, e:
        if logger: logger.error("Warning in gdalwarp")

    return 0

def reprojectRaster(in_raster, out_raster, gdal_path, t_srs=None, overwrite=False, logger=None):
    try:
        if logger: logger.debug("%s", in_raster)
        if logger: logger.debug("%s", out_raster)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        options = [gdal_exe]
        options.append('-srcnodata')
        options.append('-3000')
        options.append('-dstnodata')
        options.append('-9999')
        if overwrite:
            options.append('-overwrite')
        if t_srs:
            options.append('-t_srs')
            options.append("{0}".format(t_srs))
        options.append(in_raster)
        options.append(out_raster)
        retcode = subprocess.call(options)
        if logger: logger.debug("gdalwarp return code is %s", retcode)
    except subprocess.CalledProcessError as e:
        if logger: logger.error("Error in gdalwarp")
        if logger: logger.error("%s", e.output)
        #    raise
    except Exception, e:
        if logger: logger.error("Warning in gdalwarp")
    return 0


def setRasterNoDataValues(in_raster, out_raster, gdal_path, dst_nodata=None, src_nodata=None,
                          output_type = None, overwrite=False, logger=None):
    try:
        if logger: logger.debug("%s", in_raster)
        if logger: logger.debug("%s", out_raster)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        options = [gdal_exe]
        if src_nodata:
            options.append('-srcnodata')
            options.append("{0}".format(src_nodata))
        if dst_nodata:
            options.append('-dstnodata')
            options.append("{0}".format(dst_nodata))
        if overwrite:
            options.append('-overwrite')
        if output_type:
            options.append('-ot')
            options.append(output_type)
        options.append(in_raster)
        options.append(out_raster)
        retcode = subprocess.call(options)
        if logger: logger.debug("gdalwarp return code is %s", retcode)
    except subprocess.CalledProcessError as e:
        if logger: logger.error("Error in gdalwarp")
        if logger: logger.error("%s", e.output)
        #        raise
    except Exception, e:
        if logger: logger.error("Warning in gdalwarp")

    return 0
