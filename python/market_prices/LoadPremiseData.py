__author__ = 'rochelle'
#!/usr/bin/env python

import csv
import arcpy
import logging
import os

logger = logging.getLogger('LoadPremiseData')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

arcpy.env.workspace = r"Database Connections\vampire_vampire_gdb_localhost.sde"

def utilRemoveAllRows(dbName, logger = None):
    try:
        with arcpy.da.UpdateCursor(dbName, "OBJECTID") as cursor:
            for row in cursor:
                cursor.deleteRow()
    except Exception as err:
        logger.debug('Unable to delete row - %s', err.message)

def findMarketID(dbName, market, logger = None):
    m_id = -1
    sql_query = "\"market\" = '{0}'".format(market)
    try:
        with arcpy.da.SearchCursor(dbName, ("objectid"), sql_query) as cursor:
            for row in cursor:
                m_id = row[0]
    except:
        if logger:
            logger.debug('Unable to find market %s', market)

    return m_id

def ingestDataFromFile(filename, locationsDB, pricesDB, logger = None):
    f = open(filename, 'r')
    csvReader = csv.reader(f)
    header = csvReader.next()
    marketIdx = header.index("market")
    productIdx = header.index("product")
    startDateIdx = header.index("start_date")
    endDateIdx = header.index("end_date")
    unitsIdx = header.index("units")
    meanIdx = header.index("mean")
    medianIdx = header.index("median")
    cvIdx = header.index("cv")

    fields = ['market_id', 'market', 'product', 'start_date', 'end_date', 'units', 'mean', 'median', 'cv']
    cursor = arcpy.da.InsertCursor(pricesDB, fields)

    for row in csvReader:
        market = row[marketIdx]
        product = row[productIdx]
        startDate = row[startDateIdx]
        endDate = row[endDateIdx]
        units = row[unitsIdx]
        mean = row[meanIdx]
        median = row[medianIdx]
        cv = row[cvIdx]
        if cv == '':
            cv = 0.0
        # find market id
        marketID = findMarketID(locationsDB, market, logger)
        if marketID != -1:
            # check it doesn't already exist and if not, add to table
            try:
                squery = "\"market_id\" = '{0}' and \"market\" = '{1}' and " \
                         "\"product\" = '{2}' and \"start_date\" = date '{3}' and " \
                         "\"end_date\" = date '{4}'".format(marketID, market, product, startDate, endDate)
#                         "" \
#                         "and \"units\" = '{5}' and \"mean\" " \
#                         " = {6} and \"median\" = '{7}' and \"cv\" = '{8}".format\
#                    (marketID, market, product, startDate, endDate, units, mean, median, cv)
                with arcpy.da.SearchCursor(pricesDB, ("objectid",), squery) as sCursor:
                    for sRow in sCursor:
                        # already exists
                        logger.debug('Duplicate row, ignoring')
                        break
                    else:
                        cursor.insertRow((marketID, market, product, startDate, endDate, units, mean, median, cv))
                        print "Inserted row {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}".format(marketID, market, product, startDate, endDate, units, mean, median, cv)

            except Exception as err:
                if logger:
                    logger.debug('Unable to insert row - %s', err.message)
    del cursor
    del sCursor

def getCSVFileFromURL(url, output_dir, overwrite = False, logger = None):
    import urllib2
    import BaseHTTPServer
    # get file name from end of url
    nfl = url.rsplit('/', 1)[1]
    output_file = os.path.join(output_dir, nfl)
    # see if file exists
    if os.path.exists(output_file) and not overwrite:
        # file exists - overwrite?
        return 0
    if logger:
        logger.debug("url: ", url)
        logger.debug("looking for file: ", nfl)
    else:
        print "url: ", url
        print "looking for file: ", nfl
    # Retrieve the webpage as a string
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if logger:
            logger.debug("Could not retrieve file %s. %s", url, BaseHTTPServer.BaseHTTPRequestHandler.responses[e.code][1])
        else:
            print "could not retrieve file ", url, BaseHTTPServer.BaseHTTPRequestHandler.responses[e.code][1]
        return -1
    except urllib2.URLError as e:
        if logger:
            logger.debug("Could not retrieve file %s. %s", url, e.reason)
        else:
            print "could not retrieve file ", url, e.reason
        return -1
    else:
        open(output_file, 'wb').write(response.read())
        if logger:
            logger.debug("downloaded file ", output_file)
        else:
            print "downloaded file ", output_file
    return 0

def downloadPremiseData(output_dir, to_date = None, from_date = "2016-02-14",
                        base_url = "https://s3.amazonaws.com/premise-dpc-iris/UN_ID/ID_data_drop/", max_tries = 3, logger = None):
    from datetime import date, datetime
    from dateutil.rrule import rrule, WEEKLY
    # data is weekly
    sd = datetime.strptime(from_date, "%Y-%m-%d").date()
    if to_date:
        ed = datetime.strptime(to_date, "%Y-%m-%d").date()
    else:
        ed = date.today()

    for dt in rrule(WEEKLY, dtstart=sd, until=ed):
        url = "{0}NTB_data_{1}_{2}_{3}.csv".format(base_url, dt.year, dt.strftime("%m"),
                                                             dt.strftime("%d"))
        tries = 0
        while getCSVFileFromURL(url, output_dir, logger) == -1 and tries < max_tries:
            print "Trying to access ", url
            tries = tries + 1

        url = "{0}NTT_data_{1}_{2}_{3}.csv".format(base_url, dt.year, dt.strftime("%m"),
                                                             dt.strftime("%d"))
        tries = 0
        while getCSVFileFromURL(url, output_dir, logger) == -1 and tries < max_tries:
            print "Trying to access ", url
            tries = tries + 1
    return 0

market_locations = 'vampire_gdb.vampire.idn_market_locations'
market_prices = 'vampire_gdb.vampire.idn_market_prices'

#utilRemoveAllRows(market_prices, logger)

out_dir = 'T:\\WFP2\\IDN_GIS\\01_Data\\02_IDN\\TabularData\\Market Prices\\Premise\\'
downloadPremiseData(out_dir)

#csv_file = r'T:\WFP2\IDN_GIS\01_Data\02_IDN\TabularData\Market Prices\Premise\NTT_data_2016_01_31.csv'
#ingestDataFromFile(csv_file, market_locations, market_prices, logger)
#csv_file = r'T:\WFP2\IDN_GIS\01_Data\02_IDN\TabularData\Market Prices\Premise\NTT_data_2016_02_07.csv'
#ingestDataFromFile(csv_file, market_locations, market_prices, logger)
##csv_file = r'T:\WFP2\IDN_GIS\01_Data\02_IDN\TabularData\Market Prices\Premise\NTB_data_2016_01_24.csv'
##ingestDataFromFile(csv_file, market_locations, market_prices, logger)
#csv_file = r'T:\WFP2\IDN_GIS\01_Data\02_IDN\TabularData\Market Prices\Premise\NTB_data_2016_01_31.csv'
#ingestDataFromFile(csv_file, market_locations, market_prices, logger)
#csv_file = r'T:\WFP2\IDN_GIS\01_Data\02_IDN\TabularData\Market Prices\Premise\NTB_data_2016_02_07.csv'
#ingestDataFromFile(csv_file, market_locations, market_prices, logger)
