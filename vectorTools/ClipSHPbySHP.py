import osr, ogr

def ClipSHPbySHP(inSHP, clipSHP):
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
