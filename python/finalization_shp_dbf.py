# sample input = python finalization_shp_dbf.py /var/lib/opengeo/geoserver/data/IDN_GIS/05_Analysis/03_Early_Warning/Rainfall_Anomaly_test/ 2016-07

import shapefile
import sys
import datetime
import dbf

location_geoserver = str(sys.argv[1])
filename = location_geoserver.split('/')[-2]
period = str(sys.argv[2])
period_join = period.replace('-','')
period_year = period.split('-')[0]
period_month = period.split('-')[1]


fileshp = location_geoserver + filename + '.shp'
fileshx = location_geoserver + filename + '.shx'
filedbf = location_geoserver + filename + '.dbf'
filetif = 'idn_cli_chirps-%s.ratio_anom.tif' % period_join

table = dbf.Table(filedbf)

print fileshp, filedbf, filetif

def update_shp():
	try:
		r = shapefile.Reader(fileshp)
		w = shapefile.Writer(r.shapeType)

		w.fields = list(r.fields)
		w.records.extend(r.records())
		w._shapes.extend(r.shapes())

		w.poly(parts=[[[94.95000405604239, -11.050000982838242], [94.95000405604239, 5.949999016941131], [141.1500040554428, 5.949999016941131], [141.1500040554428, -11.050000982838242], [94.95000405604239, -11.050000982838242]]])

		w.saveShp(fileshp)
		w.saveShx(fileshx)
		print 'Successed update shp and shx'
	
	except:
		print 'Failed update shp'

def update_dbf():
	try:
		with table:
			datum = (filetif, datetime.date(int(period_year), int(period_month), 1))
			table.append(datum)
		print 'Successed update dbf'
	
	except:
		print 'Failed update dbf'

def main():
	update_shp()
	update_dbf()

if __name__ == '__main__':
	main()

