
def RasterizeExtentPolygon(SHPpath, refRaster):
    import ogr, gdal
    drvMemV = ogr.GetDriverByName('Memory')
    drvMemR = gdal.GetDriverByName('MEM')
# Get info from the refRaster
    pr = refRaster.GetProjection()
    gt = refRaster.GetGeoTransform()
    cols = refRaster.RasterXSize
    rows = refRaster.RasterYSize
    #pxSize = int(gt[1])
# Open SHP-file, get extent
    shape = drvMemV.CopyDataSource(ogr.Open(SHPpath), '')
    lyr = shape.GetLayer()
    #x_min, x_max, y_min, y_max = lyr.GetExtent()
    #x_res = int((x_max - x_min) / pxSize)
    #y_res = int((y_max - y_min) / pxSize)
# Create raster-file, then rasterize the layer
    shpRas = drvMemR.Create('', cols, rows, gdal.GDT_Byte)
    shpRas.SetProjection(pr)
    shpRas.SetGeoTransform(gt)
    shpRas_rb = shpRas.GetRasterBand(1)
    shpRas_rb.SetNoDataValue(255)
# Rasterize layer, then retun rasterfile
    gdal.RasterizeLayer(shpRas, [1], lyr, burn_values=[1])
    return shpRas