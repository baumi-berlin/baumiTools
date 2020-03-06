def Calculate_Seasonal_Median(year, startMonth, endMonth, roi=None, mask_clouds=True, mask_water=False, mask_snow=False, mask_fill=True, harmonize_l8=True):
	import ee
	# Convert the information on year, startMonth, endMonth to a date for the filter
	start = ee.Date.fromYMD(ee.Number(year).subtract(ee.Number(1)), startMonth, 1)
	end = ee.Date.fromYMD(ee.Number(year).add(ee.Number(1)), endMonth, 31)
	#start = str(year) + "-" + "{0:0=2d}".format(startMonth) + "-01"
	#end = str(year) + "-" + "{0:0=2d}".format(endMonth) + "-31"
	
	# Select all the images, convert 
	select_bands = ['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']
	# band names in input and output collections
	bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'B6', 'pixel_qa']
	band_names = ['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2', 'T', 'pixel_qa']
	l8bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B1', 'B10', 'B11', 'pixel_qa']
	l8band_names = ['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2', 'UB', 'T1', 'T2', 'pixel_qa']
	# qa bits
	cloudbit = ee.Number(ee.Algorithms.If(mask_clouds, 40, 0))
	waterbit = ee.Number(ee.Algorithms.If(mask_water, 4, 0))
	snowbit = ee.Number(ee.Algorithms.If(mask_snow, 16, 0))
	fillbit = ee.Number(ee.Algorithms.If(mask_fill, 1, 0))
	bits = cloudbit.add(waterbit).add(snowbit).add(fillbit)
	## helper functions
	# function to apply masks based on pixel qa band
	def apply_masks(img):
		qa = img.select('pixel_qa')
		mask = qa.bitwiseAnd(bits).eq(0)
		return img.updateMask(mask)
	# function to harmonize l8 surface reflectance with coefficients from Roy et al. 2016
	def l8_harmonize(l8img):
		b = ee.Image(0.0183).add(ee.Image(0.8850).multiply(l8img.select('B'))).int16()
		g = ee.Image(0.0123).add(ee.Image(0.9317).multiply(l8img.select('G'))).int16()
		r = ee.Image(0.0123).add(ee.Image(0.9372).multiply(l8img.select('R'))).int16()
		nir = ee.Image(0.0448).add(ee.Image(0.8339).multiply(l8img.select('NIR'))).int16()
		swir1 = ee.Image(0.0306).add(ee.Image(0.8639).multiply(l8img.select('SWIR1'))).int16()
		swir2 = ee.Image(0.0116).add(ee.Image(0.9165).multiply(l8img.select('SWIR2'))).int16()

		out = ee.Image(b.addBands(g).addBands(r).addBands(nir).addBands(swir1).addBands(swir2).addBands(
			l8img.select(['UB', 'T1', 'T2', 'pixel_qa'])).copyProperties(l8img, l8img.propertyNames())).rename(
			l8band_names)
		return out
	# function to remove double counts from path overlap areas
	def remove_double_counts(collection):
		def add_nn(image):
			start = ee.Date.fromYMD(image.date().get('year'), image.date().get('month'),
			                        image.date().get('day')).update(hour=0, minute=0, second=0)
			end = ee.Date.fromYMD(image.date().get('year'), image.date().get('month'), image.date().get('day')).update(
				hour=23, minute=59, second=59)
			overlapping = collection.filterDate(start, end).filterBounds(image.geometry())
			nn = overlapping.filterMetadata('WRS_ROW', 'equals', ee.Number(image.get('WRS_ROW')).subtract(1)).size()
			return image.set('nn', nn)
		collection_nn = collection.map(add_nn)
		has_nn = collection_nn.filterMetadata('nn', 'greater_than', 0)
		has_no_nn = ee.ImageCollection(ee.Join.inverted().apply(collection, has_nn, ee.Filter.equals(leftField='LANDSAT_ID', rightField='LANDSAT_ID')))
		def mask_overlap(image):
			start = ee.Date.fromYMD(image.date().get('year'), image.date().get('month'), image.date().get('day')).update(hour=0, minute=0, second=0)
			end = ee.Date.fromYMD(image.date().get('year'), image.date().get('month'), image.date().get('day')).update(hour=23, minute=59, second=59)
			overlapping = collection.filterDate(start, end).filterBounds(image.geometry())
			nn = ee.Image(overlapping.filterMetadata('WRS_ROW', 'equals', ee.Number(image.get('WRS_ROW')).subtract(1)).first())
			newmask = image.mask().where(nn.mask(), 0)
			return image.updateMask(newmask)
		has_nn_masked = ee.ImageCollection(has_nn.map(mask_overlap))
		out = ee.ImageCollection(has_nn_masked.merge(has_no_nn).copyProperties(collection))
		return out

	if roi != None:
		l4 = remove_double_counts(ee.ImageCollection('LANDSAT/LT04/C01/T1_SR').select(bands, band_names).filterBounds(roi).filterDate(start, end).map(apply_masks))
		l5 = remove_double_counts(ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').select(bands, band_names).filterBounds(roi).filterDate(start, end).map(apply_masks))
		l7 = remove_double_counts(ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').select(bands, band_names).filterBounds(roi).filterDate(start, end).map(apply_masks))
		l8 = remove_double_counts(ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').select(l8bands, l8band_names).filterBounds(roi).filterDate(start, end).map(apply_masks))
		l8h = ee.ImageCollection(ee.Algorithms.If(harmonize_l8, l8.map(l8_harmonize), l8))
	else:
		l4 = remove_double_counts(ee.ImageCollection('LANDSAT/LT04/C01/T1_SR').select(bands, band_names).filterDate(start, end).map(apply_masks))
		l5 = remove_double_counts(ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').select(bands, band_names).filterDate(start, end).map(apply_masks))
		l7 = remove_double_counts(ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').select(bands, band_names).filterDate(start, end).map(apply_masks))
		l8 = remove_double_counts(ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').select(l8bands, l8band_names).filterBounds(roi).filterDate(start, end).map(apply_masks))
		l8h = ee.ImageCollection(ee.Algorithms.If(harmonize_l8, l8.map(l8_harmonize), l8))
	# combine landsat collections
	landsat = ee.ImageCollection(l4.merge(l5).merge(l7).merge(l8h)).select(select_bands)
	# Apply the median reducer
	median = landsat.reduce(ee.Reducer.median())
	return median