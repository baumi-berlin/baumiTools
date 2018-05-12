import gdal

def GetCorners(path):
    ''' Function that calculate the xy-coordinates of the extenet of a raster file

    Parameters
    -----------
    path : string (required)
        path to the raster-file

    Returns
    --------
    minx, miny, maxx, maxy : numeric
        min/max x/y coordinates of the extent of the image in the input projection

    '''
    ds = gdal.Open(path)
    gt = ds.GetGeoTransform()
    width = ds.RasterXSize
    height = ds.RasterYSize
    minx = gt[0]
    miny = gt[3] + width * gt[4] + height * gt[5]
    maxx = gt[0] + width * gt[1] + height * gt[2]
    maxy = gt[3]
    return minx, miny, maxx, maxy