from osgeo import ogr, osr, gdal
import numpy as np
import math
import baumiTools as bt

def Geom_Raster_to_np(geom, raster):
    '''
    Function that takes a geometry from a polygon shapefile and a rasterfile, and returns both features as 2d-arryas
    in the size of the geom --> can be later used for masking.
    Function does a coordinate transformation implicitely!

    PARAMETERS
    -----------
    geom : geom object (required)
        geometry of the feature
    raster: gdal object (required)
        raster as a gdal-object (through gdal.Open())

    RETURNS
    -------
    Two numpy-arrays
    (1) np-array of the geometry as binary feature --> values inside the geometry have value '1', values outside '0'
    (2) np-array of the raster in the same size (i.e., as a subset of the raster) of the geometry

    '''
    # Make a coordinate transformation of the geom-srs to the raster-srs
    pol_srs = geom.GetSpatialReference()
    #print(pol_srs)
    ras_srs = raster.GetProjection()
    #print(ras_srs)
    #exit(0)
    target_SR = osr.SpatialReference()
    target_SR.ImportFromWkt(ras_srs)
    srs_trans = osr.CoordinateTransformation(pol_srs, target_SR)
    geom.Transform(srs_trans)
    # Create a memory shp/lyr to rasterize in
    geom_shp = ogr.GetDriverByName('Memory').CreateDataSource('')
    geom_lyr = geom_shp.CreateLayer('geom_shp', srs=geom.GetSpatialReference())
    geom_feat = ogr.Feature(geom_lyr.GetLayerDefn())
    geom_feat.SetGeometryDirectly(ogr.Geometry(wkt=str(geom)))
    geom_lyr.CreateFeature(geom_feat)
    # Rasterize the layer, open in numpy
    #bt.baumiVT.CopySHPDisk(geom_shp, "D:/baumamat/Warfare/_Variables/Forest/_tryout.shp")
    x_min, x_max, y_min, y_max = geom.GetEnvelope()
    gt = raster.GetGeoTransform()
    pr = raster.GetProjection()
    x_res = math.ceil((abs(x_max - x_min)) / gt[1])
    y_res = math.ceil((abs(y_max - y_min)) / gt[1])
    new_gt = (x_min, gt[1], 0, y_max, 0, -gt[1])
    lyr_ras = gdal.GetDriverByName('MEM').Create('', x_res, y_res, 1, gdal.GDT_Byte)
    #lyr_ras.GetRasterBand(1).SetNoDataValue(0)
    lyr_ras.SetProjection(pr)
    lyr_ras.SetGeoTransform(new_gt)
    gdal.RasterizeLayer(lyr_ras, [1], geom_lyr, burn_values=[1], options = ['ALL_TOUCHED=TRUE'])
    geom_np = np.array(lyr_ras.GetRasterBand(1).ReadAsArray())
    # Now load the raster into the array --> only take the area that is 1:1 the geom-layer (see Garrard p.195)
    inv_gt = gdal.InvGeoTransform(gt)
    offsets_ul = gdal.ApplyGeoTransform(inv_gt, x_min, y_max)
    off_ul_x, off_ul_y = map(int, offsets_ul)
    raster_np = np.array(raster.GetRasterBand(1).ReadAsArray(off_ul_x, off_ul_y, x_res, y_res))   
    ## Just for checking if the output is correct --> write it to disc. Outcommented here
    #val_ras = gdal.GetDriverByName('MEM').Create('', x_res, y_res, 1, gdal.GDT_UInt16)
    #val_ras.SetProjection(pr)
    #val_ras.SetGeoTransform(new_gt)
    #val_ras.GetRasterBand(1).WriteArray(raster_np, 0, 0)
    #bt.baumiRT.CopyMEMtoDisk(lyr_ras, "E:/Baumann/_ANALYSES/geom.tif")
    #bt.baumiRT.CopyMEMtoDisk(val_ras, "E:/Baumann/_ANALYSES/raster.tif")
    #exit(0)
    return geom_np, raster_np