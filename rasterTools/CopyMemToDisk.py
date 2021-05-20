from osgeo import gdal#import gdal

def CopyMEMtoDisk(memRas, outpath):
    endList = [[".tif", 'GTiff'], [".bsq", "ENVI"], [".img", "HFA"]]
    for end in endList:
        if outpath.endswith(end[0]):
            ending = end[1]
    drvR = gdal.GetDriverByName(ending)
    drvR.CreateCopy(outpath, memRas)
    memRas = None
    outpath = None
    # To add --> find the highest rastervalue and subsequently find optimal format (bit, byte, float)