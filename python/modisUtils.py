__author__ = 'rochelle'
#!/usr/bin/env python

import os
import errno
from collections import defaultdict
from directoryUtils import buildFileList
from subprocess import check_call, CalledProcessError, STDOUT
from rasterUtils import clipRasterToShp

#toolspath = "/Volumes/Rochelle External/WFP/MODIS/MODIS Reprojection Tool/bin/"

def getMODISYrAndDoY(filename):
    d = filename.split('.', 2)[1]
    return d

def generateParamFile(wdir, pfile, infile, outfile, extras = []):
    # generate parameter file
    pname = os.path.join(wdir, pfile)
    try:
        pfile = open(pname, 'w')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "some default data"
        # Not a permission error.
        raise
    else:
        with pfile:
            pfile.write('INPUT_FILENAME = "' + infile + '"\n')
            pfile.write('OUTPUT_FILENAME = "' + outfile + '"\n')
            pfile.write('OUTPUT_PROJECTION_TYPE = GEO\n')
            pfile.write('DATUM = WGS84\n')
            pfile.write('\n')
            for s in extras:
                pfile.write('{0}\n'.format(s))
            pfile.close()
    return 0

def reprojectMosaic(param_file, tools_path):
    # call resample using parameter file
    try:
        check_call([tools_path + 'resample', '-p', param_file])
    except CalledProcessError as e:
        print("Error in resample")
        print(e.output)
        raise
    return 0

def mosaicFiles(infile, outfile, toolspath):
    # call mrtmosaic using input filename
    try:
        check_call([toolspath + 'mrtmosaic', '-i', infile, '-o', outfile, '-s', "1 1"])
    except CalledProcessError as e:
        print("Error in mrtmosaic")
        print(e.output)
        return -1
    return 0

def writeMosaicList(fname, files = []):
    if files:
        try:
            pfile = open(fname, 'w')
        except IOError as e:
            if e.errno == errno.EACCES:
                return "Error creating file " + fname
            # Not a permission error.
            raise
        else:
            with pfile:
                for f in files:
                    pfile.write('"' + f + '"')
                    pfile.write('\n')
                pfile.close()
    return 0

def cropMODIS(base_path, output_path, bounds, tools_path, filenames = ('MOD13Q1', '.hdf'), output_filenames = ('idn_phy_MOD13Q1.005', '.hdf')):
    f_base = filenames[0] #'MOD13Q1'
    ext = filenames[1] #'.hdf'
    of_base = output_filenames[0]
    of_ext = output_filenames[1]
    all_files = buildFileList(base_path, ext)
    pfl = os.path.join(base_path, f_base + ".prm")
    for ifl in all_files:
        # only process files with correct extension
        if ifl.endswith(ext):
            fn = os.path.splitext(os.path.basename(ifl))
            out_raster = os.path.join(output_path, '{0}{1}{2}'.format(of_base, fn[0], of_ext))
            # crop file here
            print "Cropping file: " + ifl
            clipRasterToShp(bounds, ifl, out_raster, tools_path)
    return 0

# Mosaic all files with same date/day of year in the directory dname
def mosaicMODIS(base_path, output_path, tools_path, work_path, filenames = ('MOD13Q1', '.hdf')):
    f_base = filenames[0] #'MOD13Q1'
    ext = filenames[1] #'.hdf'
    all_files = buildFileList(base_path, ext)
    if not all_files:
        print 'No files found in ' + base_path + ', please check directory and try again'
        return -1
    param_file = os.path.join(work_path, f_base + ".prm")
    files_dict = defaultdict(list)
    for fl in all_files:
        if fl.endswith(ext):
            # add file to appropriate place in the dictionary
            yr_doy = getMODISYrAndDoY(fl)
            files_dict[yr_doy].append(fl)
    for i,v in files_dict.iteritems():
        # create a list file for mosaic for each day
        file_list = os.path.join(work_path, f_base + "_" + i + ".lst")
        writeMosaicList(file_list, v)
        mosaicname = os.path.join(output_path, '{0}.{1}.005_m{2}'.format(f_base, i, ext))
        # mosaic files for this day
        if mosaicFiles(file_list, mosaicname, tools_path) == -1:
            print 'Error generating mosaic ' + mosaicname
        else:
            outputname = os.path.join(output_path, '{0}.{1}.005{2}'.format(f_base, i, ext))
            generateParamFile(output_path, param_file, mosaicname, outputname)
            reprojectMosaic(param_file, tools_path)
            # remove temp file
            os.remove(mosaicname)
    return 0

def extractNDVI(base_path, output_path, tools_path, filenames = ('MOD13Q1', '.hdf'), output_filenames = ('idn_phy_MOD13Q1', '.tif')):
    f_base = filenames[0] #'MOD13Q1'
    ext = filenames[1] #'.hdf'
    of_base = output_filenames[0]
    of_ext = output_filenames[1]
    all_files = buildFileList(base_path, ext)
    if not all_files:
        print 'No files found in ' + base_path + ', please check directory and try again'
        return -1
    pfl = os.path.join(base_path, f_base + ".prm")
    for ifl in all_files:
        # only process files with correct extension
        if ifl.endswith(ext):
            # generate parameter file
            params = ['SPECTRAL_SUBSET = ( 1 0 0 0 0 0 0 0 0 0 0 )']
            doy = getMODISYrAndDoY(ifl)
            ofl = os.path.join(output_path, '{0}.{1}.005{2}'.format(of_base, doy, of_ext))
            generateParamFile(base_path, pfl, ifl, ofl, params)
            reprojectMosaic(pfl, tools_path)
    return 0

def extractEVI(base_path, output_path, tools_path, filenames = ('MOD13Q1', '.hdf'), output_filenames = ('idn_phy_MOD13Q1', '.tif')):
    f_base = filenames[0] #'MOD13Q1'
    ext = filenames[1] #'.hdf'
    of_base = output_filenames[0]
    of_ext = output_filenames[1]
    all_files = buildFileList(base_path, ext)
    if not all_files:
        print 'No files found in ' + base_path + ', please check directory and try again'
        return -1
    pfl = os.path.join(base_path, f_base + ".prm")
    for ifl in all_files:
        # only process files with correct extension
        if ifl.endswith(ext):
            # generate parameter file
            params = ['SPECTRAL_SUBSET = ( 0 1 0 0 0 0 0 0 0 0 0 )']
            doy = getMODISYrAndDoY(ifl)
            ofl = os.path.join(output_path, '{0}.{1}.005{2}'.format(of_base, doy, of_ext))
            generateParamFile(base_path, pfl, ifl, ofl, params)
            reprojectMosaic(pfl, tools_path)
    return 0

