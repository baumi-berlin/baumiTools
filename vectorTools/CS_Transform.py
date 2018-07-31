import osr

def CS_Transform(geom, LYRto):
    ''' Function that creates the ruling for a coordinate transformation of a geometry to the geometry of a second layer.
        Is often used when doing point-intersections or zonal summaries over vectors. To reduce the amount of calculations
        this trnasformation should be defined prior to the actual processing of the geometries.

    Parameters
    -----------
    geom : object (required)
        geometry object, retrieve through: feat.GetGeometryRef()
    LYRto : object (required)
        layer object of the layer with the coordinate system we want to transform into

    Returns
    --------
    transform : object
        transformation rule for the geo-transformation

    '''
    outPR = LYRto.GetSpatialRef()
    inPR = geom.GetSpatialReference()
    transform = osr.CoordinateTransformation(inPR, outPR)
    return transform