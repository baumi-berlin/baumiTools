import gdal

def ClumpEliminate(rasterPath, neighbors, pxSize):
    drvMemR = gdal.GetDriverByName('MEM')
    # Output is a raster that is written into memory
    ds = gdal.Open(rasterPath)
    gt = ds.GetGeoTransform()
    pr = ds.GetProjection()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    # Generate output-file --> first in memory
    sieveMem = drvMemR.Create('', cols, rows, 1, gdal.GDT_Byte)
    sieveMem.SetGeoTransform(gt)
    sieveMem.SetProjection(pr)
    # Do the ClumpSieve
    rb_in = ds.GetRasterBand(1)
    rb_out = sieveMem.GetRasterBand(1)
    maskband = None
    prog_func = gdal.TermProgress
    result = gdal.SieveFilter(rb_in, maskband, rb_out, pxSize, neighbors, callback=prog_func)
    return sieveMem