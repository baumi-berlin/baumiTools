def Calculate_Landsat_Seasonal_Median(year, startMonth, endMonth, roi=None, path=None, row=None, band_rename=False, mask_clouds=True, mask_water=False, mask_snow=False, mask_fill=True, harmonize_l8=True):
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
	# This is so that we can still name the bands homogenously even though images from the next two months are selected
	startMonth_name = startMonth
	endMonth_name = endMonth
	year_name = year
	# In case we switch to the surrounding year, we have to increase the year counter for the end date, that is why we need to specify the Startyear and endYear
	yearStart = year
	yearEnd = year

	# Convert the information on year, startMonth, endMonth to a date for the filter --> define lastday of endMonth based on how many days are in that month
	if endMonth in [4,6,9,11]:
		lastDay = 30
	if endMonth in [1,3,5,7,8,10,12]:
		lastDay = 31
	if endMonth == 2:
		lastDay = 28
	start = ee.Date.fromYMD(yearStart, startMonth, 1)
	end = ee.Date.fromYMD(yearEnd, endMonth, lastDay)

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

	# Introduce a flag. This flag controls, that there are any images in the collection that build the image.
	# If there arent't any, the the season of interest will be extended by 3 months until there are images
	img_flag = 0
	#print(year)
	while img_flag == 0:
		#print("")
		#print(yearStart, startMonth)
		#print(yearEnd, endMonth)
		if roi != None:
			l4 = remove_double_counts(ee.ImageCollection('LANDSAT/LT04/C01/T1_SR').filterBounds(roi).select(bands, band_names).filter(ee.Filter.date(start, end)).map(apply_masks))
			l5 = remove_double_counts(ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').filterBounds(roi).select(bands, band_names).filter(ee.Filter.date(start, end)).map(apply_masks))
			l7 = remove_double_counts(ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').filterBounds(roi).select(bands, band_names).filter(ee.Filter.date(start, end)).map(apply_masks))
			l8 = remove_double_counts(ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').filterBounds(roi).select(l8bands, l8band_names).filter(ee.Filter.date(start, end)).map(apply_masks))
			l8h = ee.ImageCollection(ee.Algorithms.If(harmonize_l8, l8.map(l8_harmonize), l8))
		elif path!= None and row != None:
			l4 = remove_double_counts(ee.ImageCollection('LANDSAT/LT04/C01/T1_SR').select(bands, band_names).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
			l5 = remove_double_counts(ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').select(bands, band_names).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
			l7 = remove_double_counts(ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').select(bands, band_names).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
			l8 = remove_double_counts(ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').select(l8bands, l8band_names).filterDate(start, end).filter(ee.Filter.eq('WRS_PATH', path)).filter(ee.Filter.eq('WRS_ROW', row)).map(apply_masks))
			l8h = ee.ImageCollection(ee.Algorithms.If(harmonize_l8, l8.map(l8_harmonize), l8))
		else:
			l4 = remove_double_counts(ee.ImageCollection('LANDSAT/LT04/C01/T1_SR').select(bands, band_names).filter(ee.Filter.date(start, end)).map(apply_masks))
			l5 = remove_double_counts(ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').select(bands, band_names).filter(ee.Filter.date(start, end)).map(apply_masks))
			l7 = remove_double_counts(ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').select(bands, band_names).filter(ee.Filter.date(start, end)).map(apply_masks))
			l8 = remove_double_counts(ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').select(l8bands, l8band_names).filter(ee.Filter.date(start, end)).map(apply_masks))#
			l8h = ee.ImageCollection(ee.Algorithms.If(harmonize_l8, l8.map(l8_harmonize), l8))
		# combine landsat collections
		landsat = ee.ImageCollection(l4.merge(l5).merge(l7).merge(l8h)).select(['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2'])
		# Apply the median reducer
		median = landsat.reduce(ee.Reducer.median())
		nBands = median.bandNames().getInfo()
	# Check if there are bands. If there are, calculate the median, rename the bands, and change the img_flag to 1
		if len(nBands) > 0:
	# Select bands and edit band names
			timeStamp = "_" + str(year_name) + "-" + "{0:0=2d}".format(startMonth_name) + "-" + "{0:0=2d}".format(endMonth_name)
			median = median.select(['B_median', 'G_median', 'R_median', 'NIR_median', 'SWIR1_median', 'SWIR2_median']).rename(['B'+timeStamp, 'G'+timeStamp, 'R'+timeStamp, 'NIR'+timeStamp, 'SWIR1'+timeStamp, 'SWIR2'+timeStamp])
			img_flag = 1
	# If there aren't any, add 1 month to the left and right of the interval
		else:
			img_flag = img_flag
			if endMonth < 12:
				endMonth = endMonth + 1
			else:
				yearEnd = yearEnd + 1
				endMonth = 1
			#else:
			#	endMonth = endMonth
			if startMonth > 1:
				startMonth = startMonth - 1
			else:
				startMonth = startMonth
			start = ee.Date.fromYMD(yearStart, startMonth, 1)
			end = ee.Date.fromYMD(yearEnd, endMonth, lastDay-3)

	# If we make a time calibrated model, we cannot make the specific band naming, but have to have a sequential numbering of bands
		if band_rename == True:
			old_bandnames = median.bandNames()
			bandseq = ee.List.sequence(1, old_bandnames.size())
    
			def create_bandnames(i):
				return ee.String('v').cat(ee.Number(i).format('%03d'))
    
			new_bandnames = bandseq.map(create_bandnames)
    
			median = median.select(old_bandnames, new_bandnames)
			
			
			
	return median
	
def Calculate_S2_Seasonal_Median(year, startMonth, endMonth, roi=None, resolution=10):
	'''
	Function that calculates a seasonal mean for an individual year in google earth engine
	Parameters:
	------------
	year (integer): Year for which the composite should be generated (required)
	startMonth (integer): starting month of the season (required)
	endMonth (integer): ending month of the season (required)
	roi: region of interest. Defines the boundary for which the composite will be calculated. (optional, defaults to None)
	resolution: select the multispectral bands based on their spatial resolution. (otpional, defaults to 10m)
	
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
	
	#if resolution == 10:
	bands = ee.List(['B2', 'B3', 'B4', 'B8', 'QA60'])
	band_names = ee.List(['B','G','R', 'NIR','QA60'])
	if resolution == 20:
		bands = ['B5', 'B6', 'B7', 'B8A','B11','B12','QA60']
		band_names = ['RE1','RE2','RE3','RE4','SWIR1','SWIR2','QA60']
		
	def mask_clouds(img):
		qa = img.select('QA60')
		clouds = qa.bitwiseAnd(1 << 10).eq(0)
		cirrus = qa.bitwiseAnd(1 << 11).eq(0)
		full_mask = clouds.add(cirrus)
		return img.updateMask(full_mask)#.divide(10000)
	
	if roi != None:
		s2_collect = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(roi).filter(ee.Filter.date(start, end)).select(bands, band_names).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).map(mask_clouds)
	else:
		s2_collect = ee.ImageCollection('COPERNICUS/S2_SR').filter(ee.Filter.date(start, end)).select(bands, band_names).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).map(mask_clouds)
	
	# Apply the median reducer
	median = s2_collect.reduce(ee.Reducer.median())
	# Select bands and edit band names
	timeStamp = "_" + str(year) + "-" + "{0:0=2d}".format(startMonth) + "-" + "{0:0=2d}".format(endMonth)
	if resolution == 10:
		median = median.select(['B_median', 'G_median', 'R_median', 'NIR_median']).rename(['B'+timeStamp, 'G'+timeStamp, 'R'+timeStamp, 'NIR'+timeStamp])
	if resolution == 20:
		median = median.select(['RE1_median', 'RE2_median', 'RE3_median', 'RE4_median', 'SWIR1_median', 'SWIR2_median']).rename(['RE1'+timeStamp, 'RE2'+timeStamp, 'RE3'+timeStamp, 'RE4'+timeStamp, 'SWIR1'+timeStamp, 'SWIR2'+timeStamp])
	
	return median