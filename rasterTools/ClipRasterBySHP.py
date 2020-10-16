#import ogr, gdal, osr
from osgeo import ogr, gdal, osr
import numpy as np
import baumiTools as bt

def ClipRasterBySHP(SHP, raster, mask):

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
    lyr_pr.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
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
    target_SR.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
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
    if raster.RasterCount == 1:
        array = raster.GetRasterBand(1).ReadAsArray(i1, j1, colsNew, rowsNew)
    if raster.RasterCount > 1:
        array = np.zeros((rowsNew, colsNew, raster.RasterCount))
        for bandCount, arrCount in enumerate(range(raster.RasterCount), start=1):
            array[:, :, arrCount] = raster.GetRasterBand(bandCount).ReadAsArray(i1, j1, colsNew, rowsNew)

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
        # root_folder = "E:/Baumann/_ANALYSES/AnnualLandCoverChange_CHACO/"
        # classRun = 6
        # out_root = root_folder + "04_Map_Products/Run" + str("{:02d}".format(classRun)) + "/"
        # outname = out_root + "Run" + str("{:02d}".format(classRun)) + "maskkk.tif"
        # bt.baumiRT.CopyMEMtoDisk(shpRas, outname)
        # exit(0)
        shpArray = shpRasBand.ReadAsArray()
    ### Test: in case of multiband do this per band
        if array.ndim == 2:
            array = np.where((shpArray == 0), 0, array)
        if array.ndim > 2:
            import copy
            for index in range(array.shape[2]):
                array_index = array[:, :, index]
                array_index = np.where((shpArray == 0), 0, array_index)
                array[:, :, index] = copy.deepcopy(array_index)
# Mask the array       
    else:
        array = array
        
# Write to disc --> again, check if more than one band
    if array.ndim == 2:
        outRas = drvMemR.Create('', colsNew, rowsNew, 1, dType)
        outRas.SetProjection(ras_pr)
        outRas.SetGeoTransform((newX, pixelSize, ras_gt[2], newY, ras_gt[4], -pixelSize))
        # write the values into it
        outRas.GetRasterBand(1).WriteArray(array)
        #outRas.GetRasterBand(1).SetNoDataValue(NoDataValue)
    if array.ndim > 2:
        outRas = drvMemR.Create('', colsNew, rowsNew, array.shape[2], dType)
        outRas.SetProjection(ras_pr)
        outRas.SetGeoTransform((newX, pixelSize, ras_gt[2], newY, ras_gt[4], -pixelSize))
        # write the values into it
        for bandCount, arrCount in enumerate(range(array.shape[2]), start=1):
            outRas.GetRasterBand(bandCount).WriteArray(array[:, :, arrCount])
        
    return outRas