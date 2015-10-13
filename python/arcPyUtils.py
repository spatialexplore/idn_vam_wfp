__author__ = 'rochelle'
import arcpy

def useSpatialAnalyst():
    # Check out the ArcGIS Spatial Analyst extension license
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        arcpy.AddMessage("Error: Couldn't get Spatial Analyst extenstion")
        return -1
    arcpy.env.overwriteOutput = 1
    return 0