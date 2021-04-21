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


"""
/**
 * SimpleMask: create boolean (actually int [0,1]) mask image by selecting
 *             the set of values ('classes') to be masked, in a classification.
 *             optionally an 'ignore' image can be passed, which specifies (non-zero)
 *             pixels to be excluded from the masking process (mask will always be '0')
 *
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
    def __init__(self, s2sclclassesarray):
        """
        """
        _assertlistofnumber(s2sclclassesarray)
        self.ees2sclclasseslist = ee.List(s2sclclassesarray)
 
    def makemask(self, s2sclimage, ignoremaskimage=None):
        """
        """
        def eeiterfunction(currentiterationobject, previousreturnobject):
            currentiterationsclclass  = ee.Number(currentiterationobject)
            previousreturnedmaskimage = ee.Image(previousreturnobject)
            currentreturningmaskimage = s2sclimage.eq(currentiterationsclclass).Or(previousreturnedmaskimage)
            return currentreturningmaskimage
        
        maskimage = ee.Image(self.ees2sclclasseslist.iterate(eeiterfunction, ee.Image(0))) # should be 'false' image
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
        """
        _assertlistofnumber(s2sclclassesarray)
        self.eeclasseslist = ee.List(s2sclclassesarray);
        self.eenodatalist  = None
        if nodataclassesarray is not None:
            _assertlistofnumber(nodataclassesarray)
            self.eenodatalist  = ee.List(nodataclassesarray);
        
    def makefractions(self, classesimagecollection):
        """
        """
        classescollection = classesimagecollection.map(SimpleMask(self.eeclasseslist).makemask);
        observationscount = classescollection.count();
        if self.eenodatalist is not None:
            nodatacollection  = classesimagecollection.map(SimpleMask(self.eenodatalist).makemask);
            observationscount = observationscount.subtract(nodatacollection.sum());
        return classescollection.sum().divide(observationscount).rename('ClassFractions');


"""
/**
 * StaticsMask: create boolean mask image by applying a threshold value
 *              on a ClassFractions image
 */
"""
class StaticsMask:
    """
    """
    def __init__(self, s2sclclassesarray, nodataclassesarray, threshold):
        """
        """
        self.classfractions = ClassFractions(s2sclclassesarray, nodataclassesarray);
        if not isinstance(threshold, numbers.Number) : raise ValueError("invalid threshold")
        self.eethreshold    = ee.Number(threshold);
        self.binvert        = False if (threshold > 0) else True;

    def makemask(self, classesimagecollection):
        classfractionsimage = ee.Image(self.classfractions.makefractions(classesimagecollection));
        if self.binvert:
            return classfractionsimage.lte(self.eethreshold.abs()).rename('StaticsLTMask');
        return classfractionsimage.gte(self.eethreshold).rename('StaticsGTMask');


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
 * var bazmask  = ConvMask([2,4,5,6,7], [3,8,9,10,11]], [20*9, 20*101], [-0.057, 0.025]).makemask(bazscl)
 * var cmmaker  = ConvMask([2,4,5,6,7], [3,8,9,10,11]], [20*9, 20*101], [-0.057, 0.025])
 * var foomask  = cmmaker.makemask(fooscl)
 * var barmask  = cmmaker.makemask(barscl)
 * 
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



