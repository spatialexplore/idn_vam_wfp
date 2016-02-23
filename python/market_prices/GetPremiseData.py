__author__ = 'rochelle'
#!/usr/bin/env python

import urllib2, BaseHTTPServer
import os
import psycopg2
import csv
import arcpy
from psycopg2.extras import DateRange

def dropAllTables(connection):
    cursor = connection.cursor()
#    cursor.execute("select exists(select * from information_schema.tables where table_catalog='Test' AND table_schema = 'public' AND table_name='public.market')")
#    if cursor.fetchone()[0]:
    cursor.execute("DROP TABLE IF EXISTS public.market CASCADE;")
#    cursor.execute("select exists(select * from information_schema.tables where table_catalog='Test' AND table_schema = 'public' AND table_name='public.product')")
#    if cursor.fetchone()[0]:
    cursor.execute("DROP TABLE IF EXISTS public.product CASCADE;")
#    cursor.execute("select exists(select * from information_schema.tables where table_catalog='Test' AND table_schema = 'public' AND table_name='public.timestamp')")
#    if cursor.fetchone()[0]:
    cursor.execute("DROP TABLE IF EXISTS public.timestamp CASCADE;")
#    cursor.execute("select exists(select * from information_schema.tables where table_catalog='Test' AND table_schema = 'public' AND table_name='public.price_index')")
#    if cursor.fetchone()[0]:
    cursor.execute("DROP TABLE IF EXISTS public.price_index CASCADE;")
#    cursor.execute("select exists(select * from information_schema.tables where table_catalog='Test' AND table_schema = 'import' AND table_name='import.weeklydata')")
#    if cursor.fetchone()[0]:
    cursor.execute("DROP TABLE IF EXISTS import.weeklydata;")
    cursor.execute("DROP TABLE IF EXISTS public.time_series CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS public.tstype CASCADE;")

    cursor.close()

def setupDatabase(connection):
    dropAllTables(connection)
    create_market_table(connection)
    create_product_table(connection)
    create_timestamp_table(connection)
    create_prices_table(connection)
    create_weeklydata_table(connection)
    create_tstype_table(connection)
    create_time_series_table(connection)
    # create relationships
    rel = createMarketTSRelationship(connection)

def getCSVFileFromURL(url, output_dir, logger = None):
    # get file name from end of url
    nfl = url.rsplit('/', 1)[1]
    # Retrieve the webpage as a string
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if logger:
            logger.debug("Could not retrieve file %s. %s", url, BaseHTTPServer.BaseHTTPRequestHandler.responses[e.code][1])
    else:
        output_file = os.path.join(output_dir, nfl)
        open(output_file, 'wb').write(response.read())
    return 0

def openDBConnection(dbname = 'test', host= 'localhost', port= 5432, user = 'rochelle',password= 'rochelle', logger = None):
    try:
        conn = psycopg2.connect(dbname = dbname, host= host, port= port, user = user, password= password)
    except psycopg2.Error as e:
        if logger:
            logger ("Unable to connect to the database. %s", e.pgerror)
    else:
        return conn
    return None

def ingestDataFromFile(connection, filename, logger = None):
    f = open(filename, 'r')
    try:
        create_weeklydata_table(connection)
        import_price_data(connection, 'import.weeklydata', f)
    except:
        if logger:
            logger.debug('Unable to ingest price data from %s', filename)

    # process imported data into tables
    process_markets(connection, 'import.weeklydata')
    process_products(connection, 'import.weeklydata')
    process_timestamps(connection, 'import.weeklydata')
    process_prices(connection, 'import.weeklydata')
    process_tstype(connection, 'import.weeklydata')
    process_new_data(connection, 'import.weeklydata')
    return 0

def updateMarketLocations(connection, filename, logger = None):
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            pt = [row[2], row[1]]
            logger.debug("Updating market %s with location (%s,%s)" % (row[0], pt[0], pt[1]))
            update_market_location(connection, row[0], pt)
    return 0

def clear_all(connection):
    cursor = connection.cursor()
    create_market_table(connection)
    create_product_table(connection)
    create_timestamp_table(connection)
    create_prices_table(connection)
    create_tstype_table(connection)
    create_time_series_table(connection)
    cursor.close()

def createMarketTSRelationship(connection):
    origin = "public.market"
    dest = "public.time_series"
    relClass = "market_timeseries_RelClass"
    forLabel = "Has"
    backLabel = "For"
    primaryKey = "market_id"
    foreignKey = "ts_id"
    arcpy.CreateRelationshipClass_management(origin, dest, relClass, "SIMPLE", forLabel,
					     backLabel, "BACKWARD", "ONE_TO_MANY",
					     "NONE", primaryKey, foreignKey)
    return 0

def create_market_table(connection):
    cursor = connection.cursor()
    createMarketTable = "CREATE TABLE public.market(market_id serial NOT NULL, name character varying(30), " \
                        "location point, " \
                        "CONSTRAINT market_pkey PRIMARY KEY (market_id))" \
                        "WITH (OIDS=FALSE);"
#    cursor.execute("DROP TABLE public.market CASCADE;")
    try:
        cursor.execute(createMarketTable)
        cursor.execute("ALTER TABLE public.market OWNER TO rochelle;")
        createGeometry = "SELECT AddGeometryColumn('public', 'market', 'geom', 4326, 'POINT', 2)"
        cursor.execute(createGeometry)
        cursor.execute("CREATE INDEX market_idx ON public.market USING gist (geom)")
    except psycopg2.Error as e:
        print "{0} - {1}".format(e.diag.severity, e.diag.message_primary)
    else:
        connection.commit()
    cursor.close()

def update_market_location(connection, market, point):
    cursor = connection.cursor()
    updateMarketLocation = "UPDATE public.market SET " \
                           "geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326) " \
                           "WHERE name = %s;"
#    updateMarketLocation = "UPDATE public.market SET " \
#                           "geom = ST_GeomFromText('POINT(116.077921 -8.564303)', 4326) " \
#                           "WHERE name = 'kebon roek ampenan mataram';"
    try:
#        cursor.execute(updateMarketLocation)
#        cursor.execute(updateMarketLocation, ('116.077921', '-8.564303', market))
        print (updateMarketLocation % (point[0], point[1], market))
        cursor.execute(updateMarketLocation, (float(point[0]), float(point[1]), market))
    except psycopg2.Error as e:
        print "{0} - {1}".format(e.diag.severity, e.diag.message_primary)
    else:
        connection.commit()
    cursor.close()
    return 0

def create_time_series_table(connection):
    cursor = connection.cursor()
    createTimeSeriesTable = "CREATE TABLE time_series(ts_id serial NOT NULL, tstype_id integer, feature_id integer, " \
                            "start_date_value date NOT NULL, end_date_value date NOT NULL, " \
                            "mean_value numeric(10,3), median_value numeric(10,3), cv_value numeric(8,7), " \
                            "CONSTRAINT time_series_pkey PRIMARY KEY (ts_id), " \
                            "CONSTRAINT time_series_tstype_id_fkey FOREIGN KEY (tstype_id) REFERENCES tstype (tstype_id) MATCH SIMPLE " \
                            "ON UPDATE NO ACTION ON DELETE NO ACTION, " \
                            "CONSTRAINT time_series_feature_id_fkey FOREIGN KEY (feature_id) REFERENCES market (market_id) MATCH SIMPLE " \
                            "ON UPDATE NO ACTION ON DELETE NO ACTION) " \
                            "WITH (OIDS=FALSE);"
    cursor.execute(createTimeSeriesTable)
    cursor.execute("ALTER TABLE time_series OWNER TO rochelle;")
    connection.commit()
    cursor.close()
    return 0

def create_tstype_table(connection):
    cursor = connection.cursor()
    createTSTypeTable = "CREATE TABLE tstype(tstype_id serial NOT NULL, variable character varying(30), " \
                        "units character varying(30), " \
                        "CONSTRAINT tstype_tstype_id_pkey PRIMARY KEY (tstype_id))" \
                        "WITH (OIDS=FALSE);"
    cursor.execute(createTSTypeTable)
    cursor.execute("ALTER TABLE tstype OWNER TO rochelle;")
    connection.commit()
    cursor.close()
    return 0

def create_product_table(connection):
    cursor = connection.cursor()
    createProductTable = "CREATE TABLE product(id serial NOT NULL, name character varying(30)," \
                        "CONSTRAINT product_pkey PRIMARY KEY (id))" \
                        "WITH (OIDS=FALSE);"
#    cursor.execute("DROP TABLE public.product CASCADE;")
    cursor.execute(createProductTable)
    cursor.execute("ALTER TABLE product OWNER TO rochelle;")
    connection.commit()
    cursor.close()

def create_timestamp_table(connection):
    cursor = connection.cursor()
    createTimestampTable = "CREATE TABLE timestamp(id serial NOT NULL, start_date date NOT NULL, end_date date NOT NULL," \
                         "CONSTRAINT timestamp_pkey PRIMARY KEY (id))" \
                         "WITH (OIDS=FALSE);"
#    cursor.execute("DROP TABLE public.timestamp CASCADE;")
    cursor.execute(createTimestampTable)
    cursor.execute("ALTER TABLE timestamp OWNER TO rochelle;")
    connection.commit()
    cursor.close()

def create_prices_table(connection):
    cursor = connection.cursor()
    createPricesTable = "CREATE TABLE price_index(id serial NOT NULL, mean real, median real, cv real," \
                        "timestamp_id integer NOT NULL, product_id integer NOT NULL, market_id integer NOT NULL," \
                        "CONSTRAINT price_index_pkey PRIMARY KEY (id, timestamp_id, product_id, market_id), " \
                        "CONSTRAINT price_index_product_id_fkey FOREIGN KEY (product_id) REFERENCES product (id) MATCH SIMPLE " \
                        "ON UPDATE NO ACTION ON DELETE NO ACTION, " \
                        """CONSTRAINT price_index_timestamp_id_fkey FOREIGN KEY (timestamp_id) REFERENCES "timestamp" (id) MATCH SIMPLE """ \
                        "ON UPDATE NO ACTION ON DELETE NO ACTION) " \
                        "WITH (OIDS=FALSE);"
#    cursor.execute("DROP TABLE public.price_index CASCADE;")
    cursor.execute(createPricesTable)
    cursor.execute("ALTER TABLE price_index OWNER TO rochelle;")
    connection.commit()
    cursor.close()

def create_weeklydata_table(connection):
    cursor = connection.cursor()
    cursor.execute("DROP TABLE IF EXISTS import.weeklydata;")
    cursor.execute("CREATE TABLE import.weeklydata (market text, product text, start_date date, end_date date," \
                "units text, mean real, median real, cv real)" \
                "WITH (OIDS=FALSE);")
    cursor.execute("ALTER TABLE import.weeklydata OWNER TO rochelle;")
    connection.commit()
    cursor.close()

def import_price_data(connection, table_name, file_object):
    sqlStatement = """ COPY %s FROM STDIN WITH CSV HEADER DELIMITER AS ',' """
    cursor = connection.cursor()
    cursor.copy_expert(sql=sqlStatement % table_name, file=file_object)
    connection.commit()
    cursor.close()

def process_markets(connection, table_name):
    cursor = connection.cursor()
    # select unique markets and add to public.market table if they don't already exist
    sqlStatement = "INSERT INTO public.market (name)" \
                   "(SELECT DISTINCT market FROM %s as new_markets WHERE NOT EXISTS(SELECT 1 FROM " \
                   "public.market as old_markets WHERE new_markets.market = old_markets.name));"
    cursor.execute(sqlStatement % table_name)
    connection.commit()
    cursor.close()

def process_tstype(connection, table_name):
    cursor = connection.cursor()
    # select unique tstypes (products) and add to public.tstype table if they don't already exist
    sqlStatement = "INSERT INTO public.tstype (variable, units)" \
                   "(SELECT DISTINCT product, units FROM %s as new_tstypes WHERE NOT EXISTS(SELECT 1 FROM " \
                   "public.tstype as old_tstypes WHERE new_tstypes.product = old_tstypes.variable));"
    cursor.execute(sqlStatement % table_name)
    connection.commit()
    cursor.close()


def process_products(connection, table_name):
    cursor = connection.cursor()
    # select unique products and add to public.product table if they don't already exist
    sqlStatement = "INSERT INTO public.product (name)" \
                   "(SELECT DISTINCT product FROM %s as new_products WHERE NOT EXISTS(SELECT 1 FROM " \
                   "public.product as old_products WHERE new_products.product = old_products.name));"
    cursor.execute(sqlStatement % table_name)
    connection.commit()
    cursor.close()

def process_timestamps(connection, table_name):
    cursor = connection.cursor()
    # select unique products and add to public.product table if they don't already exist
    sqlStatement = "INSERT INTO public.timestamp (start_date, end_date) " \
                   "(SELECT DISTINCT start_date, end_date FROM %s as new_date WHERE NOT EXISTS(SELECT 1 FROM " \
                    "public.timestamp as old_date WHERE new_date.start_date = old_date.start_date AND new_date.end_date = old_date.end_date));"
    cursor.execute(sqlStatement % table_name)

    connection.commit()
    cursor.close()

def process_new_data(connection, table_name):
    cursor = connection.cursor()
    sqlselect = "SELECT market, product, start_date, end_date, mean, median, cv FROM %s as new_data"
    cursor.execute(sqlselect % table_name)
    records = cursor.fetchall()
    row_count = 0
    ts_insert = "INSERT INTO public.time_series (mean_value, median_value, cv_value, feature_id, tstype_id, " \
                "start_date_value, end_date_value) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for row in records:
        row_count += 1
        print "row: %s    %s\n" % (row_count, row)
        # find market and ts_type indices
        cursor.execute("SELECT market_id FROM public.market WHERE public.market.name = %s", (row[0],))
        m = cursor.fetchone()
        cursor.execute("SELECT tstype_id FROM public.tstype WHERE public.tstype.variable = %s", (row[1],))
        t = cursor.fetchone()
        print "market: %s, timestamp: %s\n" % (m[0], t[0])
        #check if already in database
        sqlcheck = "SELECT count(1) FROM public.time_series WHERE public.time_series.feature_id = %s AND " \
                   "public.time_series.tstype_id = %s"
        cursor.execute(sqlcheck, (m[0], t[0]))
        if (cursor.fetchone()[0] == 0):
            #insert price indices
            cursor.execute(ts_insert,(row[4], row[5], row[6], m[0], t[0], row[2], row[3]))

    connection.commit()
    cursor.close()
    return 0

def process_prices(connection, table_name):
    cursor = connection.cursor()
    # add price indices to public.price_index
    sqlselect = "SELECT market, product, start_date, end_date, mean, median, cv FROM %s as new_data"
    cursor.execute(sqlselect % table_name)
    records = cursor.fetchall()
#    row_count = 0
    sqlinsert = "INSERT INTO public.price_index (mean, median, cv, timestamp_id, product_id, market_id) VALUES (%s, %s, %s, %s, %s, %s)"
    for row in records:
#        row_count += 1
#        print "row: %s    %s\n" % (row_count, row)
        # find market, product and timestamp indices
        cursor.execute("SELECT market_id FROM public.market WHERE public.market.name = %s", (row[0],))
        m = cursor.fetchone()
        cursor.execute("SELECT id FROM public.product WHERE public.product.name = %s", (row[1],))
        p = cursor.fetchone()
        cursor.execute("SELECT id FROM public.timestamp WHERE public.timestamp.start_date = %s AND public.timestamp.end_date = %s", (row[2], row[3]))
        t = cursor.fetchone()
#        print "market: %s, product: %s, timestamp: %s\n" % (m[0], p[0], t[0])
        #check if already in database
        sqlcheck = "SELECT count(1) FROM public.price_index WHERE public.price_index.market_id = %s AND " \
                   "public.price_index.product_id = %s AND public.price_index.timestamp_id = %s"
        cursor.execute(sqlcheck, (m[0], p[0], t[0]))
        if (cursor.fetchone()[0] == 0):
            #insert price indices
            cursor.execute(sqlinsert,(row[4], row[5], row[6], t[0], p[0], m[0]))

    connection.commit()
    cursor.close()


# #DB connection properties
# try:
#     conn = psycopg2.connect(dbname = 'test', host= 'localhost', port= 5432, user = 'rochelle',password= 'rochelle')
# except:
#     print ('Unable to connect to the database')
#
# create_weeklydata_table(conn)
# clear_all(conn)
# #create_market_table(conn)
#
# # import weekly price data from csv file
# f = open(r'S:\WFP\PriceMonitoring\data_2015_12_13.csv', 'r')
# #f = open(r'S:\WFP\PriceMonitoring\data_2015_12_20.csv', 'r')
# #f = open(r'S:\WFP\PriceMonitoring\data_2015_12_27.csv', 'r')
# #f = open(r'S:\WFP\PriceMonitoring\data_2016_01_03.csv', 'r')
# try:
#     import_price_data(conn, 'import.weeklydata', f)
# except:
#     print ('Unable to import price indices')
#
# # process imported data into tables
# process_markets(conn, 'import.weeklydata')
# process_products(conn, 'import.weeklydata')
# process_timestamps(conn)
# process_prices(conn, 'import.weeklydata')
#
# conn.close()
