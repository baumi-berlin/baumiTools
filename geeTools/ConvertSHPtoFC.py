def Convert_SHP_to_FC(LYR):
	packageSize = 5
	
	
	feat = LYR.GetNextFeature()
	while feat:
		geom = feat.GetGeometryRef()
	# Convert the CS to EPSG:4326
		source_SR = geom.GetSpatialReference()
		target_SR = osr.SpatialReference()
		target_SR.ImportFromEPSG(4326)
		trans = osr.CoordinateTransformation(source_SR, target_SR)
		geom.Transform(trans)
	# Build the EE-feature via the json-conversion
		geom_json = json.loads(geom.ExportToJson())
		geom_coord = geom_json['coordinates']
		geom_EE = ee.Geometry.Polygon(coords=geom_coord)
	
	
	
