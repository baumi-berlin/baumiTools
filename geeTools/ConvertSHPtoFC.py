def Convert_SHP_to_FC(LYR, idField, classLabelField, type="point"):
	import ee
	import ogr, osr
	import json
	
	
	liste = []

	feat = LYR.GetNextFeature()
	while feat:
		geom = feat.GetGeometryRef()
	# Convert the CS to EPSG:4326
		source_SR = geom.GetSpatialReference()
		target_SR = osr.SpatialReference()
		target_SR.ImportFromEPSG(4326)
		trans = osr.CoordinateTransformation(source_SR, target_SR)
		geom.Transform(trans)
	# Get the ID
		pid = feat.GetField(idField)
		cl = feat.GetField(classLabelField)
	# Build the EE-feature via the json-conversion
		geom_json = json.loads(geom.ExportToJson())
		geom_coord = geom_json['coordinates']
		if not type == "point":
			geom_EE = ee.Geometry.Polygon(coords=geom_coord)
		else:
			geom_EE = ee.Geometry.Point(coords=geom_coord)
	# Create feature
		eeFeat = ee.Feature(geom_EE, {"ID": pid, "Class": cl})
		liste.append(eeFeat)
	# take next feature
		feat = LYR.GetNextFeature()
	# Convert list to EE feature collection
	fc = ee.FeatureCollection(ee.List(liste))
	return fc
	
	
	
