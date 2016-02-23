__author__ = 'rochelle'

import yaml, os, sys, traceback
import optparse
import time
import logging
import market_prices.GetPremiseData

logger = logging.getLogger('ProcessMarketPriceData')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def configFileError(msg, e):
    logger.debug('Error in config file %s' % msg)
    logger.debug('%s' % str(e))
    return -1

def setupDatabase(process, cfg):
    dbname = ""
    host = ""
    port = ""
    user = ""
    password = ""

    if 'database' in cfg:
        db = cfg['database'][0]
        if 'database' in db:
            dbname = db['database']
        if 'host' in db:
            host = db['host']
        if 'port' in db:
            port = db['port']
        if 'user' in db:
            user = db['user']
        if 'password' in db:
            password = db['password']

    conn = market_prices.GetPremiseData.openDBConnection(dbname, host, port, user, password, logger)
    market_prices.GetPremiseData.setupDatabase(conn)
    conn.close()
    return 0

def getPremiseData(process, cfg):
    url = "http://"
    output_dir = ""
    if 'url' in process:
        url = process['url']
    if 'output_dir' in process:
        output_dir = process['output_dir']
    market_prices.GetPremiseData.getCSVFileFromURL(url, output_dir, logger)
    return 0

def updateMarkets(process, cfg):
    dbname = ""
    host = ""
    port = ""
    user = ""
    password = ""
    filename = ""
    if 'database' in cfg:
        db = cfg['database'][0]
        if 'database' in db:
            dbname = db['database']
        if 'host' in db:
            host = db['host']
        if 'port' in db:
            port = db['port']
        if 'user' in db:
            user = db['user']
        if 'password' in db:
            password = db['password']
    conn = market_prices.GetPremiseData.openDBConnection(dbname, host, port, user, password, logger)
    if 'filename' in process:
        filename = process['filename']
    if conn:
        market_prices.GetPremiseData.updateMarketLocations(conn, filename, logger)
    conn.close()
    return 0


def ingestPremiseData(process, cfg):
    dbname = ""
    host = ""
    port = ""
    user = ""
    password = ""
    filename = ""
    if 'database' in cfg:
        db = cfg['database'][0]
        if 'database' in db:
            dbname = db['database']
        if 'host' in db:
            host = db['host']
        if 'port' in db:
            port = db['port']
        if 'user' in db:
            user = db['user']
        if 'password' in db:
            password = db['password']
    conn = market_prices.GetPremiseData.openDBConnection(dbname, host, port, user, password, logger)
    if 'filename' in process:
        filename = process['filename']
    if conn:
        market_prices.GetPremiseData.ingestDataFromFile(conn, filename)
    conn.close()
    return 0

def main (config):

    global options, args

    if config:
        # parse config file
        with open(config, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
#    if arcPyUtils.useSpatialAnalyst() == -1:
#        os._exit(1)

    processList = cfg['run']
    print processList
    for i,p in enumerate(processList):
        try:
            if p['process'] == 'GET':
                getPremiseData(p, cfg)
            if p['process'] == 'INGEST':
                ingestPremiseData(p, cfg)
            if p['process'] == 'SETUP_DB':
                setupDatabase(p, cfg)
            if p['process'] == 'UPDATE_MARKETS':
                updateMarkets(p, cfg)
        except Exception, e:
            configFileError("running process PUBLISH", e)

if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        parser.add_option ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option ('-c', '--config', dest='config_file', action='store', help='config filename')
        (options, args) = parser.parse_args()
        if options.verbose: print time.asctime()
        config_f = ""
        if options.config_file:
            config_f = options.config_file
            print 'config file=', config_f
        main(config_f)
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
