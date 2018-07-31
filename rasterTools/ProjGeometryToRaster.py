import gdal
import osr

def ProjGeometryToRaster(geom, pr):
    ''' Function that build the rule for the coordinate-trnasformation of a geometry to a raster-projection.
        Is often used when doing point-intersections or zonal summaries over rasters

    Parameters
    -----------
    geom : object (required)
        geometry object, retrieve through: feat.GetGeometryRef()
    pr : target projection (required)
        Format is well-known-text. Retreive through. ds.GetProjection()

    Returns
    --------
    coordTrans : object
        transformation rule for the geo-transformation

    '''
    source_SR = geom.GetSpatialReference()
    target_SR = osr.SpatialReference()
    target_SR.ImportFromWkt(pr)
    coordTrans = osr.CoordinateTransformation(source_SR, target_SR)
    return coordTrans