

def CopyToMem(path):
    import ogr
    drvMemV = ogr.GetDriverByName('Memory')
    f_open = drvMemV.CopyDataSource(ogr.Open(path),'')
    return f_open


def CS_Transform(LYRfrom, LYRto):
    import osr
    outPR = LYRto.GetSpatialRef()
    inPR = LYRfrom.GetSpatialRef()
    transform = osr.CoordinateTransformation(inPR, outPR)
    return transform


def CopySHPDisk(shape, outpath):
    import ogr
    drvV = ogr.GetDriverByName('ESRI Shapefile')
    outSHP = drvV.CreateDataSource(outpath)
    lyr = shape.GetLayer()
    sett90LYR = outSHP.CopyLayer(lyr, 'lyr')
    del lyr, shape, sett90LYR, outSHP


def ClipSHPbySHP(inSHP, clipSHP):
    import osr, ogr
    drvMemV = ogr.GetDriverByName('Memory')
    # Check if "SHP" is a string/path or an object. If string, then copy to memory
    if isinstance(inSHP, str):
        inSHP = drvMemV.CopyDataSource(ogr.Open(inSHP), '')
    else:
        inSHP = inSHP
    if isinstance(clipSHP, str):
        clipSHP = drvMemV.CopyDataSource(ogr.Open(clipSHP), '')
    else:
        inSHP = clipSHP
# Get the layers of the shapefiles
    inLYR = inSHP.GetLayer()
    clipLYR = clipSHP.GetLayer()
# Build a coordinate transformation
    clipPR = clipLYR.GetSpatialRef()
    inPR = inLYR.GetSpatialRef()
    transform = osr.CoordinateTransformation(clipPR, inPR)
# Create an output shapefile --> same properties as the inSHP
    feat = inLYR.GetNextFeature()
    geom = feat.GetGeometryRef()
    geomType = geom.GetGeometryType()
    inLYR.ResetReading()
    outSHP = drvMemV.CreateDataSource('')
    outLYR = outSHP.CreateLayer('outSHP', inPR, geom_type=geomType)
    # Create all fields in the new shp-file that we created before
    inLayerDefn = outLYR.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLYR.CreateField(fieldDefn)
    outLYRDefn = outLYR.GetLayerDefn()
# Now loop through each feature in the clipSHP to clip the geometries in the inSHP, write them into the new shapefile
    clipFeat = clipLYR.GetNextFeature()
    while clipFeat:
        clipGeom = clipFeat.GetGeometryRef()
        clipGeom.Transform(transform)
    # Set extent in inLYR to the clipFeat, so that we exclude polygons a priori that won't intersect anyways
        inLYR.SetSpatialFilter(clipGeom)
    # Loop through the features of the inLYR, build difference of the two
        inFeat = inLYR.GetNextFeature()
        while inFeat:
            inGeom = inFeat.GetGeometryRef()
            print(inFeat.GetField("OGC_FID"))
            intersection = inGeom.Intersection(clipGeom)
    # Convert intersection into new geometry, write to output
            outFeat = ogr.Feature(outLYRDefn)
            outFeat.SetGeometry(intersection)
            for i in range(0, outLYRDefn.GetFieldCount()):
                outFeat.SetField(outLYRDefn.GetFieldDefn(i).GetNameRef(), feat.GetField(i))
            outLYR.CreateFeature(outFeat)
    # Switch to next feature
            inFeat = inLYR.GetNextFeature()
    # Reset reading from the inLYR, then take next feature in clipSHP
        inLYR.ResetReading()
        clipFeat = clipLYR.GetNextFeature()
# Write output shapefile
    return outSHP


def AddFieldToSHP(shape, name, type):
    import ogr, osr
    drvMemV = ogr.GetDriverByName('Memory')
    # Check if "SHP" is a string/path or an object. If string, then copy to memory
    if isinstance(shape, str):
        shape = drvMemV.CopyDataSource(ogr.Open(shape), '')
    else:
        shape = shape
    # Shape = input-shapefile, name = name of the field, type = type of the field
    # types --> Integer=OFTInteger, Float=OFTReal, String=OFTString
    lyr = shape.GetLayer()
    # Check if field already exists, if exists throw out warning
    ldef = lyr.GetLayerDefn()
    if ldef.GetFieldIndex(name) != -1:
        print("--> Warning: Fieldname " + name + " already exists. Skipping...")
    else:
        if type == "float":
            fieldDef = ogr.FieldDefn(name, ogr.OFTReal)
        if type == "int":
            fieldDef = ogr.FieldDefn(name, ogr.OFTInteger)
        if type == "string":
            fieldDef = ogr.FieldDefn(name, ogr.OFTString)
        lyr.CreateField(fieldDef)
    return shape

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