from osgeo import ogr

def SaveGEOMtoFile(geom, outpath):
    drvV = ogr.GetDriverByName('ESRI Shapefile')
    outSHP = drvV.CreateDataSource(outpath)
    outLYR = outSHP.CreateLayer('outSHP', srs=geom.GetSpatialReference())
    outFEAT = ogr.Feature(outLYR.GetLayerDefn())
    outFEAT.SetGeometryDirectly(ogr.Geometry(wkt=str(geom)))
    outLYR.CreateFeature(outFEAT)
