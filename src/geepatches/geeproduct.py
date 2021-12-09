#
#  
#
import numbers
import ee
import geeutils
import geebiopar
import geemask


"""
"""
class IProjectable(object):
    """
    By default, Earth Engine performs nearest neighbor resampling by default during reprojection.
    
    used in GEECol.getcollection (reproject to align pixel boundaries of the product with reference roi)
    """
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        depending on the nature of the (images in) the collection,
        reprojecting (to larger pixels) will be done by averaging (ordinal images),
        selecting the median (categorical images) or by a specific algorithm (e.g. log scaled images).

        TODO: check that these reductions reduce to nop in case native projection.nominalScale > target projection.nominalScale
        TODO: check that median uses existing values only - nope. doesn(t work. switching to 'mode'
        TODO: should we split ordinal images further into mean, median, ... ? S1 will always be UserProjectable, but what with rgb's?
        """
        #
        #    default implementation might be nearest neighbor
        #
        #    return (eeimagecollection
        #            .map(lambda image: image.reproject(eeprojection)))
        #
        #    but we prefer to avoid defaults as far as possible
        #
        raise NotImplementedError("Subclasses should implement this!")


"""
"""
class UserProjectable(IProjectable):
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        to be implemented by daughter
        """
        raise NotImplementedError("Subclasses should implement this!")


"""
"""
class CategoricalProjectable(IProjectable):
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        reproject categorical collection 
        - using mode because that is what we want
        - unweighted to avoid 'float' values due to fractional pixel selections
        
        remark: 
        - in case a categorical image is down sampled considerably, mode is a far better method than nearest neighbor
        - in case a categorical image is down sampled nominally, mode acts as a smoother, whereas nearest neighbor can introduce pixel shifts
        - bottom line: no silver bullet
        """
        if verbose: print(f"{str(type(self).__name__)}._reproject - using Reducer.mode() - {geeutils.szprojectioninfo(eeprojection)}")
        def reproject(image):
            return (image
                    .reduceResolution(ee.Reducer.mode().unweighted(), maxPixels=4096)
                    .reproject(eeprojection))
         
        eeimagecollection = eeimagecollection.map(reproject)
        return eeimagecollection


"""
"""
class OrdinalProjectable(IProjectable):
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        reproject ordinal collection - using mean
        """
        if verbose: print(f"{str(type(self).__name__)}._reproject - using Reducer.mean() - {geeutils.szprojectioninfo(eeprojection)}")
        def reproject(image):
            return (image
                    .reduceResolution(ee.Reducer.mean(), maxPixels=4096)
                    .reproject(eeprojection))
         
        eeimagecollection = eeimagecollection.map(reproject)
        return eeimagecollection


###############################################################################
#
# products
#
###############################################################################

"""
"""
class GEECol(object):
    """
    The 'GEECol' class represents specific ('product') collections of images. The class contains the information and algorithms
    needed to retrieve data from gee and calculate, convert... this data into the desired products for the specified region (roi).
    e.g. some ndvi-GEEProduct class should be able to collect the NIR and RED data for a specific sensor from gee,
    and apply some normalizedDifference algorithm on this data.
    
    The resulting products are expected to be exported eventually as timeseries for the specified roi.
    - In case of overlapping images -e.g. overlap of Sentinel 2 tiles- multiple images with identical
      timestamps can cover identical points.
    - In other cases -e.g. Sentinel 1- multiple images can cover different parts of the specified roi
      shortly after each other.
    To avoid these ambiguities in the product collections, images contributing to the specified roi
    are composited/mosaiced over daily intervals (probably thereby introducing more problems than solving).

    Until further notice we'll focus on 
    - single-band (output) products
    - with minimum periodicity of 1 day
    
    GEECol <---+--- GEECol_s2ndvi
               +--- GEECol_s2fapar
               +--- GEECol_s2scl
               +--- GEECol_s2sclconvmask
               +--- GEECol_s2rgb            (test)
               +--- GEECol_s1sigma0
               +--- GEECol_s1gamma0
               +--- GEECol_s1rvi            (test)
               +--- GEECol_pv333ndvi
               +--- GEECol_pv333sm
               +--- GEECol_pv333simplemask
               +--- GEECol_pv333rgb
               +--- ...
    """

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        - selects the ee.ImageCollection(s) needed to create the product
        - filters the collections to the specified roi and dates range
        - applies the product specific algorithm (e.g.: ndvi = (nir-red)/(nir+red))
        - applies mosaicing/compositing if needed:
            - e.g. in case of collections with tiled images where a roi intersects with multiple tiles (Sentinel-1)
            - e.g. in case of collections with overlapping images where points in the roi have multiple values (Sentinel-2)
            - uses a mosaicing/compositing algorithm type appropriate to the product (e.g.: ndvi and fapar typically 'max' composite)
            - assumes a minimum periodicity of 1 day for the output product, hence mosaicing/compositing is applied on images of the same date yyyymmdd
        - add collection properties describing this collection ('gee_description')
        - returns the product as single band ee.Imagecollection with distinct dates (excluding testcases and experiments)

        :param eeroi: ee.Geometry describing the region of interest (typically an ee.Geometry.Point or a ('square') ee.Geometry.Polygon)
        :param eedatefrom: ee.Date - earliest date included in the product
        :param eedatetill: ee.Date - earliest date NOT-included in the product
        :returns: ee.ImageCollection
        """
        #
        #    to be implemented by daughter
        #
        raise NotImplementedError(f"{str(type(self).__name__)} - Subclasses should implement 'collect'!")


    def scaleandflag(self, geecolimagecollection, verbose=False):
        """
        scale, clamp, cast, ... : format the collection to be exported
            
        in case this product will be exported to file, this is recommended, otherwise masked areas
            will be exported as 0 (Export.image.toDrive) or -1 (Image.getDownloadUrl)
            regardless of its content (at least that is what we see now; ee version 0.1.248)
        
        in most normal cases - the GEEColl fully specified in its collect(...) - this should be done
        
        in special cases this might be avoided or postponed. 
            e.g. when we want temporal max composite of an ndvi collection,
            in case no scaleandflag is applied, this can be done straight forward by filtering 
            the collection into date ranges, and apply the max reducer (ee.ImageCollection.max())

        :param geecolimagecollection: ee.ImageCollection obtained from GEECol.collect
        :returns: ee.ImageCollection
        """
        #
        #    to be implemented by daughter
        #
        raise NotImplementedError(f"{str(type(self).__name__)} - Subclasses should implement 'scaleandflag!'")


    def getcollection(self, eedatefrom, eedatetill, eepoint, roipixelsindiameter, refcollection=None, refroipixelsdiameter=None, doscaleandflag=True, verbose=False):
        """
        wrap _getcollection to allow some retries to avoid sporadic "ee.ee_exception.EEException: Computation timed out."
        """
        return geeutils.wrapretry(
            self._getcollection, 
            args=(eedatefrom, eedatetill, eepoint, roipixelsindiameter),
            kwargs={'refcollection':refcollection, 'refroipixelsdiameter':refroipixelsdiameter, 'doscaleandflag':doscaleandflag, 'verbose':verbose},
            attempts=8, backoffseconds=60, backofffactor=2, verbose=verbose) # max 1 + 2 + ... + 64 = 127 minutes


    def _getcollection(self, eedatefrom, eedatetill, eepoint, roipixelsindiameter, refcollection=None, refroipixelsdiameter=None, doscaleandflag=True, verbose=False):
        """
        determine reference roi (to obtain product patches congruent with reference product)
        determine reference projection (to obtain specified resolution)
        collect the specified ee.ImageCollection
        reproject and rescale this ee.ImageCollection
        add some properties to the resulting collection:
            - 'gee_refroi'      : ee.Geometry - used as region parameter for exports
            - 'gee_centerpoint' : ee.Geometry.Point - debug
            - 'gee_projection'  : ee.Projection - used to shrink the exported region a little, and to find the scale parameter for exports
            - 'gee_description' : string - used to brew filenames for exports
        """

        #
        # find reference collection
        #
        if isinstance(refcollection, ee.ImageCollection):
            if verbose: print(f"{str(type(self).__name__)}.getcollection: reference collection specified as ee.ImageCollection")
            _eerefimagecollection = refcollection
        elif isinstance(refcollection, GEECol): 
            if verbose: print(f"{str(type(self).__name__)}.getcollection: reference collection specified as {str(type(refcollection).__name__)}")
            _eerefimagecollection = refcollection.collect(eepoint, eedatefrom, eedatetill, verbose=verbose)
        else:
            if verbose: print(f"{str(type(self).__name__)}.getcollection: no reference collection specified - using self")
            _eerefimagecollection = self.collect(eepoint, eedatefrom, eedatetill, verbose=verbose)

        #
        # find reference image - assume single band, or all bands having identical projection
        #
        try:
            _eerefimage = geeutils.someImageNear(_eerefimagecollection, eedatefrom, eepoint).select(0)
            #
            #    this weird call is expected to throw in case no _eerefimage can be found (e.g. due to empty _eerefimagecollection)
            #    for strange reason the _eerefimage will have type ee.Image, even if it is not there
            #    and even then some calls will pass, while others will throw. 
            #
            if (_eerefimage.bandNames().size().getInfo() > 0): pass
        except Exception as e:
            if verbose: print(f"{str(type(self).__name__)}.getcollection: no reference image found. Exception:  {str(e)}")
            raise ValueError(f"{str(type(self).__name__)}.getcollection: no reference image found.")
        if verbose: print(f"{str(type(self).__name__)}.getcollection: selected reference image:\n{geeutils.szprojectioninfo(_eerefimage)} id:{_eerefimage.id().getInfo()}")

        #
        # find roi center
        #
        if refroipixelsdiameter is not None:
            if verbose: print(f"{str(type(self).__name__)}.getcollection: specified roi diameter in reference collection pixels: {refroipixelsdiameter}")
            pass                                                                          # roi size in pixels of reference collection
        else:
            if verbose: print(f"{str(type(self).__name__)}.getcollection: no roi diameter in reference collection pixels specified (using destination roi diameter: {roipixelsindiameter})")
            refroipixelsdiameter = roipixelsindiameter                                    # self acting as reference
            
        _refroipixelsdiameter = round(refroipixelsdiameter)                               #  "an integer" I said.
        _refroipixelsdiameter = max(_refroipixelsdiameter, 1)                             #  preferably larger then 1
        if verbose and (_refroipixelsdiameter != refroipixelsdiameter):
            print(f"{str(type(self).__name__)}.getcollection: specified roi diameter in reference collection pixels ({refroipixelsdiameter}) modified to {_refroipixelsdiameter}")

        if (_refroipixelsdiameter %2) == 0:                                               #  even diameter
            if verbose: print(f"{str(type(self).__name__)}.getcollection: selecting roi center at reference collection pixels raster intersection")
            _eeroicenterpoint = geeutils.pixelinterspoint(eepoint, _eerefimage) #  roi center on refimage pixels intersection
        else:                                                                   #  odd diameter
            if verbose: print(f"{str(type(self).__name__)}.getcollection: selecting roi center at reference collection pixel center")
            _eeroicenterpoint = geeutils.pixelcenterpoint(eepoint, _eerefimage) #  roi center on refimage pixel center
        if verbose: print(f"{str(type(self).__name__)}.getcollection: selected roi center:\n{geeutils.szgeometryinfo(_eeroicenterpoint)}")
        #
        # find actual roi -  roi radius for odd sizes: 1, 2, 3, ... - for even sizes: 0.5, 1.5, 2.5, ...
        #
        _eerefroi = geeutils.squarerasterboundsroi(_eeroicenterpoint, _refroipixelsdiameter/2, _eerefimage, verbose=verbose)
        if verbose: print(f"{str(type(self).__name__)}.getcollection: selected roi:\n{geeutils.szgeometryinfo(_eerefroi)}")
        #
        # find roi origin to translate to, to align pixel boundaries with reference roi
        #
        _eerefroiulx  = _eerefroi.coordinates().flatten().get(0)
        _eerefroiuly  = _eerefroi.coordinates().flatten().get(1)
        #
        # translate and scale reference projection to obtain target projection
        #
        _roipixelsindiameter = round(roipixelsindiameter)                              #  "an integer" I said.
        _roipixelsindiameter = max(_roipixelsindiameter, 1)                            #  preferably larger then 1
        if verbose and (_roipixelsindiameter != roipixelsindiameter):
            print(f"{str(type(self).__name__)}.getcollection: specified roi diameter in destination collection pixels ({roipixelsindiameter}) modified to {_roipixelsindiameter}")
        
        _eedstprojection = _eerefimage.projection().translate(_eerefroiulx, _eerefroiuly)
        _eedstprojection = _eedstprojection.scale(_refroipixelsdiameter/_roipixelsindiameter, _refroipixelsdiameter/_roipixelsindiameter)
        if verbose: print(f"{str(type(self).__name__)}.getcollection: destination projection roi:\n{geeutils.szprojectioninfo(_eedstprojection)}")
        #
        # find native image collection
        #
        _eenatimagecollection = self.collect(_eerefroi, eedatefrom, eedatetill, verbose=verbose)
        if _eenatimagecollection is None:
            if verbose: print(f"{str(type(self).__name__)}.getcollection: destination collection is empty - bailing out")
            raise ValueError(f"{str(type(self).__name__)}.getcollection: destination collection is empty.")
        #
        # reproject it, to align pixel boundaries with reference roi, in resolution specified by roipixelsindiameter
        #
        _eedstimagecollection = self._reproject(_eenatimagecollection, _eedstprojection, verbose=verbose)
        #
        # apply scaling, clipping, masking,... preparing the collection for export
        #
        if doscaleandflag:
            _eedstimagecollection = self.scaleandflag(_eedstimagecollection, verbose=verbose)
            if verbose: print(f"{str(type(self).__name__)}.getcollection: scaled collection: {geeutils.szimagecollectioninfo(_eedstimagecollection)}")
        #
        # add some collection properties (e.g. used during export)
        #
        _eedstimagecollection = _eedstimagecollection.set('gee_refroi',      _eerefroi)
        _eedstimagecollection = _eedstimagecollection.set('gee_centerpoint', _eeroicenterpoint)
        _eedstimagecollection = _eedstimagecollection.set('gee_projection',  _eedstprojection)
        if verbose: 
            print(f"{str(type(self).__name__)}.getcollection: set 'gee_refroi' to: \n{geeutils.szgeometryinfo(_eerefroi)}")
            print(f"{str(type(self).__name__)}.getcollection: set 'gee_projection' to: \n{geeutils.szprojectioninfo(_eedstprojection)}")
        #
        #
        #
        if True:
            #
            #    store intermediates so client can retrieve them for debugging
            #
            self._eerefimagecollection = _eerefimagecollection
            self._eerefimage           = _eerefimage
            self._refroipixelsdiameter = _refroipixelsdiameter
            self._eeroicenterpoint     = _eeroicenterpoint
            self._eerefroi             = _eerefroi
            self._eerefroiulx          = _eerefroiulx
            self._eerefroiuly          = _eerefroiuly
            self._roipixelsindiameter  = _roipixelsindiameter
            self._eedstprojection      = _eedstprojection
            self._eenatimagecollection = _eenatimagecollection
            self._eedstimagecollection = _eedstimagecollection
        #
        #
        #
        return _eedstimagecollection


###############################################################################
#
# Sentinel 2 related products
#
###############################################################################

"""
"""
class S2sclcppfilter(geemask.IColFilter):
    """
    simple filter for sentinel 2 collections, based on scene classification.
    default settings emulate some 'cloudy pixel percentage' filter: maximum 95% pixels have SCL class 8,9 or 10
    typical use in the collect method of sentinel 2  products (GEECol daughter classes)
    """
    def __init__(self, s2sclclassesarray=[8,9,10], thresholdpct=-95):
        """
        :param s2sclclassesarray: list (python list, NOT ee.List) of the SCL class values to be evaluated
        :param thresholdpct: the minimum (positive thresholds) or maximum (negative thresholds) percentage coverage by these classes ( [0..100] )
        """
        self.filter = geemask.SimpleFilter('SCL', s2sclclassesarray, thresholdpct)

    def filtercollection(self, eeimagecollection, eeregion, verbose=False):
        """
        :param eeimagecollection: sentinel 2 ee.ImageCollection to be filtered (MUST CONTAIN SCL BAND)
        :param eeregion: region to be evaluated by the filter (would be nice if the eeimagecollection actually covers this region...)
        """
        if verbose: print(f"{str(type(self).__name__)}.filtercollection: input collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        eeimagecollection = self.filter.filtercollection(eeimagecollection, eeregion, verbose=verbose)
        if verbose: print(f"{str(type(self).__name__)}.filtercollection: resulting collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        return eeimagecollection


"""
"""
class GEECol_s2ndvi(GEECol, OrdinalProjectable):

    def __init__(self, colfilter=None):
        self.colfilter=colfilter
        if (colfilter is not None) and (not isinstance(colfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")
        
    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        #
        #    base collection
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
                             .select(['B4', 'B8', 'SCL'])                               # B4~Red B8~Nir - SCL to allow SCL-based filters
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    (optional) filtering
        #
        if self.colfilter is not None:
            eeimagecollection = self.colfilter.filtercollection(eeimagecollection, eeroi, verbose=verbose)
        #
        #    apply ndvi = (nir-red)/(nir+red)
        #
        def ndvi(image):
            return ((image.select('B8').subtract(image.select('B4'))).divide(image.select('B8').add(image.select('B4')))
                    .rename('NDVI')
                    .copyProperties(image, ['system:id', 'system:time_start']))
        eeimagecollection = eeimagecollection.map(ndvi)
        #
        #    apply maximum composite in case of overlapping images on same day
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="max", verbose=verbose)
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2ndvi')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .clamp(-1,1)           # clamp looses properties 
                                                                 .toFloat()             # should be obsolete here, but side effect is no-data as -inf or nan iso 0
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection


"""
GEECol_s2ndvi with historical vito ndvi scaling
"""
class GEECol_s2ndvi_he(GEECol_s2ndvi):

    def __init__(self, colfilter=None):
        super().__init__(colfilter)

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        return super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose).set('gee_description', 'S2ndvi_he')

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        #
        #    historical vito ndvi scaling [ -0.08, 0.92 ] -> [0, 250] with 255 as no-data
        #
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .add(0.08).multiply(250).clamp(0,250)
                                                                 .unmask(255, False)
                                                                 .toUint8()
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection        


"""
"""
class GEECol_s2fapar(GEECol, OrdinalProjectable):

    def __init__(self, colfilter=None):
        self.colfilter=colfilter
        if (colfilter is not None) and (not isinstance(colfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        #
        #    base collection
        #
        #    beware: apparently the collection contains some images with missing properties
        #            e.g. ee.Image('COPERNICUS/S2_SR/20190117T061209_20190117T061411_T42TVK')
        #
        #            geebiopar.get_s2fapar3band expects 'MEAN_INCIDENCE_ZENITH_ANGLE_B8', 'MEAN_SOLAR_ZENITH_ANGLE', 
        #            'MEAN_SOLAR_AZIMUTH_ANGLE' and 'MEAN_INCIDENCE_AZIMUTH_ANGLE_B8' to be available,
        #            hence the additional "notNull" filter
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
                             .select(['B3', 'B4', 'B8', 'SCL'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill))
                             .filter(ee.Filter.notNull(['MEAN_INCIDENCE_ZENITH_ANGLE_B8', 'MEAN_SOLAR_ZENITH_ANGLE', 'MEAN_SOLAR_AZIMUTH_ANGLE', 'MEAN_INCIDENCE_AZIMUTH_ANGLE_B8'])))
        #
        #    (optional) filtering
        #
        if self.colfilter is not None:
            eeimagecollection = self.colfilter.filtercollection(eeimagecollection, eeroi, verbose=verbose)
        #
        #    apply fapar network
        #
        def fapar(image):
            return (geebiopar.get_s2fapar3band(image)
                    .rename('FAPAR')
                    .copyProperties(image, ['system:id', 'system:time_start']))
        eeimagecollection = eeimagecollection.map(fapar)
        #
        #    apply maximum composite in case of overlapping images on same day
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="max", verbose=verbose)
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2fapar')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .clamp(0,1)            # clamp looses properties 
                                                                 .toFloat()             # otherwise would be double (Float64)
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection


"""
GEECol_s2fapar with historical vito fapar scaling
"""
class GEECol_s2fapar_he(GEECol_s2fapar):

    def __init__(self, colfilter=None):
        super().__init__(colfilter)

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        return super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose).set('gee_description', 'S2fapar_he')

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        #
        #    historical vito fapar scaling [ 0, 1 ] -> [0, 200] with 255 as no-data
        #
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .multiply(200).clamp(0,200)
                                                                 .unmask(255, False)
                                                                 .toUint8()
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection  


"""
"""
class GEECol_s2scl(GEECol, CategoricalProjectable):
    """
    https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR
    
    Scene Classification Map (The "No Data" value of 0 is masked out)
         1     ff0004     Saturated or defective
         2     868686     Dark Area Pixels
         3     774b0a     Cloud Shadows
         4     10d22c     Vegetation
         5     ffff52     Bare Soils
         6     0000ff     Water
         7     818181     Clouds Low Probability / Unclassified
         8     c0c0c0     Clouds Medium Probability
         9     f1f1f1     Clouds High Probability
        10     bac5eb     Cirrus
        11     52fff9     Snow / Ice
    """

    def __init__(self, colfilter=None):
        self.colfilter=colfilter
        if (colfilter is not None) and (not isinstance(colfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        #
        #    base collection
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
                             .select(['SCL'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    (optional) filtering
        #
        if self.colfilter is not None:
            eeimagecollection = self.colfilter.filtercollection(eeimagecollection, eeroi, verbose=verbose)
        #
        #    apply mode composite in case of overlapping images on same day
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="mode", verbose=verbose)
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2scl')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        'S2 half tiles' (e.g. 31UES on '2020-01-29') have limited their footprint to the area 
        where data lives, thus *NOT* the full 31UES footprint
        when exporting these images, we'll mask the empty area with 0 - being the SCENE CLASSIFICATION NO-DATA value
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(0, False)      # no data to 0 
                                                                 .toUint8()))           # actually obsolete here
        return eeimagecollection


"""
"""
class GEECol_s2sclsimplemask(GEECol_s2scl):
    """
    """
    def __init__(self, s2sclclassesarray=None, binvert=None, colfilter=None):
        """
        """
        super().__init__(colfilter)

        if s2sclclassesarray is None:
            s2sclclassesarray =  [2, 4, 5, 6, 7] # assuming 2,4,5,6 en 7 to be 'valid' classification classes (unlike 'volatile' clouds, saturations, snow,...)
        if binvert is None:
            binvert = True
        
        self.maskmaker = geemask.SimpleMask(s2sclclassesarray, binvert)

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection: SCL from parent - already composited (daily) to avoid striping at overlaps
        #
        eeimagecollection = super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose)
        #
        #
        #
        def simplemask(image):
            return (self.maskmaker
                    .makemask(image)
                    .toUint8()           # uint8 [0:not masked, 1:masked]  (obsolete ?)
                    .rename('MASK')
                    .copyProperties(image, ['system:time_start', 'gee_date']))
        eeimagecollection = eeimagecollection.map(simplemask)
        #
        #    no mosaic/composite - already done in base collection
        #
        pass
        #
        #    add collection properties describing this collection (in this case: overwrites 'gee_description' from GEECol_s2scl)
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2sclsimplemask')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        'S2 half tiles' (e.g. 31UES on '2020-01-29') have limited their footprint to the area 
        where data lives, thus *NOT* the full 31UES footprint
        when exporting masks [0,1] for these images, we'll indicate the unknown area with 255 as no data
        
          0: not masked (clear sky)
          1: masked     (belgian sky)
        255: no data    (belgian politics)
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(255, False)    # no data to 255
                                                                 .toUint8()))           # actually obsolete here
        return eeimagecollection


"""
"""
class GEECol_s2sclconvmask(GEECol_s2scl):
    """
    """
    def __init__(self, lsts2sclclassesarray=None, lstwindowsizeinmeters=None, lstthreshold=None, colfilter=None):
        """
        """
        super().__init__(colfilter)

        if lsts2sclclassesarray is None:
            lsts2sclclassesarray =  [[2, 4, 5, 6, 7], [3, 8, 9, 10, 11]]
        if lstwindowsizeinmeters is None:
            lstwindowsizeinmeters = [20*9, 20*101]
        if lstthreshold is None:
            lstthreshold =  [-0.057, 0.025]
        
        self.maskmaker = geemask.ConvMask(lsts2sclclassesarray, lstwindowsizeinmeters, lstthreshold)

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection: SCL from parent - already composited (daily) to avoid striping at overlaps
        #
        eeimagecollection = super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose)
        #
        #
        #
        def convmask(image):
            return (self.maskmaker
                    .makemask(image)
                    .toUint8()           # uint8 [0:not masked, 1:masked]  (obsolete ?)
                    .rename('MASK')
                    .copyProperties(image, ['system:time_start', 'gee_date']))
        eeimagecollection = eeimagecollection.map(convmask)
        #
        #    no mosaic/composite - already done in base collection
        #
        pass
        #
        #    add collection properties describing this collection (in this case: overwrites 'gee_description' from GEECol_s2scl)
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2sclconvmask')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        'S2 half tiles' (e.g. 31UES on '2020-01-29') have limited their footprint to the area 
        where data lives, thus *NOT* the full 31UES footprint
        when exporting masks [0,1] for these images, we'll indicate the unknown area with 255 as no data
        
          0: not masked (clear sky)
          1: masked     (belgian sky)
        255: no data    (belgian politics)
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(255, False)    # no data to 255
                                                                 .toUint8()))           # actually obsolete here
        return eeimagecollection


"""
"""
class GEECol_s2sclstaticsmask(GEECol_s2scl):

    def __init__(self, s2sclclassesarray=None, threshold=None, thresholdunits=None, statisticsareametersradius=None):
        """
        :param s2sclclassesarray: list of s2 scl classes
        :param thresholdunits: "sigma", "percentage" or "percentile" - defaults to "sigma" 
        :param threshold: threshold value. can be absolute percentage or based on regional statistics
                 - thresholdunits: "sigma":      +/- ]0,4]   - mask if frequency >= mean + threshold * sigma or frequency <= mean -  abs(threshold) * sigma
                 - thresholdunits: "percentile": +/- [1,100] - mask if frequency >= percentile(threshold)    or frequency < percentile(abs(threshold))
                 - thresholdunits: "percentage": +/- [1,100] - mask if frequency >= threshold                or frequency < abs(threshold)
                                                 (using values [1,100] to avoid confusion between fractions and percentages)
        :param statisticsareametersradius: (only for thresholdunits="sigma") specifies the region over which mean and sigma will be calculated
                 - actual area is square with radius statisticsareametersradius
                 - this area is assumed to be "large" with respect to the actual target region (in .collect)
        """
        #
        # super (GEECol_s2scl) WITHOUT filter
        #
        super().__init__(colfilter=None)
        #
        # s2sclclassesarray
        #
        if s2sclclassesarray is None: 
            self.s2sclclassesarray = [3,8,9,10,11]                            # default: in clouds we trust, ... and snow?
        else:
            if not isinstance(s2sclclassesarray, list)                        : raise ValueError("s2sclclassesarray expected to be a list")
            for number in s2sclclassesarray:
                if not isinstance(number, numbers.Number)                     : raise ValueError("s2sclclassesarray expected to be a list of integers")
                if not (0 <= number <= 11)                                    : raise ValueError("ridicule s2 scl class value (expected [0,11])")
            
            self.s2sclclassesarray = s2sclclassesarray

        #
        # thresholdunits
        #
        if thresholdunits is None: 
            self.thresholdunits = "sigma"                                     # default: threshold based on regional statistics
        else:
            if not thresholdunits in ["percentage", "sigma", "percentile"]    : raise ValueError("thresholdunits expected to be 'percentage', 'sigma' or 'percentile'")
            self.thresholdunits = thresholdunits

        #
        # threshold
        #
        if self.thresholdunits == "sigma":
            if threshold is None:
                self.threshold = 2                                            # default: strict - lose only about 2.1 % (assuming a normal distribution)
            else:
                if not isinstance(threshold, numbers.Number)                  : raise ValueError("invalid threshold")
                if not (0 < abs(threshold) <= 4)                              : raise ValueError("ridicule (stdev) threshold value (expected ]0,4])")
                self.threshold = threshold
            
        else:
            if threshold is not None:
                if not isinstance(threshold, numbers.Number)                  : raise ValueError("invalid threshold")
                if not (1 <= abs(threshold) <= 100)                           : raise ValueError("invalid threshold value  (expected +/- [1, 100]")
                self.threshold = threshold
            else:
                if self.thresholdunits == "percentage":
                    self.threshold = 70                                       # default for "percentage"
                else:
                    self.threshold = 98                                       # default for "percentile"


        #
        # regional statistics area
        #
        if self.thresholdunits == "percentage":
            self.metersradius = 0                                             # not used with absolute thresholds                
        else:
            if statisticsareametersradius is None:
                self.metersradius = 25000                                     # default: about a quarter of typical s2 tile ( which is 100km x 100km )
            else:
                if not isinstance(statisticsareametersradius, numbers.Number) : raise ValueError("invalid statisticsareametersradius")
                if ( statisticsareametersradius < 500)                        : raise ValueError("ridicule statisticsareametersradius value (expected min 500)")
                self.metersradius = statisticsareametersradius
            
    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #
        #
        if verbose: print(f"{str(type(self).__name__)}.collect: threshold({self.threshold} {self.thresholdunits}) area({self.metersradius} radius)")
        #
        # daily mosaiced scl collection
        #
        eesclimgcollection = super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose)
        #
        #
        #
        if self.thresholdunits != "percentage": eestatisticsregion = geeutils.squareareaboundsroi(eeroi.centroid(maxError=0.001), self.metersradius)
        else:                                   eestatisticsregion = None
        #
        #
        #
        staticsmask        = ( ee.Image(geemask.StaticsMask(
            self.s2sclclassesarray, 
            None, 
            self.threshold, 
            self.thresholdunits, 
            eestatisticsregion, 
            verbose=verbose)
            .makemask(eesclimgcollection)
            .toUint8()           # uint8 [0:not masked, 1:masked]  (obsolete ?)
            .rename('STATICS')
            .copyProperties(eesclimgcollection.first(), ['system:time_start', 'gee_date'])))
        #
        #    make (single image) collection and add properties describing this collection
        #       
        szdescription = "S2sclstaticsmask(" + str(self.threshold) + self.thresholdunits + ")"
        eeimagecollection = ee.ImageCollection(staticsmask).set('gee_description', szdescription)
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        'S2 half tiles' (e.g. 31UES on '2020-01-29') have limited their footprint to the area 
        where data lives, thus *NOT* the full 31UES footprint
        when exporting masks [0,1] for these images, we'll indicate the unknown area with 255 as no data

        since staticsmask is supposed to use large date ranges, this actually schouldn't matter here
        
          0: not masked (clear sky)
          1: masked     (belgian sky)
        255: no data    (belgian politics)
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(255, False)    # no data to 255
                                                                 .toUint8()))           # actually obsolete here
        return eeimagecollection


"""
"""
class GEECol_s2sclcombimask(GEECol_s2scl):
    """
    convmask using staticsmask as ignoremaskimage to exclude 'abnormal' pixels from convolutions
    """
    def __init__(self, 
                 conv_lsts2sclclassesarray=None, conv_lstwindowsizeinmeters=None, conv_lstthreshold=None, colfilter=None,
                 stat_s2sclclassesarray=None, stat_threshold=None, stat_thresholdunits=None, stat_statisticsareametersradius=None, stat_idaysbackward=None):
        """
        """
        #
        # super (GEECol_s2scl) WITHOUT filter 
        #    - filtering will be applied on the result (hence after ignoremaskimage has been calculated on the 'complete' collection)
        #    - this does not give completely identical results as GEECol_s2sclconvmask, since now filter is applied AFTER mosaic
        #
        super().__init__(colfilter=None)
        self.finalcolfilter=colfilter
        if (self.finalcolfilter is not None) and (not isinstance(self.finalcolfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")
        #
        #
        #
        if conv_lsts2sclclassesarray       is None: conv_lsts2sclclassesarray       = [[2, 4, 5, 6, 7], [3, 8, 9, 10, 11]]
        if conv_lstwindowsizeinmeters      is None: conv_lstwindowsizeinmeters      = [20*9, 20*101]
        if conv_lstthreshold               is None: conv_lstthreshold               = [-0.057, 0.025] #[-0.057, 0.015]
 
        self.conv_maskmaker = geemask.ConvMask(conv_lsts2sclclassesarray, conv_lstwindowsizeinmeters, conv_lstthreshold)
        #
        #
        #
        self.stat_s2sclclassesarray          = [3, 8, 9, 10, 11] if stat_s2sclclassesarray          is None else stat_s2sclclassesarray
        self.stat_threshold                  = 2                 if stat_threshold                  is None else stat_threshold
        self.stat_thresholdunits             = "sigma"           if stat_thresholdunits             is None else "sigma"
        self.stat_statisticsareametersradius = 25000             if stat_statisticsareametersradius is None else  stat_statisticsareametersradius
        self.stat_idaysbackward              = 365               if stat_idaysbackward              is None else stat_idaysbackward
        
    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #
        #
        if verbose: print(f"{str(type(self).__name__)}.collect")
        #
        #    obtain staticsmask used as ignoremaskimage in ConvMask.makemask
        #
        if self.stat_idaysbackward <= 0:
            staticsmask        = None
            eesclimgcollection = super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose)

        else:
            if self.stat_thresholdunits != "percentage": eestatisticsregion = geeutils.squareareaboundsroi(eeroi.centroid(maxError=0.001), self.stat_statisticsareametersradius)
            else:                                        eestatisticsregion = None

            eesclimgcollection = super().collect(eeroi, eedatefrom.advance(-1*self.stat_idaysbackward, 'day'), eedatetill, verbose=verbose)
            staticsmask        = ee.Image(geemask.StaticsMask(
                self.stat_s2sclclassesarray, 
                None, 
                self.stat_threshold, 
                self.stat_thresholdunits, 
                eestatisticsregion, 
                verbose=verbose)
                .makemask(eesclimgcollection))
            eesclimgcollection = eesclimgcollection.filter(ee.Filter.date(eedatefrom, eedatetill))
        #
        #    (optional) filtering - remark: staticsmask is calculated with complete (unfiltered) scl collection
        #
        if self.finalcolfilter is not None:
            eesclimgcollection = self.finalcolfilter.filtercollection(eesclimgcollection, eeroi, verbose=verbose)

        #
        #
        #
        def mask(image):
            return (self.conv_maskmaker.makemask(image, staticsmask)
                    .toUint8()           # uint8 [0:not masked, 1:masked]  (obsolete ?)
                    .rename('MASK')
                    .copyProperties(image, ['system:time_start', 'gee_date']))
        
        eeimagecollection = eesclimgcollection.map(mask)
        #
        #    add collection properties describing this collection (in this case: overwrites 'gee_description' from GEECol_s2scl)
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2sclcombimask')
        #
        #
        #
        return eeimagecollection            

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        'S2 half tiles' (e.g. 31UES on '2020-01-29') have limited their footprint to the area 
        where data lives, thus *NOT* the full 31UES footprint
        when exporting masks [0,1] for these images, we'll indicate the unknown area with 255 as no data
        
          0: not masked (clear sky)
          1: masked     (belgian sky)
        255: no data    (belgian politics)
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(255, False)    # no data to 255
                                                                 .toUint8()))           # actually obsolete here
        return eeimagecollection


"""
"""
class GEECol_s2sclclassfractions(GEECol_s2scl):

    def __init__(self, s2sclclassesarray=None):
        """
        this class is only ment as an aid in evaluating the GEECol_s2sclstaticsmask parameters
        :param s2sclclassesarray: list of s2 scl classes
        """
        #
        # super (GEECol_s2scl) WITHOUT filter
        #
        super().__init__(colfilter=None)
        #
        # s2sclclassesarray
        #
        if s2sclclassesarray is None: 
            self.s2sclclassesarray = [3,8,9,10,11]                            # default: in clouds we trust, ... and snow?
        else:
            if not isinstance(s2sclclassesarray, list)                        : raise ValueError("s2sclclassesarray expected to be a list")
            for number in s2sclclassesarray:
                if not isinstance(number, numbers.Number)                     : raise ValueError("s2sclclassesarray expected to be a list of integers")
                if not (0 <= number <= 11)                                    : raise ValueError("ridicule s2 scl class value (expected [0,11])")
            
            self.s2sclclassesarray = s2sclclassesarray

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        # daily mosaiced scl collection
        #
        eesclimgcollection = super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose)
        #
        #
        #
        fractions = ( ee.Image(geemask.ClassFractions(
            self.s2sclclassesarray, 
            None)
            .makefractions(eesclimgcollection)
            .rename('FRACTIONS')
            .copyProperties(eesclimgcollection.first(), ['system:time_start', 'gee_date'])))
        #
        #    make (single image) collection and add properties describing this collection
        #       
        eeimagecollection = ee.ImageCollection(fractions).set('gee_description', "S2sclclassfractions")
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        we'll scale the fractions [0.0, 1.0] to percentages [0, 100]

        we'll export them as Int16, 
        *NOT as Uint8*, because my current QGIS has problems showing histograms of Uint8, 
        *NOT as Int8*, because my current GEE exports these - according to QGIS- "Data type    Int16 - Sixteen bit signed integer" anyway
        hence, with Int16, at least we know what we are doing, we can use 255 for no-data, and we get a decent histogram
        ...jiezes...I just should have kept floats...
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .multiply(100)
                                                                 .clamp(0,100)               # looses properties
                                                                 .unmask(255, False)         # no data to 255
                                                                 .toInt16()                  # .toUint8()
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection


"""
"""
class GEECol_s2rgb(GEECol, OrdinalProjectable):
    """
    experimental - just for the fun of it (to check where multiband images give problems)
    
    https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR
    - doesn't bother to give minimum and maximum values of the bands
    - their sample snippet hacks around with the quality bands to reduce clouds, and then ***.divide(10000)*** - this gives a hint?
    
    https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/definitions
    - tells something about TCI bands (True Color Image)
        'The TCI is an RGB image built from the B02 (Blue), B03 (Green), and B04 (Red) Bands. 
        The reflectances are coded between 1 and 255, 0 being reserved for 'No Data'. 
        The saturation level of 255 digital counts correspond to a level of 3558 for L1C products 
        or 2000 for L2A products (0.3558 and 0.2 in reflectance value respectively.'
        
        GEE collection seems to have replaced this 'No Data' by masking it.

    - Sentinel-2 Products Specification Document (issue 14.6 16/03/2021) page 425:
        'The conversion formulae to apply to image Digital Numbers (DN) to obtain physical values is:
        Reflectance (float) = DC / (QUANTIFICATION_VALUE)
        Note that the reflectance meaningful values go from "1" to "65535" as "0" is reserved for the NO_DATA.

        problem: ...DN...DC... ???
        problem: QUANTIFICATION_VALUE not found in GEE
        
    https://gis.stackexchange.com/questions/233874/what-is-the-range-of-values-of-sentinel-2-level-2a-images
    - refers to "Level 2A Product Format Specifications Technical Note"
    - which is nowhere to be found (anymore?)
    - but claims that once upon a time, there might have been 
        - a formulae: Surface reflectance SR = DN / 10000.
        - a comment: spectacular effects on surface or clouds could lead to values higher than 1.0
        
    """
    def __init__(self, colfilter=None):
        self.colfilter=colfilter
        if (colfilter is not None) and (not isinstance(colfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):

#         eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
#                              .select(['B4', 'B3', 'B2'])
#                              .filterBounds(eeroi)
#                              .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    using the mystic TCI bands - including SCL to allow SCL based filter
        #       
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
                             .select(['TCI_R', 'TCI_G', 'TCI_B', 'SCL'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    (optional) filtering - typically -but not mandatory- using an SCL based filter
        #
        if self.colfilter is not None:
            eeimagecollection = self.colfilter.filtercollection(eeimagecollection, eeroi, verbose=verbose)
        #
        #    drop SCL band which was only included to allow SCL based filter
        #
        eeimagecollection = eeimagecollection.select(['TCI_R', 'TCI_G', 'TCI_B'])
        #
        #    apply median composite in case of overlapping images on same day
        #    could be refined (e.g. select value with max ndvi) but worldcover 
        #    uses median too, and this is just an experimental class anyway.
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="median", verbose=verbose)
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2tcirgb')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(0, False)      # no data to 0 as esa intended
                                                                 .toUint8()))
        return eeimagecollection


"""
"""
class GEECol_s2cloudlessmask(GEECol, CategoricalProjectable):
    """
    copy of the gee tutorial "Sentinel-2 Cloud Masking with s2cloudless"

    https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless
    https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_CLOUD_PROBABILITY#description
    
    issues:
    - s2cloudless probability has problems at edges 
        - e.g. geeutils.half31UESpoint on geeutils.half31UESday
          - data beyond image data (at edge)
          - and this data does not seem correct
    - resulting (mask) image extends beyond edges too 
        - hence the updateMask with SCL mask, at least it is consistent with GEECol_s2sclconvmask
    - suggested parameters need tuning. 
        - e.g. CLD_PRJ_DIST on 1 km is too little for half31UESpoint on geeutils.half31UESday; shadows are ignored.
        
    """
    def __init__(self):
        """
        configuration parameters:
        CLOUD_FILTER    (60)   integer    Maximum image cloud cover percent allowed in image collection
        CLD_PRB_THRESH  (50)   integer    Cloud probability (%); values greater than are considered cloud
        NIR_DRK_THRESH  (0.15) float      Near-infrared reflectance; values less than are considered potential cloud shadow
        CLD_PRJ_DIST    (1)    float      Maximum distance (km) to search for cloud shadows from cloud edges
        BUFFER          (50)   integer    Distance (m) to dilate the edge of cloud-identified objects
        """
        self.CLOUD_FILTER   = 100   #60
        self.CLD_PRB_THRESH = 40    #50
        self.NIR_DRK_THRESH = 0.15
        self.CLD_PRJ_DIST   = 5     #1
        self.BUFFER         = 100   #50
    
    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        # Import and filter S2 SR.
        #
        s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR')
                     .filterBounds(eeroi)
                     .filterDate(eedatefrom, eedatetill)
                     .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', self.CLOUD_FILTER)))
        #
        # Import and filter s2cloudless.
        #
        s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
                            .filterBounds(eeroi)
                            .filterDate(eedatefrom, eedatetill))
        #
        # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
        #
        eeimagecollection = ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
            'primary': s2_sr_col,
            'secondary': s2_cloudless_col,
            'condition': ee.Filter.equals(**{
                'leftField': 'system:index', 'rightField': 'system:index'})}))

        #
        # Define a function to add the s2cloudless probability layer and derived cloud mask as bands to an S2 SR image input.
        #
        def add_cloud_bands(img):
            # Get s2cloudless image, subset the probability band.
            cld_prb = ee.Image(img.get('s2cloudless')).select('probability')
        
            # Condition s2cloudless by the probability threshold value.
            is_cloud = cld_prb.gt(self.CLD_PRB_THRESH).rename('clouds')
        
            # Add the cloud probability layer and cloud mask as image bands.
            return img.addBands(ee.Image([cld_prb, is_cloud]))

        # 
        # Define a function to add dark pixels, cloud projection, and identified shadows as bands to an S2 SR image input. 
        # Note that the image input needs to be the result of the above add_cloud_bands function 
        # because it relies on knowing which pixels are considered cloudy ('clouds' band).
        # 
        def add_shadow_bands(img):
            # Identify water pixels from the SCL band.
            not_water = img.select('SCL').neq(6)
        
            # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
            SR_BAND_SCALE = 1e4
            dark_pixels = img.select('B8').lt(self.NIR_DRK_THRESH*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')
        
            # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
            shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));
        
            # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
            cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, self.CLD_PRJ_DIST*10)
                .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
                .select('distance')
                .mask()
                .rename('cloud_transform'))
        
            # Identify the intersection of dark pixels with cloud shadow projection.
            shadows = cld_proj.multiply(dark_pixels).rename('shadows')
        
            # Add dark pixels, cloud projection, and identified shadows as image bands.
            return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))              

        #
        # Define a function to assemble all of the cloud and cloud shadow components and produce the final mask.
        #
        def add_cld_shdw_mask(img):
            # Add cloud component bands.
            img_cloud = add_cloud_bands(img)
        
            # Add cloud shadow component bands.
            img_cloud_shadow = add_shadow_bands(img_cloud)
        
            # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
            is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)
        
            # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
            # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
            is_cld_shdw = (is_cld_shdw.focal_min(2).focal_max(self.BUFFER*2/20)
                .reproject(**{'crs': img.select([0]).projection(), 'scale': 20})
                .rename('cloudmask'))
        
            # Add the final cloud-shadow mask to the image.
            return img_cloud_shadow.addBands(is_cld_shdw)
 
        #       
        #    base collection - extend with calculated bands => now the thing has 29 bands ( print(geeutils.szbandsinfo(eeimagecollection.first())) )
        #
        eeimagecollection = eeimagecollection.map(add_cld_shdw_mask)
        #
        #    but normally we want only the resulting 'cloudmask'
        #
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .select('cloudmask')
                                                                 .updateMask(image.select('SCL').mask())))
        #
        #
        #
        #
        #    apply mode composite in case of overlapping images on same day
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="max", verbose=verbose)
        #
        #    add collection properties describing this collection (in this case: overwrites 'gee_description' from GEECol_s2scl)
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S2cloudlessmask')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        'S2 half tiles' (e.g. 31UES on '2020-01-29') have limited their footprint to the area 
        where data lives, thus *NOT* the full 31UES footprint
        when exporting masks [0,1] for these images, we'll indicate the unknown area with 255 as no data
        
          0: not masked (clear sky)
          1: masked     (belgian sky)
        255: no data    (belgian politics)
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(255, False)    # no data to 255
                                                                 .toUint8()))           # actually obsolete here
        return eeimagecollection


###############################################################################
#
# Sentinel 1 related products
#
###############################################################################

"""
"""
class GEECol_s1sigma0(GEECol, UserProjectable):

    def __init__(self, szband, szorbitpass):
        
        if not szband in ['VV', 'VH', 'HV', 'HH']:
            raise ValueError("band must be specified as one of 'VV', 'VH', 'HV', 'HH'")
        self.szband = szband

        if not szorbitpass in ['ASC', 'ASCENDING', 'DES', 'DESCENDING']:
            raise ValueError("orbitpass must be specified as one of 'ASCENDING'(or 'ASC'), 'DESCENDING'(or 'DES')")
        if szorbitpass == 'ASC': szorbitpass = 'ASCENDING'
        if szorbitpass == 'DES': szorbitpass = 'DESCENDING'
        self.szorbitpass = szorbitpass

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection - limited to single band & single orbit direction
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                             .filter(ee.Filter.eq('instrumentSwath', 'IW'))
                             .filter(ee.Filter.listContains('system:band_names', self.szband))
                             .filter(ee.Filter.eq('orbitProperties_pass', self.szorbitpass))
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    just the selected band
        #
        eeimagecollection = eeimagecollection.select([self.szband])
        #
        #    apply mosaic in case of multiple images in roi (on same day) since
        #    - I don't have a clue what is 'should' be (mean, median, ...?)
        #    - S1 images do not seem to overlap
        #    - so we only need this step for roi's at edges
        #    - worldcereal/worldcover has been using plain mosaic from start
        #    - and it doen't need the everlasting from-to-db
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="mosaic", verbose=verbose)
        #
        #    add collection properties describing this collection - S1, as always, being something special
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S1sigma0_' + self.szband + '_' + self.szorbitpass[0:3])
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        TODO: for the moment just toFloat() conversion
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .toFloat()))
        return eeimagecollection

    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        reproject the collection - for S1 we need to convert and reconvert from/to dB
        """
        def undodbprojredodb(image):
            return (ee.Image(10.0).pow(image.divide(10.0))
                    .reduceResolution(ee.Reducer.mean(), maxPixels=4096)
                    .reproject(eeprojection)
                    .log10().multiply(10.0)
                    .rename(image.bandNames()) # gotcha: eeimagecollection 2 bands: no problem, 1 band: name becomes 'constant': "The output bands are named for the longer of the two inputs, or if they're equal in length, in image1's order."
                    .copyProperties(image)
                    .copyProperties(image, ['system:id', 'system:time_start']))
        eeimagecollection = eeimagecollection.map(undodbprojredodb)

        return eeimagecollection


"""
"""
class GEECol_s1gamma0(GEECol_s1sigma0):

    def __init__(self, szband, szorbitpass):
        super().__init__(szband, szorbitpass)

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    can't use GEECol_s1sigma0.collect to convert sigma to gamma:
        #    problem is that we do need the 'angle' - will be dropped later
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                             .filter(ee.Filter.eq('instrumentSwath', 'IW'))
                             .filter(ee.Filter.listContains('system:band_names', self.szband))
                             .filter(ee.Filter.listContains('system:band_names','angle'))
                             .filter(ee.Filter.eq('orbitProperties_pass', self.szorbitpass))
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    gamma = f(sigma)
        #
        def sigme0dbtogamma0db(image):
            """
            gamma0 = sigma0 / cos(t)   with t in radians = angle(degrees) x pi / 180
            => 10 x log(gamma0) = 10 x log(sigma0) - 10 x log(cos(t))\
            => gamma0_db = sigma0_db - 10 x log(cos(t))
            """
            return (image.select(self.szband)
                    .subtract(image.select('angle').multiply(3.1415/180.0).cos().log10().multiply(10.))
                    .copyProperties(image)
                    .copyProperties(image, ['system:id', 'system:time_start']))
        eeimagecollection = eeimagecollection.map(sigme0dbtogamma0db)
        #
        #    apply plain mosaic in case of multiple images in roi (on same day)
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="mosaic", verbose=verbose)
        #
        #    add collection properties describing this collection - S1, as always, being something special
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S1gamma0_' + self.szband + '_' + self.szorbitpass[0:3])
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        TODO: for the moment just toFloat() conversion
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .toFloat()))
        return eeimagecollection


"""
"""
class GEECol_s1rvi(GEECol, OrdinalProjectable):
    """
    experimental - just for the fun of it (to play with S1_GRD_FLOAT collection)
    """

    def __init__(self, szorbitpass):
        
        if not szorbitpass in ['ASC', 'ASCENDING', 'DES', 'DESCENDING']:
            raise ValueError("orbitpass must be specified as one of 'ASCENDING'(or 'ASC'), 'DESCENDING'(or 'DES')")
        if szorbitpass == 'ASC': szorbitpass = 'ASCENDING'
        if szorbitpass == 'DES': szorbitpass = 'DESCENDING'
        self.szorbitpass = szorbitpass
        
    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection - using S1_GRD_FLOAT collection
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT')
                             .filter(ee.Filter.eq('instrumentSwath', 'IW'))
                             .filter(ee.Filter.listContains('system:band_names', 'VV'))
                             .filter(ee.Filter.listContains('system:band_names', 'VH'))
                             .filter(ee.Filter.eq('orbitProperties_pass', self.szorbitpass))
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    apply rvi = 4 x VH / (VV + VH)
        #
        def rvi(image):
            vv  = image.select('VV')
            vh  = image.select('VH')
            rvi = vh.multiply(4).divide(vh.add(vv))
            return ee.Image(rvi.rename('RVI').copyProperties(image, ['system:id', 'system:time_start']))
        eeimagecollection = eeimagecollection.map(rvi)
        #
        #    apply maximum composite in case of overlapping images on same day. TODO: is this ok?
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod="max", verbose=verbose)        
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S1rvi_' + self.szorbitpass[0:3])
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        TODO: for the moment just toFloat() conversion
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .toFloat()))
        return eeimagecollection


###############################################################################
#
# Proba V related products
#
###############################################################################

"""
"""
class PV333smfilter(geemask.IColFilter):
    """
    simple filter for ProbaV 333m collections, based on STATUS MASK band.
    default settings filter: minimum 5% pixels have STATUS MASK values 112, 120, 240 or 248
        0111 0000 : 112 Radiometric all but blue ok. sea.  clear sky.
        0111 1000 : 120 Radiometric all but blue ok. land. clear sky.
        1111 0000 : 240 Radiometric all ok.          sea.  clear sky. 
        1111 1000 : 248 Radiometric all ok.          land. clear sky. 

    typical use in the collect method of sentinel 2  products (GEECol daughter classes)
    """
    def __init__(self, classesarray=[112, 120, 240, 248], thresholdpct=5):
        """
        :param classesarray: list (python list, NOT ee.List) of the STATUS MASK values to be evaluated
        :param thresholdpct: the minimum (positive thresholds) or maximum (negative thresholds) percentage coverage by these values ( [0..100] )
        """
        self.filter = geemask.SimpleFilter('SM', classesarray, thresholdpct)

    def filtercollection(self, eeimagecollection, eeregion, verbose=False):
        """
        :param eeimagecollection: ProbaV 333m ee.ImageCollection to be filtered (MUST CONTAIN SM BAND)
        :param eeregion: region to be evaluated by the filter (would be nice if the eeimagecollection actually covers this region...)
        """
        if verbose: print(f"{str(type(self).__name__)}.filtercollection: input collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        eeimagecollection = self.filter.filtercollection(eeimagecollection, eeregion, verbose=verbose)
        if verbose: print(f"{str(type(self).__name__)}.filtercollection: resulting collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        return eeimagecollection


"""
"""
class GEECol_pv333ndvi(GEECol, OrdinalProjectable):
    """
    https://developers.google.com/earth-engine/datasets/catalog/VITO_PROBAV_C1_S1_TOC_333M
    """

    def __init__(self, colfilter=None):
        self.colfilter=colfilter
        if (colfilter is not None) and (not isinstance(colfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection
        #
        eeimagecollection = (ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M')
                             .select(['NIR', 'RED', 'SM'])                       # SM to allow STATUS MASK-based filters
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    (optional) filtering
        #
        if self.colfilter is not None:
            eeimagecollection = self.colfilter.filtercollection(eeimagecollection, eeroi, verbose=verbose)
        #
        #    apply ndvi = (nir-red)/(nir+red)
        #
        def ndvi(image):
            return ((image.select('NIR').subtract(image.select('RED'))).divide(image.select('NIR').add(image.select('RED')))
                    .rename('NDVI')
                    .copyProperties(image, ['system:id', 'system:time_start']))
        eeimagecollection = eeimagecollection.map(ndvi)
        #
        #    no sense in mosaicing: S1_TOC_333M is global
        #    however: geeutils.mosaictodate adds the 'gee_date' property which is mandatory in a GEECol
        #    TODO: check if nop-mosaic costs performance. if so add 'gee_date' without mosaicing
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod=None, verbose=verbose) # currently None defaults to "mosaic"       
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'PV333ndvi')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .clamp(-1,1)           # clamp looses properties 
                                                                 .toFloat()             # should be obsolete here, but side effect is no-data as -inf or nan iso 0
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection


"""
GEECol_pv333ndvi with historical vito ndvi scaling
"""
class GEECol_pv333ndvi_he(GEECol_pv333ndvi):

    def __init__(self, colfilter=None):
        super().__init__(colfilter)

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        return super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose).set('gee_description', 'PV333ndvi_he')

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        #
        #    historical vito ndvi scaling [ -0.08, 0.92 ] -> [0, 250] with 255 as no-data
        #
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .add(0.08).multiply(250).clamp(0,250)
                                                                 .unmask(255, False)
                                                                 .toUint8()
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection 


"""
"""
class GEECol_pv333sm(GEECol, CategoricalProjectable):
    """
    https://developers.google.com/earth-engine/datasets/catalog/VITO_PROBAV_C1_S1_TOC_333M#bands
    
    Bits 0-2: Cloud/ice snow/shadow flag    :  0: Clear  1: Shadow  2: Undefined  3: Cloud4: Ice
    Bit    3: Land/sea                      :  0: Sea    1: Land (pixels with this value may include areas of sea)
    Bit    4: Radiometric quality SWIR flag :  0: Bad    1: Good
    Bit    5: Radiometric quality NIR flag  :  0: Bad    1: Good
    Bit    6: Radiometric quality RED flag  :  0: Bad    1: Good
    Bit    7: Radiometric quality BLUE flag :  0: Bad    1: Good
    
    remark: this is a BIT coded mask. 
        we do use CategoricalProjectable (mode),
        but one might argue reprojecting should be done per-bit 
           
    """

    def __init__(self, colfilter=None):
        self.colfilter=colfilter
        if (colfilter is not None) and (not isinstance(colfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        #
        #    base collection
        #
        eeimagecollection = (ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M')
                             .select(['SM'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    (optional) filtering
        #
        if self.colfilter is not None:
            eeimagecollection = self.colfilter.filtercollection(eeimagecollection, eeroi, verbose=verbose)
        #
        #    no sense in mosaicing: S1_TOC_333M is global
        #    however: geeutils.mosaictodate adds the 'gee_date' property which is mandatory in a GEECol
        #    TODO: check if nop-mosaic costs performance. if so add 'gee_date' without mosaicing
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod=None, verbose=verbose) # currently None defaults to "mosaic"       
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'PV333sm')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(2, False) # mask to 00000010 - all bad, sea, undefined
                                                                 .toUint8()))
        return eeimagecollection


"""
"""
class GEECol_pv333simplemask(GEECol_pv333sm):
    """
    https://developers.google.com/earth-engine/datasets/catalog/VITO_PROBAV_C1_S1_TOC_333M#bands
    
    STATUS MASK band:
        Bits 0-2: Cloud/ice snow/shadow flag    :  0: Clear  1: Shadow  2: Undefined  3: Cloud4: Ice
        Bit    3: Land/sea                      :  0: Sea    1: Land (pixels with this value may include areas of sea)
        Bit    4: Radiometric quality SWIR flag :  0: Bad    1: Good
        Bit    5: Radiometric quality NIR flag  :  0: Bad    1: Good
        Bit    6: Radiometric quality RED flag  :  0: Bad    1: Good
        Bit    7: Radiometric quality BLUE flag :  0: Bad    1: Good

   geemask.SimpleMask: not masked (or clear) will be
        0111 0000 : 112 Radiometric all but blue ok. sea.  clear sky.
        0111 1000 : 120 Radiometric all but blue ok. land. clear sky.
        1111 0000 : 240 Radiometric all ok.          sea.  clear sky. 
        1111 1000 : 248 Radiometric all ok.          land. clear sky. 
           
    """

    def __init__(self, colfilter=None):
        super().__init__(colfilter)

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection from parent (SM)
        #
        eeimagecollection = super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose)
        #
        #
        #
        def simplemask(image):
            return (geemask.SimpleMask([112, 120, 240, 248])
                .makemask(image)
                .Not()
                .unmask(255, False)  # sameFootprint=False: otherwise missing beyond footprint becomes 0. TODO: what does this mean here (global images)
                .toUint8()           # uint8 [0:not masked, 1:masked], no data: 255
                .rename('MASK')
                .copyProperties(image, ['system:time_start', 'gee_date']))
        eeimagecollection = eeimagecollection.map(simplemask)
        #
        #    no mosaic/composite - already done in base collection - and was obsolete there, but for the 'gee_date' property
        #
        pass
        #
        #    add collection properties describing this collection (in this case: overwrites 'gee_description' from GEECol_pv333sm)
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'PV333smsimplemask')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
          0: not masked
          1: masked
        255: no data
        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .unmask(255, False)    # no data to 255
                                                                 .toUint8()))           # actually obsolete here
        return eeimagecollection


"""
"""
class GEECol_pv333rgb(GEECol, OrdinalProjectable):
    """
    experimental - just for the fun of it (to check where multiband images give problems)
                 - actually not rgb but a 'false color'
    
    https://developers.google.com/earth-engine/datasets/catalog/VITO_PROBAV_C1_S1_TOC_333M
    - doesn't bother to give minimum and maximum values of the bands
    
    https://proba-v.vgt.vito.be/sites/proba-v.vgt.vito.be/files/products_user_manual.pdf
    - reflectances:  scale: 2000 offset: 0 no-data: -1
    - PV = (DN - OFFSET) / SCALE
        
    """

    def __init__(self, colfilter=None):
        self.colfilter=colfilter
        if (colfilter is not None) and (not isinstance(colfilter, geemask.IColFilter) ) : raise ValueError("filter expected to be an IColFilter")

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):

        #
        #
        #       
        eeimagecollection = (ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M')
                             .select(['RED', 'NIR', 'BLUE', 'SM'])                       # SM to allow STATUS MASK-based filters
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    (optional) filtering - typically -but not mandatory- using an SCL based filter
        #
        if self.colfilter is not None:
            eeimagecollection = self.colfilter.filtercollection(eeimagecollection, eeroi, verbose=verbose)
        #
        #    drop SM band which was only included to allow STATUS MASK based filter
        #
        eeimagecollection = eeimagecollection.select(['RED', 'NIR', 'BLUE'])
        #
        #    no sense in mosaicing: S1_TOC_333M is global
        #    however: geeutils.mosaictodate adds the 'gee_date' property which is mandatory in a GEECol
        #    TODO: check if nop-mosaic costs performance. if so add 'gee_date' without mosaicing
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, szmethod=None, verbose=verbose)
        #
        #    add collection properties describing this collection
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'PV333rgb')
        #
        #
        #
        return eeimagecollection

    def scaleandflag(self, eeimagecollection, verbose=False):
        """
        PV products_user_manual:
        - reflectances:  scale: 2000 offset: 0 no-data: -1
        - PV = (DN - OFFSET) / SCALE

        we'll try to mimic Sentinel-2 TCI bands scaling
            'The TCI is an RGB image built from the B02 (Blue), B03 (Green), and B04 (Red) Bands. 
            The reflectances are coded between 1 and 255, 0 being reserved for 'No Data'. 

        """
        eeimagecollection = eeimagecollection.map(lambda image: (image
                                                                 .divide(2000).multiply(254).add(1)
                                                                 .unmask(0, False)
                                                                 .toUint8()
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
        return eeimagecollection



