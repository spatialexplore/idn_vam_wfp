__author__ = 'rochelle'
#!/usr/bin/env python

import csv
import arcpy
import logging

logger = logging.getLogger('LoadSurveyData')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

arcpy.env.workspace = r"Database Connections\vampire_vampire_gdb_localhost.sde"

def utilRemoveAllRows(dbName, logger = None):
    try:
        with arcpy.da.UpdateCursor(dbName, "OBJECTID") as cursor:
            for row in cursor:
                cursor.deleteRow()
    except Exception as err:
        logger.debug('Unable to delete row - %s', err.message)

def findDistrictID(dbName, district, logger = None):
    m_id = -1
    sql_query = "\"districtfname\" = '{0}'".format(district)
    try:
        with arcpy.da.SearchCursor(dbName, ("objectid"), sql_query) as cursor:
            for row in cursor:
                m_id = row[0]
    except:
        if logger:
            logger.debug('Unable to find district %s', district)

    return m_id

def ingestDataFromFile(filename, locationsDB, surveyDB, timestamp, logger = None):
    f = open(filename, 'rU')
    csvReader = csv.reader(f)
    header = csvReader.next()
    districtIdx = header.index("district")
    fcsIdx = header.index("fcs")
    fcgPoorIdx = header.index("fcg_poor")
    fcgBorderlineIdx = header.index("fcg_borderline")
    fcgAcceptableIdx = header.index("fcg_acceptable")
    dcStaplesIdx = header.index("days_consume_staples")
    dcPulsesIdx = header.index("days_consume_pulses")
    dcDairyIdx = header.index("days_consume_dairy")
    dcMeatIdx = header.index("days_consume_meat")
    dcVegesIdx = header.index("days_consume_vegetables")
    dcFruitIdx = header.index("days_consume_fruits")
    dcSugarIdx = header.index("days_consume_sugar")
    dcOilsAndFatIdx = header.index("days_consume_oilsandfat")

    fields = ['district_id', 'district', 'fcs', 'fcg_poor', 'fcg_borderline', 'fcg_acceptable', 'days_consume_staples',
              'days_consume_pulses', 'days_consume_dairy', 'days_consume_meat', 'days_consume_vegetables',
              'days_consume_fruits', 'days_consume_sugar', 'days_consume_oilsandfat', 'timestamp']
    cursor = arcpy.da.InsertCursor(surveyDB, fields)

    for row in csvReader:
        if row:
            district = row[districtIdx].upper()
            fcs = row[fcsIdx]
            fcgPoor = row[fcgPoorIdx]
            fcgBorderline = row[fcgBorderlineIdx]
            fcgAcceptable = row[fcgAcceptableIdx]
            dcStaples = row[dcStaplesIdx]
            dcPulses = row[dcPulsesIdx]
            dcDairy = row[dcDairyIdx]
            dcMeat = row[dcMeatIdx]
            dcVeges = row[dcVegesIdx]
            dcFruit = row[dcFruitIdx]
            dcSugar = row[dcSugarIdx]
            dcOilsAndFat = row[dcOilsAndFatIdx]

            # find district id
            districtID = findDistrictID(locationsDB, district, logger)
            if districtID != -1:
                # check it doesn't already exist and if not, add to table
                try:
                    squery = "\"district_id\" = '{0}' and \"district\" = '{1}' and " \
                             "\"timestamp\" = date '{2}'".format(districtID, district, timestamp)
                    with arcpy.da.SearchCursor(surveyDB, ("objectid",), squery) as sCursor:
                        for sRow in sCursor:
                            # already exists
                            logger.debug('Duplicate row, ignoring')
                            break
                        else:
                            cursor.insertRow((districtID, district, fcs, fcgPoor, fcgBorderline, fcgAcceptable, dcStaples, dcPulses,
                                              dcDairy, dcMeat, dcVeges, dcFruit, dcSugar, dcOilsAndFat, timestamp))
                            print "Inserted row {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, {10}, {11}, {12}, {13}, {14}"\
                                .format(districtID, district, fcs,
                                        fcgPoor, fcgBorderline,
                                        fcgAcceptable, dcStaples, dcPulses,
                                        dcDairy, dcMeat, dcVeges, dcFruit,
                                        dcSugar, dcOilsAndFat, timestamp)

                except Exception as err:
                    if logger:
                        logger.debug('Unable to insert row - %s', err.message)
    del cursor
    del sCursor

district_locations = 'vampire_gdb.vampire.idn_districts'
survey = 'vampire_gdb.vampire.idn_householdsurvey_2015'

#utilRemoveAllRows(market_prices, logger)

csv_file = r'T:\WFP2\IDN_GIS\01_Data\02_IDN\TabularData\Household Survey\HouseholdSurvey_2015.csv'
ingestDataFromFile(csv_file, district_locations, survey, "2015/12/01", logger)
