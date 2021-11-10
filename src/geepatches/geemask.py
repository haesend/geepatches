#
#
#
import numbers
import ee
if not ee.data._credentials: ee.Initialize()

"""
some minimal assertions
"""
def _assertlistofnumber(listofnumber):
    if listofnumber is None: raise ValueError("list not specified")
    try:
        for number in listofnumber:
            if not isinstance(number, numbers.Number) : raise ValueError("non-number in list"%(str(listofnumber),))
    except: raise ValueError("not a list")

def _assertlistoflistofnumber(listoflistofnumber):
    if listoflistofnumber is None: raise ValueError("list of lists not specified")
    try:
        for listofnumber in listoflistofnumber:
            _assertlistofnumber(listofnumber);
    except: raise ValueError("not a list of lists")

def _assertexclusive(somelist, otherlist):
    try:
        if not set(somelist).isdisjoint(otherlist) : raise ValueError("non-disjoint lists")
    except: raise ValueError("not a list")
    


"""
/**
 * SimpleMask: create boolean (actually int [0,1]) mask image by selecting
 *             the set of values ('classes') to be masked, in a classification.
 *             optionally an 'ignore' image can be passed, which specifies (non-zero)
 *             pixels to be excluded from the masking process (mask will always be '0')
 *
 * e.g.
 *   classification    values    result(mask)
 *      1 1 2 1 1                 F F T F F
 *      1 3 3 3 1      [2,3]      F T T T F
 *      1 1 2 1 4                 F F T F F
 * 
 * var bazmask  = SimpleMask([9, 10]).makemask(bazscl)
 * 
 * var smmaker  = SimpleMask([9, 10])
 * var foomask  = smmaker.makemask(fooscl)
 * var barmask  = smmaker.makemask(barscl)
 * 
 * var s2maskcollection = s2sclImageCollection.map(SimpleMask([8,9,10]).makemask);
 * 
 * TODO: using Image.remap(...) iso iteration could be interesting
 * 
 */
"""
class SimpleMask:
    """
    """
    def __init__(self, s2sclclassesarray, binvert=False):
        """
        :param s2sclclassesarray: list (python list, NOT ee.List) of class values to be masked
        :param binvert: invert the mask (optional, default Fals)
        """
        _assertlistofnumber(s2sclclassesarray)
        self.ees2sclclasseslist = ee.List(s2sclclassesarray)
        self.binvert = binvert
 
    def makemask(self, s2sclimage, ignoremaskimage=None):
        """
        """
        def eeiterfunction(currentiterationobject, previousreturnobject):
            currentiterationsclclass  = ee.Number(currentiterationobject)
            previousreturnedmaskimage = ee.Image(previousreturnobject)
            currentreturningmaskimage = s2sclimage.eq(currentiterationsclclass).Or(previousreturnedmaskimage)
            return currentreturningmaskimage
        
        maskimage = ee.Image(self.ees2sclclasseslist.iterate(eeiterfunction, ee.Image(0))) # should be 'false' image
        if self.binvert   : maskimage = maskimage.Not()
        if ignoremaskimage: maskimage = maskimage.And(ee.Image(ignoremaskimage).Not())
        return (maskimage
                    .set('system:time_start', s2sclimage.get('system:time_start'))
                    .set('system:footprint',  s2sclimage.get('system:footprint'))
                    .rename('SimpleMask'))


""""  
/**
 * ClassFractions: create fractions image from a classification ImageCollection
 *                 representing the frequency (per pixel, over time) of the
 *                 occurrence of the classes specified.
 * 
 * var s2snowfractionsimage   = ClassFractions.([11]).makefractions(s2sclImageCollection)
 * var s2cloudfractionsimage  = ClassFractions.([8,9,10]).makefractions(s2sclImageCollection)
 * 
 * to be safe, we could explicitly specify the S2 SCL NO_DATA class (being 0)
 * but in the GEE case, these pixels are not present; the images geometry is reduced to not-NO_DATA
 *
 * var s2snowfractionsimage   = ClassFractions.([11], [0]).makefractions(s2sclImageCollection)
 * var s2cloudfractionsimage  = ClassFractions.([8,9,10], [0]).makefractions(s2sclImageCollection)
 *
 * var s2cloudmaker      = ClassFractions.([8,9,10], [0])
 * var s2cloudsimage2018 = s2cloudmaker.makefractions(s2sclImageCollection2018)
 * var s2cloudsimage2018 = s2cloudmaker.makefractions(s2sclImageCollection2019)
 * 
 */
 """
class ClassFractions:
    """
    """
    def __init__(self, s2sclclassesarray, nodataclassesarray=None):
        """
        :param s2sclclassesarray: list (python list, NOT ee.List) of class values for which frequency (as a set) is to be calculated
        :param nodataclassesarray: list (python list, NOT ee.List) of class values to be ignored as observation
        :remark s2sclclassesarray and nodataclassesarray may not have common values   
        """
        _assertlistofnumber(s2sclclassesarray)
        self.simpleclassesmasker = SimpleMask(s2sclclassesarray)
        self.simplenodatamasker  = None
        if nodataclassesarray is not None:
            _assertlistofnumber(nodataclassesarray)
            _assertexclusive(nodataclassesarray, s2sclclassesarray)
            self.simplenodatamasker = SimpleMask(nodataclassesarray)
        
    def makefractions(self, classesimagecollection):
        """
        """
        classescollection = classesimagecollection.map(self.simpleclassesmasker.makemask);
        observationscount = classescollection.count();
        if self.simplenodatamasker is not None:
            nodatacollection  = classesimagecollection.map(self.simplenodatamasker.makemask);
            observationscount = observationscount.subtract(nodatacollection.sum());
        return (classescollection
                .sum()
                .divide(observationscount)
                .rename('ClassFractions')
                .setDefaultProjection(classescollection.first().projection()))


"""
/**
 * StaticsMask: create boolean mask image by applying a threshold value
 *              on a ClassFractions image
 */
"""
class StaticsMask:
    """
    """
    def __init__(self, s2sclclassesarray, nodataclassesarray, threshold, thresholdunits="percentage", eestatisticsregion=None, verbose=False):
        """
        :param thresholdunits "percentage" or "sigma":
            mask if fraction < fthreshold percentage
            mask if fraction < mean - fthreshold-sigma with mean and sigma
                mean and sigma (of the class fractions) are calculated over the specified statistics region ee.Geometry)
                this region should be (much) larger than the actual region we're interested in to get decent statistics 
                of course it would also be nice if this region was covered by the classesimagecollection, otherwise
                stranger things could happen, but seldom yield desired results.
        """
        self.classfractions = ClassFractions(s2sclclassesarray, nodataclassesarray);
        if not isinstance(threshold, numbers.Number)          : raise ValueError("invalid threshold")
        if not thresholdunits in ["percentage","sigma"]       : raise ValueError("thresholdunits must be 'percentage' or 'sigma'")
        self.thresholdunits = thresholdunits
        self.binvert        = False if (threshold > 0) else True;
        if self.thresholdunits == "percentage":
            if not (0 <= abs(threshold) <= 100)                : raise ValueError("invalid (absolute) threshold value")
            self.eethreshold = ee.Number(threshold/100.).abs()
        else:
            if not (0 <= abs(threshold) <= 4)                  : raise ValueError("ridicule (stdev) threshold value")
            self.eethreshold = ee.Number(threshold).abs()
            if not isinstance(eestatisticsregion, ee.Geometry) : raise ValueError("invalid statistics region")
            self.region = eestatisticsregion
        self.verbose = verbose

    def makemask(self, classesimagecollection):
        classfractionsimage = ee.Image(self.classfractions.makefractions(classesimagecollection));
        if self.thresholdunits == "percentage":
            if self.binvert: 
                if self.verbose: print(f"{str(type(self).__name__)}.makemask stat = frac.lte({self.eethreshold.getInfo()})")
                return ee.Image(classfractionsimage.lte(self.eethreshold).rename('StaticsMask'))
            else:            
                if self.verbose: print(f"{str(type(self).__name__)}.makemask stat = frac.gte({self.eethreshold.getInfo()})")
                return ee.Image(classfractionsimage.gte(self.eethreshold).rename('StaticsMask'))
        elif self.thresholdunits == "sigma":
            #
            # attempt 1 - maximum kernel size is too small and it takes forever
            #
            # statsimage = classfractionsimage.reduceNeighborhood(ee.Reducer.stdDev().combine(ee.Reducer.mean(), sharedInputs=True), 
            #                                                     ee.Kernel.square(100, "pixels", True, 1.0))
            #
            # attempt 2 - scale 255 is too small, (and reduceresolution is limited to maxPixels=65535)
            #             and I don't know how stdev actually works with reduceresolution
            #
            # statsimage = (classfractionsimage
            #               .reduceResolution(ee.Reducer.stdDev().combine(ee.Reducer.mean(), sharedInputs=True), maxPixels=65535)
            #               .reproject(classfractionsimage.projection().scale(255,255)))

            #if self.binvert: 
            #    return classfractionsimage.lte(statsimage.select(1).subtract(statsimage.select(0).multiply(self.eethreshold))).rename('StaticsMask')
            #else:            
            #    return classfractionsimage.gte(statsimage.select(1).add(statsimage.select(0).multiply(self.eethreshold))).rename('StaticsMask')

            #
            # attempt 3 - works only with specific eestatisticsregion so we can use 'reduceRegion'
            #
            # region_mean = classfractionsimage.reduceRegion(ee.Reducer.mean(),   geometry=self.region, maxPixels = 1e13) # reluctant to use 'combine'
            # region_sdev = classfractionsimage.reduceRegion(ee.Reducer.stdDev(), geometry=self.region, maxPixels = 1e13) # since dict is not ordered
            # if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion mean : {region_mean.values().get(0).getInfo()}")
            # if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion sdev : {region_sdev.values().get(0).getInfo()}")
            # if self.binvert:
            #     eethreshold = ee.Number(region_mean.values().get(0)).subtract(ee.Number(region_sdev.values().get(0)).multiply(self.eethreshold))
            #     if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion thrd : {eethreshold.getInfo()} (stat = frac.lte(mean - th*sdev)")
            #     return ee.Image(classfractionsimage.lte(eethreshold).rename('StaticsMask'))
            # else:
            #     eethreshold = ee.Number(region_mean.values().get(0)).add(ee.Number(region_sdev.values().get(0)).multiply(self.eethreshold))
            #     if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion thrd : {eethreshold.getInfo()} (stat = frac.gte(mean + th*sdev)")
            #     return ee.Image(classfractionsimage.gte(eethreshold).rename('StaticsMask'))

            #
            # attempt 4 - works only with specific eestatisticsregion so we can use 'reduceRegion', and we risk hardcoded directory names from combined reducer
            #
            if True:
                region_stats = classfractionsimage.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True), geometry=self.region, maxPixels = 1e13)
                region_mean_value = ee.Number(region_stats.get('ClassFractions_mean'))   # someday somebody will change this naming convention, 
                region_sdev_value = ee.Number(region_stats.get('ClassFractions_stdDev')) # next somebody else will be spending hours to find out what went wrong.
                if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion mean : {region_mean_value.getInfo()}")
                if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion sdev : {region_sdev_value.getInfo()}")
                if self.binvert:
                    region_thrd_value = region_mean_value.subtract(region_sdev_value.multiply(self.eethreshold))
                    if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion thrd : {region_thrd_value.getInfo()} (stat = frac.lte(mean - th*sdev)")
                    return ee.Image(classfractionsimage.lte(region_thrd_value).rename('StaticsMask'))
                else:
                    region_thrd_value = region_mean_value.add(region_sdev_value.multiply(self.eethreshold))
                    if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion thrd : {region_thrd_value.getInfo()} (stat = frac.gte(mean + th*sdev)")
                    return ee.Image(classfractionsimage.gte(region_thrd_value).rename('StaticsMask'))
            else:
                region_mean = classfractionsimage.reduceRegion(ee.Reducer.mean(),   geometry=self.region, maxPixels = 1e13) # reluctant to use 'combine'
                region_sdev = classfractionsimage.reduceRegion(ee.Reducer.stdDev(), geometry=self.region, maxPixels = 1e13) # since dict is not ordered
                if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion mean : {region_mean.values().get(0).getInfo()}")
                if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion sdev : {region_sdev.values().get(0).getInfo()}")
                if self.binvert:
                    eethreshold = ee.Number(region_mean.values().get(0)).subtract(ee.Number(region_sdev.values().get(0)).multiply(self.eethreshold))
                    if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion thrd : {eethreshold.getInfo()} (stat = frac.lte(mean - th*sdev)")
                    return ee.Image(classfractionsimage.lte(eethreshold).rename('StaticsMask'))
                else:
                    eethreshold = ee.Number(region_mean.values().get(0)).add(ee.Number(region_sdev.values().get(0)).multiply(self.eethreshold))
                    if self.verbose: print(f"{str(type(self).__name__)}.makemask eestatisticsregion thrd : {eethreshold.getInfo()} (stat = frac.gte(mean + th*sdev)")
                    return ee.Image(classfractionsimage.gte(eethreshold).rename('StaticsMask'))
        else:
            raise ValueError("Not yet. TODO: implement percentiles...")


"""
/**
 * SingleConvMask: create boolean mask by selecting the pixels, in a classification,
 *                 of the classes to be masked. convolute these with a gaussian kernel
 *                 and apply a threshold value.
 * 
 * var bazmask  = SingleConvMask([9, 10], 101*20, 0.0003).makemask(bazscl)
 * var cmmaker  = SingleConvMask([9, 10], 101*20, 0.0003)
 * var foomask  = cmmaker.makemask(fooscl)
 * var barmask  = cmmaker.makemask(barscl)
 * 
 * as an aid, the actual convolution image can also be retrieved
 * var fooconv  = cmmaker.makeconv(fooscl)
 * 
 * beware: by trial and error we've bravely come to the conclusion that the line
 *         .reproject({scale:s2sclimage.projection().nominalScale(), crs:s2sclimage.projection().crs()});
 *         will make sure the kernel and convolution will be expressed in the native resolution of
 *         the image. this might not be what GEE would like us to do, this might be inefficient, this
 *         might cause problems, windows updates, komkommer, kwel and hoongelach all around. so be it.
 * 
 */
"""
class SingleConvMask:
    """
    """
    def __init__(self, s2sclclassesarray, windowsizeinmeters, threshold):
        """
        """
        self.simplemasker = SimpleMask(s2sclclassesarray);
        if not isinstance(windowsizeinmeters, numbers.Number) : raise ValueError("invalid windowsizeinmeters")
        self.eekernel     = ee.Kernel.gaussian(windowsizeinmeters/2.0, windowsizeinmeters/6.0, 'meters', True);
        if not isinstance(threshold, numbers.Number) : raise ValueError("invalid threshold")
        self.eethreshold  = ee.Number(threshold).abs();
        self.binvert      = False if (threshold > 0) else True;
    
    def _convolve(self, s2sclimage, ignoremaskimage):
        simplemask  = self.simplemasker.makemask(s2sclimage);
        if self.binvert:
            simplemask = simplemask.Not();
        if ignoremaskimage is not None:
            simplemask = simplemask.And(ee.Image(ignoremaskimage).Not());
        return (simplemask
                    .convolve(self.eekernel)
                    .reproject(s2sclimage.projection(), scale=s2sclimage.projection().nominalScale()));
#                    .reproject({'scale':s2sclimage.projection().nominalScale(), 'crs':s2sclimage.projection().crs()}));

    def makeconv(self, s2sclimage, ignoremaskimage=None):
        return (self._convolve(s2sclimage, ignoremaskimage)
                    .set('system:time_start', s2sclimage.get('system:time_start'))  # there must be
                    .set('system:footprint',  s2sclimage.get('system:footprint'))   # a better way
                    .rename('Convolution'));

    def makemask(self, s2sclimage, ignoremaskimage=None):
        return (self._convolve(s2sclimage, ignoremaskimage).gt(self.eethreshold)
                    .set('system:time_start', s2sclimage.get('system:time_start'))  # there must be
                    .set('system:footprint',  s2sclimage.get('system:footprint'))   # a better way
                    .rename('SingleConvMask'));


"""
/**
 * ConvMask: combine muliple SingleConvMask's
 * 
 * var bazmask  = ConvMask([[2,4,5,6,7], [3,8,9,10,11]], [20*9, 20*101], [-0.057, 0.025]).makemask(bazscl)
 * var cmmaker  = ConvMask([[2,4,5,6,7], [3,8,9,10,11]], [20*9, 20*101], [-0.057, 0.025])
 * var foomask  = cmmaker.makemask(fooscl)
 * var barmask  = cmmaker.makemask(barscl)
 *
 * var eggsmask = SingleConvMask( [9, 10],   101*20,   0.0003 ).makemask(fooscl) # simple
 * var spammask = ConvMask(      [[9, 10]], [101*20], [0.0003]).makemask(fooscl) # conv emulating single simple - mind the syntax
 */
 """
class ConvMask:
    """
    """
    def __init__(self, list_s2sclclassesarray, list_windowsizeinmeters, list_threshold):
        """
        """
        _assertlistoflistofnumber(list_s2sclclassesarray);
        _assertlistofnumber(list_windowsizeinmeters);
        _assertlistofnumber(list_threshold);
        if len(list_s2sclclassesarray) != len(list_windowsizeinmeters) : raise ValueError("mismatching list parameters")
        if len(list_s2sclclassesarray) != len(list_threshold) :          raise ValueError("mismatching list parameters")

        self.maskslist = [];
        for iConvInd in range(len(list_s2sclclassesarray)):
            self.maskslist.append(SingleConvMask(
                list_s2sclclassesarray[iConvInd], 
                list_windowsizeinmeters[iConvInd], 
                list_threshold[iConvInd]));

    def makemask(self, s2sclimage, ignoremaskimage=None):

        eeList = ee.List( [mask.makemask(s2sclimage, ignoremaskimage) for mask in self.maskslist] );
        
        def eeiterfunction(currentiterationobject, previousreturnobject):
            currentiterationmaskimage = ee.Image(currentiterationobject);
            previousreturnedmaskimage = ee.Image(previousreturnobject);
            return currentiterationmaskimage.Or(previousreturnedmaskimage); 

        return (ee.Image(eeList.iterate(eeiterfunction, ee.Image(0)))
                  .set('system:time_start', s2sclimage.get('system:time_start'))  # there must be
                  .set('system:footprint',  s2sclimage.get('system:footprint'))   # a better way
                  .rename('ConvMask'));



