
# @staticmethod
# def ReprojectShape(inShape, outProj, outname):
#     drvV = ogr.GetDriverByName('ESRI Shapefile')
#     # Open the layer of the input shapefile
#     shp = drvMemV.CopyDataSource(ogr.Open(inShape), '')
#     lyr = shp.GetLayer()
#     # Build the coordinate Transformation
#     inPR = lyr.GetSpatialRef()
#     outPR = osr.SpatialReference()
#     outPR.ImportFromWkt(outProj)
#     transform = osr.CoordinateTransformation(inPR, outPR)
#     # Create the output-SHP and LYR, get geometry type first
#     feat = lyr.GetNextFeature()
#     geom = feat.GetGeometryRef()
#     geomType = geom.GetGeometryType()
#     lyr.ResetReading()
#     outSHP = drvV.CreateDataSource(outname)
#     outLYR = outSHP.CreateLayer('outSHP', outPR, geom_type=geomType)
#     # Create all fields in the new shp-file that we created before
#     inLayerDefn = lyr.GetLayerDefn()
#     for i in range(0, inLayerDefn.GetFieldCount()):
#         fieldDefn = inLayerDefn.GetFieldDefn(i)
#         outLYR.CreateField(fieldDefn)
#         # get the output layer's feature definition
#     outLYRDefn = outLYR.GetLayerDefn()
#     # Now loop through the features from the inSHP, transform geometries, add to new SHP and also take the values in the attributes
#     feat = lyr.GetNextFeature()
#     while feat:
#         geom = feat.GetGeometryRef()
#         geom.Transform(transform)
#         outFeat = ogr.Feature(outLYRDefn)
#         outFeat.SetGeometry(geom)
#         for i in range(0, outLYRDefn.GetFieldCount()):
#             outFeat.SetField(outLYRDefn.GetFieldDefn(i).GetNameRef(), feat.GetField(i))
#         outLYR.CreateFeature(outFeat)
#         # Destroy/Close the features and get next input-feature
#         outFeat.Destroy()
#         feat.Destroy()
#         feat = lyr.GetNextFeature()
#         # Close the shapefiles, return the output shapefile
#     shp.Destroy()
#     outSHP.Destroy()
#     return outSHP

# @staticmethod
# def ReprojectSHP(shape, CSto):
#     from osgeo import ogr, osr
#     import os
#
#     driver = ogr.GetDriverByName('ESRI Shapefile')
#
#     # input SpatialReference
#     inSpatialRef = osr.SpatialReference()
#     inSpatialRef.ImportFromEPSG(2927)
#
#     # output SpatialReference
#     outSpatialRef = osr.SpatialReference()
#     outSpatialRef.ImportFromEPSG(4326)
#
#     # create the CoordinateTransformation
#     coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
#
#     # get the input layer
#     inDataSet = driver.Open(r'c:\data\spatial\basemap.shp')
#     inLayer = inDataSet.GetLayer()
#
#     # create the output layer
#     outputShapefile = r'c:\data\spatial\basemap_4326.shp'
#     if os.path.exists(outputShapefile):
#         driver.DeleteDataSource(outputShapefile)
#     outDataSet = driver.CreateDataSource(outputShapefile)
#     outLayer = outDataSet.CreateLayer("basemap_4326", geom_type=ogr.wkbMultiPolygon)
#
#     # add fields
#     inLayerDefn = inLayer.GetLayerDefn()
#     for i in range(0, inLayerDefn.GetFieldCount()):
#         fieldDefn = inLayerDefn.GetFieldDefn(i)
#         outLayer.CreateField(fieldDefn)
#
#     # get the output layer's feature definition
#     outLayerDefn = outLayer.GetLayerDefn()
#
#     # loop through the input features
#     inFeature = inLayer.GetNextFeature()
#     while inFeature:
#         # get the input geometry
#         geom = inFeature.GetGeometryRef()
#         # reproject the geometry
#         geom.Transform(coordTrans)
#         # create a new feature
#         outFeature = ogr.Feature(outLayerDefn)
#         # set the geometry and attribute
#         outFeature.SetGeometry(geom)
#         for i in range(0, outLayerDefn.GetFieldCount()):
#             outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
#         # add the feature to the shapefile
#         outLayer.CreateFeature(outFeature)
#         # dereference the features and get the next input feature
#         outFeature = None
#         inFeature = inLayer.GetNextFeature()
#
#     # Save and close the shapefiles
#     inDataSet = None
#     outDataSet = None