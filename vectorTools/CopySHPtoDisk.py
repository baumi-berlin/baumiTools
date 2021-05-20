from osgeo import ogr

def CopySHPDisk(shape, outpath):
    drvV = ogr.GetDriverByName('ESRI Shapefile')
    outSHP = drvV.CreateDataSource(outpath)
    lyr = shape.GetLayer()
    sett90LYR = outSHP.CopyLayer(lyr, 'lyr')
    del lyr, shape, sett90LYR, outSHP