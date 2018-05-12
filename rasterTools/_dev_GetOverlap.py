import gdal

def GetMinimumRasterExtent(FilePathList):
    import gdal
    # Function to get the minimum raster extent for rasters that are in THE SAME COORDINATE SYSTEM
    def GetExtent(gt, cols, rows):
    # Get extent from gt und cols,rows.
    # found at http://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
    # Format is: [[UpperLeft],[LowerLeft],[LowerRight],[UpperRight]]
        ext=[]
        xarr=[0,cols]
        yarr=[0,rows]
        for px in xarr:
            for py in yarr:
                x=gt[0]+(px*gt[1])+(py*gt[2])
                y=gt[3]+(px*gt[4])+(py*gt[5])
                ext.append([x,y])
            yarr.reverse()
        return ext
    # Loop through rasters, get extent of each
    # Then find minimum extent
    # Prepare list of extents
    ext_list = []
    for file in FilePathList:
        ds = gdal.Open(file)
        gt = ds.GetGeoTransform()
        cols = ds.RasterXSize
        rows = ds.RasterYSize
        ext = GetExtent(gt, cols, rows)
        ext_list.append(ext)
    # Determine
    UL = [max([x[0][0] for x in ext_list]),min([x[0][1] for x in ext_list])]
    LL = [max([x[1][0] for x in ext_list]),max([x[1][1] for x in ext_list])]
    LR = [min([x[2][0] for x in ext_list]),max([x[2][1] for x in ext_list])]
    UR = [min([x[3][0] for x in ext_list]),min([x[3][1] for x in ext_list])]
    # Create return array
    corners = [UL, LL, LR, UR]
    return corners
