__author__ = 'rochelle'
#!/usr/bin/env python

import datetime, time, calendar
import optparse, sys, os, traceback, errno

_defaults = {
    'gdal_dir' : '/usr/bin',
    'mrt_dir' : '/usr/bin/mrt/bin',
    'temp_dir' : '/tmp',
    'base_data_dir' : '/srv/Vampire/data/Download',
    'base_product_dir' : '/var/lib/opengeo/geoserver/data/IDN_GIS',
    'country_names' : {'IDN' : 'Indonesia'},
    'country_tiles' : {'IDN' : 'h27v08,h27v09,h27v10,h28v08,h28v09,h28v10,h29v08,h29v09,h29v10,h30v08,h30v09,h30v10,h31v08,h31v09,h31v10,h32v08,h32v09,h32v10',
                       },
    'chirps_boundary_file' : '_cli_chirps_20_005_deg_grid_diss_a.shp',
    'lst_min_file' : {'IDN' : 'idn_cli_MOD11C3.2000-2014.{0}.14yrs.min.tif'
                      },
    'lst_max_file' : {'IDN' : 'idn_cli_MOD11C3.2000-2014.{0}.14yrs.max.tif'},
    'tci_file' : {'IDN' : 'idn_cli_MOD11C3.{0}{1}.005.tif'},
}

def generateHeaderDirectory(output):
    try:
        pfile = open(output, 'w')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            file_string = """
directory:
    GDAL: {gdal_dir}
    MRT: {mrt_dir}
""".format(gdal_dir=_defaults['gdal_dir'], mrt_dir=_defaults['mrt_dir'])
            pfile.write(file_string)
            pfile.close()
    return pfile.name

def generateHeaderRun(output):
    try:
        pfile = open(output, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            file_string = """
run:
"""
            pfile.write(file_string)
            pfile.close()
    return pfile.name

def generateHeaderCHIRPS(output):
    try:
        pfile = open(output, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            file_string = """
    temp: {temp_dir}

CHIRPS:
    filenames:
        input_prefix: chirps-v2.0
        input_extension: .tiff
        output_prefix: idn_cli_chirps-v2.0
        output_ext: .tif
""".format(temp_dir=_defaults['temp_dir'])
            pfile.write(file_string)
            pfile.close()
    return pfile.name

def generateRainfallLongTermAverageConfig(country, interval, start_date, output):
    try:
        pfile = open(output, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            year = start_date.strftime("%Y")
            month = start_date.strftime("%m")
            if interval == 'monthly':
                _interval_name = 'month'
            else:
                _interval_name = interval
            _input_dir = "{0}/Download/CHIRPS/{1}/{2}".format(_defaults['base_data_dir'], interval.capitalize(),
                                                                country)
            if country == 'IDN':
                _output_dir = "{0}/01_Data/02_IDN/Rasters/Climate/Precipitation/CHIRPS/{1}/Statistics_By{2}" \
                    .format(_defaults['base_product_dir'], interval.capitalize(), _interval_name.capitalize())
            else:
                _output_dir = "{0}/01_Data/03_Regional/{1}/Rasters/Climate/Precipitation/CHIRPS/{2}/Statistics_By{3}" \
                    .format(_defaults['base_product_dir'], country, interval.capitalize(), _interval_name.capitalize())

            file_string = """
#    - process: CHIRPS
#      type: monthly
#      input_dir: {input_dir}
#      output_dir: {output_dir}""".format(input_dir=_input_dir, output_dir=_output_dir)
            pfile.write(file_string)
            pfile.close()
    return pfile.name


def generateRainfallAnomalyConfig(country, interval, start_date, output):
    try:
        pfile = open(output, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            year = start_date.strftime("%Y")
            month = start_date.strftime("%m")
            if interval == 'monthly':
                _interval_name = 'month'
            else:
                _interval_name = interval
            _dl_output = "{0}/CHIRPS/{1}".format(_defaults['base_data_dir'], interval.capitalize())
            _crop_output_pattern = "'{0}".format(country.lower()) + "_cli_{product}.{year}.{month}{extension}'"
            if country == 'IDN':
                _boundary_file = "{0}/01_Data/02_IDN/ShapeFiles/Boundaries/National/" \
                                 "idn_bnd_subset_chirps_20_005_deg_grid_diss_a.shp".format(_defaults['base_product_dir'])
                _longterm_avg_file = "{0}/01_Data/02_IDN/Rasters/Climate/Precipitation/CHIRPS" \
                "/{2}/Statistics_By{3}/idn_cli_chirps-v2.0.1981-2014.{1}.{4}.34yrs.avg.tif".format(
                    _defaults['base_product_dir'], month, interval.capitalize(), _interval_name.capitalize(), interval.lower())

            else:
                _boundary_file = "{0}/01_Data/03_Regional/{01}/ShapeFiles/Boundaries/Subset/CHIRPS/" \
                                 "{02}_cli_chirps_20_005_deg_grid_diss_a.shp".format(
                    _defaults['base_product_dir'], country, country.lower())
            file_pattern = '^(?P<product>chirps-v2.0).(?P<year>\d{4}).(?P<month>\d{2})(?P<extension>\.tif).*'
            file_string = """
## Processing chain begin - Compute Rainfall Anomaly\n
    # download CHIRPS precipitation data for {0}
    - process: CHIRPS
      type: download
      interval: {1}
      output_dir: {2}
      dates: [{3}-{4}]

    # crop data to region
    - process: Raster
      type: crop
      input_dir: {2}
      output_dir: {2}/{9}
      file_pattern: {13}
      output_pattern: {6}
      boundary_file: {7}

    # compute rainfall anomaly
    - process: Analysis
      open_source:
      type: rainfall_anomaly
      current_file: {2}/{9}/{10}_cli_chirps-v2.0.{3}.{4}.tif
      longterm_avg_file: {11}
      output_file: {12}/CHIRPS/Monthly/{9}/Rainfall_Anomaly/{10}_cli_chirps-v2.0.{3}.{4}.ratio_anom.tif
## Processing chain end - Compute Rainfall Anomaly

""".format(_defaults['country_names'][country], interval, _dl_output, year, month, interval.capitalize(),
            _crop_output_pattern, _boundary_file, _defaults['base_data_dir'], country, country.lower(),
            _longterm_avg_file, _defaults['base_data_dir'], file_pattern)
            pfile.write(file_string)
            pfile.close()
    return pfile.name

def generateVCIConfig(country, interval, start_date, output):
    try:
        pfile = open(output, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            year = start_date.strftime("%Y")
            month = start_date.strftime("%m")
            basedate = datetime.datetime.strptime("2000.{0}.01".format(month), "%Y.%m.%d")
            dayofyear = basedate.timetuple().tm_yday
            if calendar.isleap(int(year)) and dayofyear > 60:
                dayofyear = dayofyear - 1

            if country == 'IDN':
                _boundary_file = "{0}/01_Data/02_IDN/ShapeFiles/Boundaries/Subset/MODIS/idn_phy_modis_1km_grid_diss_a.shp".format(
                    _defaults['base_product_dir'])
                _output_pattern = 'idn_phy_{product}.{year}.{month}.{day}.{version}.{subset}{extension}'
                _EVI_max_file = '{0}/01_Data/02_IDN/Rasters/Vegetation/MOD13A3.EVI/Statistics_ByMonth/idn_phy_MOD13A3' \
                        '.2000-2015.{1}.1_km_monthly_EVI.15yrs.max.tif'.format(_defaults['base_product_dir'],
                                                                               str(dayofyear).zfill(3))
                _EVI_min_file = '{0}/01_Data/02_IDN/Rasters/Vegetation/MOD13A3.EVI/Statistics_ByMonth/idn_phy_MOD13A3' \
                        '.2000-2015.{1}.1_km_monthly_EVI.15yrs.min.tif'.format(_defaults['base_product_dir'],
                                                                               str(dayofyear).zfill(3))
            else:
                _boundary_file = "{0}/01_Data/03_Regional/{1}/ShapeFiles/Boundaries/Subset/MODIS/{2}_phy_modis_1km_grid_diss_a.shp".format(
                    _defaults['base_product_dir'], country, country.lower())
                _output_pattern = "'{0}".format(country.lower()) + "_phy_{product}.{year}.{month}.{day}.{version}.{subset}{extension}'"
                _EVI_max_file = '{0}/01_Data/03_Regional/{1}/Rasters/Vegetation/MOD13A3.EVI/Statistics_ByMonth/idn_phy_MOD13A3' \
                        '.2000-2015.{2}.1_km_monthly_EVI.15yrs.max.tif'.format(_defaults['base_product_dir'], country,
                                                                               str(dayofyear).zfill(3))
                _EVI_min_file = '{0}/01_Data/03_Regional/{1}/Rasters/Vegetation/MOD13A3.EVI/Statistics_ByMonth/idn_phy_MOD13A3' \
                        '.2000-2015.{2}.1_km_monthly_EVI.15yrs.min.tif'.format(_defaults['base_product_dir'], country,
                                                                               str(dayofyear).zfill(3))
            _output_file = "{product_dir}/05_Analysis/03_Early_Warning/Vegetation_Condition_Index" \
                    "/{country_l}_phy_MOD13A3.{year}.{month}.1_km_monthly_EVI_VCI.tif".format(product_dir=_defaults['base_product_dir'],
                                                                                              country_l=country.lower(),
                                                                                              year=year, month=month)

            pattern = '^(?P<product>MOD\d{2}A\d{1}).(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2}).(?P<version>\d{3}).(?P<subset>.*)(?P<extension>\.tif$)'


            file_string = """
## Processing chain begin - Compute Vegetation Condition Index
    # download MODIS vegetation data (MOD13A3.005) tiles for {country_name} and mosaic
    - process: MODIS
      type: download
      output_dir: {data_dir}/MODIS/MOD13A3/HDF_MOD
      mosaic_dir: {data_dir}/MODIS/MOD13A3/Processed/HDF_MOD
      product: MOD13A3.005
      tiles: {tiles}
      dates: [{year}-{month}]

    # extract MODIS NDVI and EVI
    - process: MODIS
      type: extract
      layer: NDVI
      input_dir: {data_dir}/MODIS/MOD13A3/Processed/HDF_MOD
      output_dir: {data_dir}/MODIS/MOD13A3/Processed/NDVI

    - process: MODIS
      type: extract
      layer: EVI
      input_dir: {data_dir}/MODIS/MOD13A3/Processed/HDF_MOD
      output_dir: {data_dir}/MODIS/MOD13A3/Processed/EVI

    # crop data to region
    - process: Raster
      type: crop
      file_pattern: {file_pattern}
      output_pattern: {pattern}
      input_dir: {data_dir}/MODIS/MOD13A3/Processed/EVI
      output_dir: {data_dir}/MODIS/MOD13A3/Processed/{country}_EVI
      boundary_file: {boundary}

    - process: Analysis
      type: VCI
      current_file: {data_dir}/MODIS/MOD13A3/Processed/{country}_EVI/{country_l}_phy_MOD13A3.{year}.{month}.01.005.1_km_monthly_EVI.tif
      EVI_max_file: {evi_max}
      EVI_min_file: {evi_min}
      output_file: {output_file}
## Processing chain end - Compute Vegetation Condition Index
""".format(country_name=_defaults['country_names'][country], data_dir=_defaults['base_data_dir'],
           tiles=_defaults['country_tiles'][country], year=year, month=month, file_pattern=pattern,
           pattern=_output_pattern, country=country,
           boundary=_boundary_file, country_l=country.lower(), evi_max=_EVI_max_file, evi_min=_EVI_min_file,
           output_file=_output_file)

            pfile.write(file_string)
            pfile.close()

    return pfile.name

def generateTCIConfig(country, interval, start_date, output):
    try:
        pfile = open(output, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            year = start_date.strftime("%Y")
            month = start_date.strftime("%m")
            basedate = datetime.datetime.strptime("2000.{0}.01".format(month), "%Y.%m.%d")
            dayofyear = basedate.timetuple().tm_yday

            _input_pattern = '^(?P<product>MOD\d{2}C\d{1}).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3}).(?P<code>.*).(?P<subset>hdf_\d{2})(?P<extension>\.tif$)'
            _avg_output_pattern = "'{product}.A{year}{dayofyear}.{version}.{code}.avg{extension}'"
            if country == 'IDN':
                _boundary_file = "{0}/01_Data/02_IDN/ShapeFiles/Boundaries/Subset/MODIS/idn_phy_modis_lst_005_grid_diss_a.shp".format(
                    _defaults['base_product_dir'])
                _output_pattern = 'idn_cli_{product}.{year}{dayofyear}.{version}{extension}'
                _LST_max_file = '{0}/01_Data/02_IDN/Rasters/Climate/Temperature/MODIS/MOD11C3/Statistics_byMonth' \
                        '/{1}'.format(_defaults['base_product_dir'], (_defaults['lst_max_file'][country]).format(month))
                _LST_min_file = '{0}/01_Data/02_IDN/Rasters/Climate/Temperature/MODIS/MOD11C3/Statistics_byMonth' \
                        '/{1}'.format(_defaults['base_product_dir'], (_defaults['lst_min_file'][country]).format(month))
                _TCI_file = '{0}/MODIS/MOD11C3/Processed/IDN/LST/{1}' \
                    .format(_defaults['base_data_dir'], (_defaults['tci_file'][country]) \
                                                        .format(year, str(dayofyear).zfill(3)))
            else:

                _boundary_file = "{0}/01_Data/03_Regional/{1}/ShapeFiles/Boundaries/Subset/MODIS/{2}_phy_modis_lst_005_grid_diss_a.shp".format(
                    _defaults['base_product_dir'], country, country.lower())
                _output_pattern = "'{0}".format(country.lower()) + "_cli_{product}.{year}.{month}.{day}.{version}{extension}'"
                _LST_max_file = '{0}/01_Data/03_Regional/{1}/Rasters/Climate/Temperature/MODIS/MOD11C3/Statistics_byMonth' \
                        '/{2}_cli_MOD11C3.2000.2014.{3}.14yrs.max.tif'.format(_defaults['base_product_dir'], country,
                                                                              country.lower(), month)
                _LST_min_file = '{0}/01_Data/03_Regional/{1}/Rasters/Climate/Temperature/MODIS/MOD11C3/Statistics_byMonth' \
                        '/{2}_cli_MOD11C3.2000.2014.{3}.14yrs.min.tif'.format(_defaults['base_product_dir'], country,
                                                                              country.lower(), month)
                _TCI_file = '{0}/MODIS/MOD11C3/Processed/{1}/LST/{2}_cli_MOD11C3.{3}{4}' \
                        '.005.tif'.format(_defaults['base_data_dir'], country, country.lower(), year, str(dayofyear).zfill(3))
            file_pattern = '^(?P<product>MOD\d{2}C\d{1}).(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3}).(?P<average>avg)(?P<extension>\.tif$)'
            file_string = """
## Processing chain begin - Compute Temperature Condition Index
    # download MODIS temperature data (MOD11C3.005)
    - process: MODIS
      type: download
      output_dir: {data_dir}/MODIS/MOD11C3/HDF_MOD
      product: MOD11C3.005
      dates: [{year}-{month}]

    - process: MODIS
      type: extract
      layer: LST_Day
      input_dir: {data_dir}/MODIS/MOD11C3/HDF_MOD/{year}.{month}.01
      output_dir: {data_dir}/MODIS/MOD11C3/Processed/Day

    - process: MODIS
      type: extract
      layer: LST_Night
      input_dir: {data_dir}/MODIS/MOD11C3/HDF_MOD/{year}.{month}.01
      output_dir: {data_dir}/MODIS/MOD11C3/Processed/Night

    - process: MODIS
      type: temp_average
      directory_day: {data_dir}/MODIS/MOD11C3/Processed/Day
      directory_night: {data_dir}/MODIS/MOD11C3/Processed/Night
      directory_output: {data_dir}/MODIS/MOD11C3/Processed/Average
      input_pattern: {input_pattern}
      output_pattern: {avg_pattern}

    - process: Raster
      type: crop
      file_pattern: {file_pattern}
      output_pattern: {country_output_pattern}
      input_dir: {data_dir}/MODIS/MOD11C3/Processed/Average
      output_dir: {data_dir}/MODIS/MOD11C3/Processed/{country}/LST
      boundary_file: {boundary}

    - process: Analysis
      type: TCI
      current_file: {tci_file}
      LST_max_file: {lst_max}
      LST_min_file: {lst_min}
      output_file: {product_dir}/05_Analysis/03_Early_Warning/Temperature_Condition_Index/{country_l}_cli_MOD11C3.{year}.{month}.tci.tif
## Processing chain end - Compute Temperature Condition Index
""".format(data_dir=_defaults['base_data_dir'], year=year, month=month, input_pattern=_input_pattern,
           avg_pattern=_avg_output_pattern, country=country, country_output_pattern=_output_pattern,
           boundary=_boundary_file, tci_file=_TCI_file, lst_max=_LST_max_file, lst_min=_LST_min_file, country_l=country.lower(),
           product_dir=_defaults['base_product_dir'], file_pattern=file_pattern)

            pfile.write(file_string)
            pfile.close()

    return pfile.name

def generateVHIConfig(country, interval, start_date, output):
    try:
        pfile = open(output, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output
        # Not a permission error.
        raise
    else:
        with pfile:
            year = start_date.strftime("%Y")
            month = start_date.strftime("%m")
            basedate = datetime.datetime.strptime("2000.{0}.01".format(month), "%Y.%m.%d")
            dayofyear = basedate.timetuple().tm_yday
            _TCI_file = '{0}/05_Analysis/03_Early_Warning/Temperature_Condition_Index/{1}_cli_MOD11C3.{2}.{3}' \
                    '.tci.tif'.format(_defaults['base_product_dir'], country.lower(), year, month)
            _VCI_file = '{product_dir}/05_Analysis/03_Early_Warning/Vegetation_Condition_Index' \
                '/{country_l}_phy_MOD13A3.{year}.{month}.1_km_monthly_EVI_VCI.tif'.format\
                (product_dir=_defaults['base_product_dir'],
                 country_l=country.lower(),
                 year=year, month=month)

            file_string = """
## Processing chain begin - Compute Vegetation Health Index
    - process: Analysis
      type: VHI
      VCI_file: {vci_file}
      TCI_file: {tci_file}
      output_file: {product_dir}/05_Analysis/03_Early_Warning/Vegetation_Health_Index/{country_l}_cli_MOD11C3.{year}.{month}.1_km_monthly_EVI_LST_VHI.tif
## Processing chain end - Compute Vegetation Health Index
""".format(year=year, month=month, country=country, tci_file=_TCI_file,
           vci_file=_VCI_file, country_l=country.lower(),
           product_dir=_defaults['base_product_dir'])

            pfile.write(file_string)
            pfile.close()

    return pfile.name



def generateConfig(country, product, interval, start_date, output):
    generateHeaderDirectory(output)
    if product == "rainfall_anomaly":
        generateHeaderCHIRPS(output)
        generateHeaderRun(output)
        generateRainfallAnomalyConfig(country, interval, start_date, output)
    elif product == "vhi":
        generateHeaderRun(output)
        generateVCIConfig(country, interval, start_date, output)
        generateTCIConfig(country, interval, start_date, output)
        generateVHIConfig(country, interval, start_date, output)
    elif product == "rainfall_longterm_average":
        generateHeaderCHIRPS(output)
        generateHeaderRun(output)
        generateRainfallLongTermAverageConfig(country, interval, start_date, output)
    return 0

if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        parser.add_option('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option('-c', '--country', dest='country', action='store', help='country id')
        parser.add_option('-p', '--product', dest='product', action='store', help='product')
        parser.add_option('-o', '--output', dest='output', action='store', help='output filename')
        parser.add_option('-i', '--interval', dest='interval', action='store', help='interval')
        parser.add_option('-d', '--start_date', dest='start_date', action='store', help='start year-month')
        (options, args) = parser.parse_args()
        #if len(args) < 1:
        #    parser.error ('missing argument')
        if options.verbose: print time.asctime()
        _country = None
        if options.country:
            _country = options.country
            print 'country=', _country
        _product = None
        if options.product:
            _product = options.product
            print 'product=', _product
        _output = None
        if options.output:
            _output = options.output
            print 'output=', _output
        _interval = None
        if options.interval:
            _interval = options.interval
            print 'interval=', _interval
        _start_date = None
        if options.start_date:
            _start_date = datetime.datetime.strptime(options.start_date, "%Y-%m")
            print 'start_date=', _start_date
        generateConfig(_country, _product, _interval, _start_date, _output)
        if options.verbose: print time.asctime()
        if options.verbose: print 'TOTAL TIME IN MINUTES:',
        if options.verbose: print (time.time() - start_time) / 60.0
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)
