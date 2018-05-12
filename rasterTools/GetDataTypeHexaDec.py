
def GetDataTypeHexaDec(gdalDtype):
    dTypes = [[1, 'b'], [2, 'H'], [3, 'h'], [4, 'I'], [5, 'i'], [6, 'f'], [7, 'd']]
    for dT in dTypes:
        if dT[0] == gdalDtype:
            band_dType = dT[1]
    return band_dType