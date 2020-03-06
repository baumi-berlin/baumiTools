def Calculate_Seasonal_Median(year, startMonth, endMonth, roi=None, path=None, row=None, mask_clouds=True, mask_water=False, mask_snow=False, mask_fill=True, harmonize_l8=True):
	'''
	Function that calculates a seasonal mean for an individual year in google earth engine
	Parameters:
	------------
	year (integer): Year for which the composite should be generated (required)
	startMonth (integer): starting month of the season (required)
	endMonth (integer): ending month of the season (required)
	roi: region of interest. Defines the boundary for which the composite will be calculated. (optional, defaults to None)
	path (integer): WRS2-path of the Landsat footprint (optional, defaults to None)
	row (integer): WRS2-path of the Landsat footprint (optional, defaults to None)
	
	Returns:
	---------
	image: Median of the six multispectral bands from all Landsat observations that fall inside the defined year/months
	
	'''
	import ee
	# Convert the information on year, startMonth, endMonth to a date for the filter --> define lastday of endMonth based on how many days are in that month
	if endMonth in [4,6,9,11]:
		lastDay = 30
	if endMonth in [1,3,5,7,8,10,12]:
		lastDay = 31
	if endMonth == 2:
		lastDay = 28
	start = ee.Date.fromYMD(year, startMonth, 1)
	end = ee.Date.fromYMD(year, endMonth, lastDay)
	
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
	elif path!= None and row != None:
		l4 = remove_double_counts(ee.ImageCollection('LANDSAT/LT04/C01/T1_SR').select(bands, band_names).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
		l5 = remove_double_counts(ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').select(bands, band_names).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
		l7 = remove_double_counts(ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').select(bands, band_names).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
		l8 = remove_double_counts(ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').select(l8bands, l8band_names).filterBounds(roi).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
		l8h = ee.ImageCollection(ee.Algorithms.If(harmonize_l8, l8.map(l8_harmonize), l8))
	else:
		l4 = remove_double_counts(ee.ImageCollection('LANDSAT/LT04/C01/T1_SR').select(bands, band_names).filterDate(start, end).map(apply_masks))
		l5 = remove_double_counts(ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').select(bands, band_names).filterDate(start, end).map(apply_masks))
		l7 = remove_double_counts(ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').select(bands, band_names).filterDate(start, end).map(apply_masks))
		l8 = remove_double_counts(ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').select(l8bands, l8band_names).filterBounds(roi).filterDate(start, end).map(apply_masks))
		l8h = ee.ImageCollection(ee.Algorithms.If(harmonize_l8, l8.map(l8_harmonize), l8))
	# combine landsat collections
	landsat = ee.ImageCollection(l4.merge(l5).merge(l7).merge(l8h)).select(['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2'])
	# Apply the median reducer
	median = landsat.reduce(ee.Reducer.median())
	# Select bands and edit band names
	timeStamp = "_" + str(year) + "-" + "{0:0=2d}".format(startMonth) + "-" + "{0:0=2d}".format(endMonth)
	median = median.select(['B_median', 'G_median', 'R_median', 'NIR_median', 'SWIR1_median', 'SWIR2_median']).rename(['B'+timeStamp, 'G'+timeStamp, 'R'+timeStamp, 'NIR'+timeStamp, 'SWIR1'+timeStamp, 'SWIR2'+timeStamp])
	#if roi!= None:
	#	median = median.clip(roi)
	return median