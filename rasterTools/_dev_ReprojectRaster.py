import gdal, osr

def ReprojectRaster(inRaster, refProj):
    drvMemR = gdal.GetDriverByName('MEM')
# (1) Build the coordinate transformation for the geotransform
    inPR = osr.SpatialReference()
    inPR.ImportFromWkt(inRaster.GetProjection())
    outPR = osr.SpatialReference()
    outPR.ImportFromWkt(refProj)
    transform = osr.CoordinateTransformation(inPR, outPR)
# (2) Build the output Geotransform, pixelsize and imagesize
    inGT = inRaster.GetGeoTransform()
    cols = inRaster.RasterXSize
    rows = inRaster.RasterYSize
    ulx, uly, ulz = transform.TransformPoint(inGT[0], inGT[3])
    lrx, lry, lrz = transform.TransformPoint(inGT[0] + inGT[1] * cols, inGT[3] + inGT[5] * rows)
    pxSize = int(lrx - ulx) / cols
    newcols = int((lrx - ulx)/ pxSize)
    newrows = int((uly - lry)/ pxSize)
    outGT = (ulx, pxSize, inGT[2], uly, inGT[4], -pxSize)
# (3) Create the new file and reproject
    dtype = inRaster.GetRasterBand(1).DataType
    outfile = drvMemR.Create('', newcols, newrows, 1, dtype)
    outfile.SetProjection(refProj)
    outfile.SetGeoTransform(outGT)
    res = gdal.ReprojectImage(inRaster, outfile, inPR.ExportToWkt(), refProj, gdal.GRA_NearestNeighbour)
    return outfile