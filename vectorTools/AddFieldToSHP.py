import ogr, osr

def AddFieldToSHP(shape, name, type):
    drvMemV = ogr.GetDriverByName('Memory')
    # Check if "SHP" is a string/path or an object. If string, then copy to memory
    if isinstance(shape, str):
        shape = drvMemV.CopyDataSource(ogr.Open(shape), '')
    else:
        shape = shape
    # Shape = input-shapefile, name = name of the field, type = type of the field
    # types --> Integer=OFTInteger, Float=OFTReal, String=OFTString
    lyr = shape.GetLayer()
    # Check if field already exists, if exists throw out warning
    ldef = lyr.GetLayerDefn()
    if ldef.GetFieldIndex(name) != -1:
        print("--> Warning: Fieldname " + name + " already exists. Skipping...")
    else:
        if type == "float":
            fieldDef = ogr.FieldDefn(name, ogr.OFTReal)
        if type == "int":
            fieldDef = ogr.FieldDefn(name, ogr.OFTInteger)
        if type == "string":
            fieldDef = ogr.FieldDefn(name, ogr.OFTString)
        lyr.CreateField(fieldDef)
    return shape