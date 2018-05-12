import ogr, gdal, osr
import math

def RasterizeSHP(SHP, field, pxSize):
    drvMemR = gdal.GetDriverByName('MEM')
    drvMemV = ogr.GetDriverByName('Memory')
    # Check if SHP is a string or a memory object, if string, then
    if isinstance(SHP, str):
        SHP = drvMemV.CopyDataSource(ogr.Open(SHP), '')
    else:
        SHP = SHP
    # Get extent of shapefile and create GeoTransform for temporary raster
    LYR = SHP.GetLayer()
    x_min, x_max, y_min, y_max = LYR.GetExtent()
    x_res = int(math.ceil((x_max - x_min) / float(pxSize)))
    y_res = int(math.ceil((y_max - y_min) / float(pxSize)))
    # Important: to put the first point a little bit towards the center in x-direction, so that we don't get the black line of 0-pixels in the middle
    x_minGT = x_min - pxSize/2
    out_gt = ((x_minGT, pxSize, 0, y_max, 0, -pxSize))
    # Create output-projection
    LYR_pr = LYR.GetSpatialRef()
    out_PR = osr.SpatialReference()
    out_PR.ImportFromWkt(LYR_pr)
    # Create raster in memory
    raster = drvMemR.Create('', x_res, y_res, gdal.GDT_Byte)
    raster.SetGeoTransform(out_gt)
    raster.SetProjection(out_PR)

    rb = raster.GetRasterBand(1)
    rb.SetNoDataValue(99)
    attribute = "'ATTRIBUTE=" + field + "'"
    gdal.RasterizeLayer(raster, [1], LYR, options=[attribute])
    return raster