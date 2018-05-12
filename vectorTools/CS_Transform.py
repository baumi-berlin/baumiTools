import osr

def CS_Transform(LYRfrom, LYRto):
    outPR = LYRto.GetSpatialRef()
    inPR = LYRfrom.GetSpatialRef()
    transform = osr.CoordinateTransformation(inPR, outPR)
    return transform