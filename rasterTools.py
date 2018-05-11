
def ReclassifyRaster(inRaster, tupel):
    import gdal
    import numpy as np
    from tqdm import tqdm
    # Check if raster is a string or a MEM object, if string then copy to memory first
    drvMemR = gdal.GetDriverByName('MEM')
    if isinstance(inRaster, str):
        inRaster = drvMemR.CreateCopy('', gdal.Open(inRaster))
    else:
        inRaster = inRaster
    # Now load the properties of the raster and create the output image in memory
    cols = inRaster.RasterXSize
    rows = inRaster.RasterYSize
    rb = inRaster.GetRasterBand(1)
    outDtype = rb.DataType
    out = drvMemR.Create('', cols, rows, outDtype)
    out.SetProjection(inRaster.GetProjection())
    out.SetGeoTransform(inRaster.GetGeoTransform())
    # Reclassify based on the tupel
    out_rb = out.GetRasterBand(1)
    for row in tqdm(range(rows)):
        vals = rb.ReadAsArray(0, row, cols, 1)
        dataOut = vals
        for tup in tupel:
            in_val = tup[0]
            out_val = tup[1]
            np.putmask(dataOut, vals == in_val, out_val)
            out_rb.WriteArray(dataOut, 0, row)
    out_ras = None
    return out


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


def BuildPyramids(path, levels):
    # levels is a vector that is multiples of 2 --> e.g., 2, 4, 6, 8, ..., 64
    import os
    if levels == None:
        command = "gdaladdo.exe " + path + " 2 4 8 16 32 64"
        os.system(command)
    else:
        command = "gdaladdo.exe " + path + " "
        for l in levels:
            command = command + l + " "
        os.system(command)


def GetCorners(path):
    import gdal
    ds = gdal.Open(path)
    gt = ds.GetGeoTransform()
    width = ds.RasterXSize
    height = ds.RasterYSize
    minx = gt[0]
    miny = gt[3] + width * gt[4] + height * gt[5]
    maxx = gt[0] + width * gt[1] + height * gt[2]
    maxy = gt[3]
    return minx, miny, maxx, maxy


def CopyMEMtoDisk(memRas, outpath):
    import gdal
    endList = [[".tif", 'GTiff'], [".bsq", "ENVI"], [".img", "HFA"]]
    for end in endList:
        if outpath.endswith(end[0]):
            ending = end[1]
    drvR = gdal.GetDriverByName(ending)
    drvR.CreateCopy(outpath, memRas)
    memRas = None
    outpath = None
    # To add --> find the highest rastervalue and subsequently find optimal format (bit, byte, float)


def ClumpEliminate(rasterPath, neighbors, pxSize):
    import gdal
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


def OpenRasterToMemory(path):
    import gdal
    drvMemR = gdal.GetDriverByName('MEM')
    ds = gdal.Open(path)
    dsMem = drvMemR.CreateCopy('', ds)
    return dsMem


def CompressENVI(ENVIfilePath):
    import gzip, os
# do gzip compression on ENVI-file
# add in the last line of hdr file the line "file compression = 1"
    tmp_path = ENVIfilePath
    tmp_path = tmp_path.replace(".bsq", "_tmp.bsq")
    f_in = open(ENVIfilePath, 'rb')
    f_out = gzip.open(tmp_path, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    # Delete old file
    os.remove(ENVIfilePath)
    # Rename new file, delete tmpfile
    os.rename(tmp_path, ENVIfilePath)
    # Add compression-info to hdr-file
    hdrpath = ENVIfilePath
    hdrpath = hdrpath.replace(".bsq", ".hdr")
    with open(hdrpath, 'a') as file:
        file.write("file compression = 1")


def ClipRasterBySHP(SHP, raster, mask):
    import ogr, gdal, osr
    import numpy as np
    import baumiTools as bt
    drvMemR = gdal.GetDriverByName('MEM')
    drvMemV = ogr.GetDriverByName('Memory')
## DO SOME PRE-THINGS
# Check if "SHP" is a string/path or an object. If string, then copy to memory
    if isinstance(SHP, str):
        SHP = drvMemV.CopyDataSource(ogr.Open(SHP), '')
    else:
        SHP = SHP
# Check if "raster" is a string/path or an object. If string, then copy to memory
    if isinstance(raster, str):
        raster = gdal.Open(raster)
    else:
        raster = raster
## DO THE CLIPPING
# Get the geometry-infos, and raster infos
    lyr = SHP.GetLayer()
    lyr_pr = lyr.GetSpatialRef()
    ras_pr = raster.GetProjection()
    ras_gt = raster.GetGeoTransform()
    pixelSize = ras_gt[1]
    xOrigin = ras_gt[0]
    yOrigin = ras_gt[3]
    rb = raster.GetRasterBand(1)
    dType = rb.DataType
    NoDataValue = rb.GetNoDataValue()
# Get the extent of the SHP-file, apply coordinate transformation and convert into raster-coordinates
    #https://gis.stackexchange.com/questions/65840/subsetting-geotiff-with-python
    target_SR = osr.SpatialReference()
    target_SR.ImportFromWkt(ras_pr)
    transform = osr.CoordinateTransformation(lyr_pr, target_SR)
    ext = lyr.GetExtent() #x_min, x_max, y_min, y_max
# Find largest extent after the coordinate transformation
    ulx, uly, ulz = transform.TransformPoint(ext[0], ext[3])
    llx, lly, llz = transform.TransformPoint(ext[0], ext[2])
    urx, ury, ulz = transform.TransformPoint(ext[1], ext[3])
    lrx, lry, llz = transform.TransformPoint(ext[1], ext[2])
    minX = min(ulx, llx, urx, lrx)
    maxY = max(uly, ury, lly, lry)
    maxX = max(urx, lrx, ulx, llx)
    minY = min(uly, lly, ury, lry)
# Calculate the new number of columns and rows
    i1 = int((minX - xOrigin) / pixelSize)
    j1 = int((yOrigin - maxY) / pixelSize)
    i2 = int((maxX - xOrigin) / pixelSize)
    j2 = int((yOrigin - minY) / pixelSize)
    colsNew = i2-i1
    rowsNew = j2-j1
    newX = xOrigin + i1*pixelSize
    newY = yOrigin - j1*pixelSize
# Read the raster into an array based on the raster coordinates, then create output-file in memory
    array = rb.ReadAsArray(i1, j1, colsNew, rowsNew)
# If mask = TRUE, then additionally mask the areas outside the polygon
    if mask == True:
# Re-project layer into CS of the raster
        # Create TMP shapefile in memory
        feat = lyr.GetNextFeature()
        geom = feat.GetGeometryRef()
        geomType = geom.GetGeometryType()
        lyr.ResetReading()
        tmpSHP = drvMemV.CreateDataSource('')
        tmpLYR = tmpSHP.CreateLayer('tmpSHP', target_SR, geom_type=geomType)
        tmpLYRDefn = tmpLYR.GetLayerDefn()
        # Now move every geometry over to the tempLYR
        inFeat = lyr.GetNextFeature()
        while inFeat:
           inGeom = inFeat.GetGeometryRef()
           inGeom.Transform(transform)
           tmpFeat = ogr.Feature(tmpLYRDefn)
           tmpFeat.SetGeometry(inGeom)
           tmpLYR.CreateFeature(tmpFeat)
           tmpFeat = None
           inFeat = lyr.GetNextFeature()
# Create a array mask from the temporary shapefile
        shpRas = drvMemR.Create('', colsNew, rowsNew, gdal.GDT_Byte)
        shpRas.SetProjection(ras_pr)
        shpRas.SetGeoTransform((newX, pixelSize, ras_gt[2], newY, ras_gt[4], -pixelSize))
        shpRasBand = shpRas.GetRasterBand(1)
        shpRasBand.SetNoDataValue(0)
        gdal.RasterizeLayer(shpRas, [1], tmpLYR, burn_values=[1])
        shpArray = shpRasBand.ReadAsArray()
# Mask the array
        array = np.where((shpArray == 0), 0, array)
    else:
        array = array
    outRas = drvMemR.Create('', colsNew, rowsNew, 1, dType)
    outRas.SetProjection(ras_pr)
    outRas.SetGeoTransform((newX, pixelSize, ras_gt[2], newY, ras_gt[4], -pixelSize))
# write the values into it
    outRas.GetRasterBand(1).WriteArray(array)
    #outRas.GetRasterBand(1).SetNoDataValue(NoDataValue)
    return outRas


def RasterizeSHP(SHP, field, pxSize):
    import ogr, gdal, osr
    import math
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

def GetDataTypeHexaDec(gdalDtype):
    dTypes = [[1, 'b'], [2, 'H'], [3, 'h'], [4, 'I'], [5, 'i'], [6, 'f'], [7, 'd']]
    for dT in dTypes:
        if dT[0] == gdalDtype:
            band_dType = dT[1]
    return band_dType


    # @staticmethod
    # def ReprojectRaster(inRaster, refProj):
    #     import gdal, osr
    #     drvMemR = gdal.GetDriverByName('MEM')
    # # (1) Build the coordinate transformation for the geotransform
    #     inPR = osr.SpatialReference()
    #     inPR.ImportFromWkt(inRaster.GetProjection())
    #     outPR = osr.SpatialReference()
    #     outPR.ImportFromWkt(refProj)
    #     transform = osr.CoordinateTransformation(inPR, outPR)
    # # (2) Build the output Geotransform, pixelsize and imagesize
    #     inGT = inRaster.GetGeoTransform()
    #     cols = inRaster.RasterXSize
    #     rows = inRaster.RasterYSize
    #     ulx, uly, ulz = transform.TransformPoint(inGT[0], inGT[3])
    #     lrx, lry, lrz = transform.TransformPoint(inGT[0] + inGT[1] * cols, inGT[3] + inGT[5] * rows)
    #     pxSize = int(lrx - ulx) / cols
    #     newcols = int((lrx - ulx)/ pxSize)
    #     newrows = int((uly - lry)/ pxSize)
    #     outGT = (ulx, pxSize, inGT[2], uly, inGT[4], -pxSize)
    # # (3) Create the new file and reproject
    #     dtype = inRaster.GetRasterBand(1).DataType
    #     outfile = drvMemR.Create('', newcols, newrows, 1, dtype)
    #     outfile.SetProjection(refProj)
    #     outfile.SetGeoTransform(outGT)
    #     res = gdal.ReprojectImage(inRaster, outfile, inPR.ExportToWkt(), refProj, gdal.GRA_NearestNeighbour)
    #     return outfile

