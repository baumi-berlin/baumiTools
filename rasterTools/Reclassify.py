import gdal
import numpy as np
from tqdm import tqdm

def ReclassifyRaster(inRaster, tupel):
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