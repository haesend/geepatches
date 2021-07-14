#
#  
#
import ee
import geeutils
import geebiopar
import geemask


"""
"""
class IProjectable(object):
    """
    By default, Earth Engine performs nearest neighbor resampling by default during reprojection.
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
        reproject categorical collection - using mode
        
        remark: 
        - in case a categorical image is down sampled considerably, mode is a far better method than nearest neighbor
        - in case a categorical image is down sampled nominally, mode acts as a smoother, whereas nearest neighbor can introduce pixel shifts
        - bottom line: no silver bullet
        """
        if verbose: print(f"{str(type(self).__name__)}._reproject - using Reducer.mode() - {geeutils.szprojectioninfo(eeprojection)}")
        def reproject(image):
            return (image
                    .reduceResolution(ee.Reducer.mode(), maxPixels=4096)
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


"""
"""
class GEECol(object):
    """
    The 'GEECol' class represents specific ('product') collections of images. The class contains the information and algorithms
    needed to retrieve data from gee and calculate, convert... this data into the desired products for the specified region (roi).
    e.g. some ndvi-GEEProduct class should be able to collect the NIR and RED data for a specific sensor from gee,
    apply some normalizedDifference algorithm on this data.
    
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
        - add collection properties describing this collection
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
        """

        #
        #
        #
        if isinstance(refcollection, ee.ImageCollection):
            if verbose: print(f"{str(type(self).__name__)}.getcollection: reference collection specified as ee.ImageCollection")
            _eerefimagecollection = refcollection
        elif isinstance(refcollection, GEECol): 
            if verbose: print(f"{str(type(self).__name__)}.getcollection: reference collection specified as {str(type(refcollection).__name__)}")
            _eerefimagecollection = refcollection.collect(eepoint, eedatefrom, eedatetill, verbose=verbose)
        else:
            if verbose: print(f"{str(type(self).__name__)}.getcollection: no reference collection specified")
            _eerefimagecollection = self.collect(eepoint, eedatefrom, eedatetill, verbose=verbose)
        #
        # find reference image - assume single band, or all bands having identical projection
        #
        _eerefimage = geeutils.someImageNear(_eerefimagecollection, eedatefrom, eepoint)
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
        # find roi origin to translate to align pixel boundaries with reference roi
        #
        _eerefroiulx  = _eerefroi.coordinates().flatten().get(0)
        _eerefroiuly  = _eerefroi.coordinates().flatten().get(1)
        #
        # translate and scale reference projection
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
            print(f"{str(type(self).__name__)}.getcollection: destination collection is empty - bailing out")
            return None
        #
        # reproject it, to align pixel boundaries with reference roi
        #
        _eedstimagecollection = self._reproject(_eenatimagecollection, _eedstprojection, verbose=verbose)
        #
        # apply scaling, clipping, masking,... preparing the collection for export
        #
        if doscaleandflag:
            _eedstimagecollection = self.scaleandflag(_eedstimagecollection, verbose=verbose)
            if verbose: print(f"{str(type(self).__name__)}.getcollection: scaled collection: {geeutils.szimagecollectioninfo(_eedstimagecollection)}")
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
        # add collection properties (needed for export)
        #
        _eedstimagecollection = _eedstimagecollection.set('gee_refroi',     _eerefroi)
        _eedstimagecollection = _eedstimagecollection.set('gee_projection', _eedstprojection)
        #
        #
        #
        return _eedstimagecollection


"""
"""
class GEECol_s2ndvi(GEECol, OrdinalProjectable):

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        #
        #    base collection
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
                             .select(['B4', 'B8'])                               # B4~Red B8~Nir
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
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
                                                                 .toFloat()             # actually obsolete here
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))
#         #
#         #    historical vito ndvi scaling [ -0.08, 0.92 ] -> [0, 250] with 255 as no-data
#         #
#         eeimagecollection = eeimagecollection.map(lambda image: (image
#                                                                  .add(0.08).multiply(250).clamp(0,250)
#                                                                  .unmask(255, False)
#                                                                  .toUint8()
#                                                                  .copyProperties(image)
#                                                                  .copyProperties(image, ['system:time_start'])))
        return eeimagecollection
        

"""
"""
class GEECol_s2fapar(GEECol, OrdinalProjectable):

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        """
        """
        #
        #    base collection
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
                             .select(['B3', 'B4', 'B8'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
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
#         #
#         #    historical vito fapar scaling [ 0, 1 ] -> [0, 200] with 255 as no-data
#         #
#         eeimagecollection = eeimagecollection.map(lambda image: (image
#                                                                  .multiply(200).clamp(0,200)
#                                                                  .unmask(255, False)
#                                                                  .toUint8()
#                                                                  .copyProperties(image)
#                                                                  .copyProperties(image, ['system:time_start'])))
        return eeimagecollection


"""
"""
class GEECol_s2scl(GEECol, CategoricalProjectable):

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
class GEECol_s2sclconvmask(GEECol_s2scl):

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection: SCL from parent - already composited (daily) to avoid striping at overlaps
        #
        eeimagecollection = super().collect(eeroi, eedatefrom, eedatetill, verbose=verbose)
        #
        #
        #
        def convmask(image):
            return (geemask.ConvMask( [[2, 4, 5, 6, 7], [3, 8, 9, 10, 11]], [20*9, 20*101], [-0.057, 0.025] )
                    .makemask(image)
                    .unmask(255, False)  # sameFootprint=False: otherwise missing beyond footprint becomes 0
                    .toUint8()           # uint8 [0:not masked, 1:masked], no data: 255)
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

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):

#         eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
#                              .select(['B4', 'B3', 'B2'])
#                              .filterBounds(eeroi)
#                              .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    using the mystic TCI bands
        #       
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S2_SR')
                             .select(['TCI_R', 'TCI_G', 'TCI_B'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    apply median composite in case of overlapping images on same day
        #    could be refined (e.g. select value with max ndvi) but worldcover 
        #     uses median too, and this is just an experimental class anyway.
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
class GEECol_s1sigma0(GEECol, UserProjectable):

    def __init__(self, szband, szorbitpass):
        
        if not szband in ['VV', 'VH', 'HV', 'HH']:
            raise ValueError("band must be specified as one of 'VV', 'VH', 'HV', 'HH'")
        self.szband = szband

        if not szorbitpass in ['ASC', 'ASCENDING', 'DES', 'DESCENDING']:
            raise ValueError("band must be specified as one of 'ASCENDING'(or 'ASC'), 'DESCENDING'(or 'DES')")
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
        eeimagecollection = eeimagecollection.set('gee_description', 'S1sigma0_' + self.szorbitpass[0:3] + '_' + self.szband)
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
        eeimagecollection = eeimagecollection.set('gee_description', 'S1gamma0_' + self.szorbitpass[0:3] + '_' + self.szband)
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

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection - using S1_GRD_FLOAT collection
        #    TODO: limited to single orbit direction?
        #
        eeimagecollection = (ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT')
                             .filter(ee.Filter.eq('instrumentSwath', 'IW'))
                             .filter(ee.Filter.listContains('system:band_names', 'VV'))
                             .filter(ee.Filter.listContains('system:band_names', 'VH'))
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
        #    add collection properties describing this collection (TODO: limited to single orbit direction? -> modify description)
        #       
        eeimagecollection = eeimagecollection.set('gee_description', 'S1rvi')
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
class GEECol_pv333ndvi(GEECol, OrdinalProjectable):
    """
    https://developers.google.com/earth-engine/datasets/catalog/VITO_PROBAV_C1_S1_TOC_333M
    """

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):
        #
        #    base collection
        #
        eeimagecollection = (ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M')
                             .select(['NIR', 'RED'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
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
                                                                 .toFloat()             # actually obsolete here
                                                                 .copyProperties(image)
                                                                 .copyProperties(image, ['system:time_start'])))

#         #
#         #    historical vito ndvi scaling [ -0.08, 0.92 ] -> [0, 250] with 255 as no-data
#         #
#         eeimagecollection = eeimagecollection.map(lambda image: (image
#                                                                  .add(0.08).multiply(250).clamp(0,250)
#                                                                  .unmask(255, False)
#                                                                  .toUint8()
#                                                                  .copyProperties(image)
#                                                                  .copyProperties(image, ['system:time_start'])))
        
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

    def collect(self, eeroi, eedatefrom, eedatetill, verbose=False):

        #
        #
        #       
        eeimagecollection = (ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M')
                             .select(['RED', 'NIR', 'BLUE'])
                             .filterBounds(eeroi)
                             .filter(ee.Filter.date(eedatefrom, eedatetill)))
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




#
#    TODO: remove below
#
"""
"""
class GEEProduct(object):
    """
    The 'GEEProduct' class represents specific ('product') collections of images. The class contains the information and algorithms
    needed to retrieve data from gee and calculate, format, scale,... this data into the desired products.
    e.g. some ndvi-GEEProduct class should be able to collect the NIR and RED data for a specific sensor from gee,
    apply some normalizedDifference algorithm on this data and format/scale/clip/... the result into some format appropriate for export.
    
    until further notice we'll focus on single-band (output) products
    """

    def __init__(self, baseeeimagecollection, verbose=False):
        """
        products base class contains a 'baseeeimagecollection' which refers to a subset of an gee ImageCollection.
        this subset should filter the source collection as far as possible, but contain everything needed to calculate
        the actual product. e.g. for some ndvi-GEEProduct, the baseeeimagecollection should at least contain the NIR & RED bands.
        
        to allow for special cases in which this baseeeimagecollection cannot be specified in a simple 
        super().__init__(...) constructor, a setbasecollection method is available.
        
        :param baseeeimagecollection:ee.ImageCollection
        """
        self._baseeeimagecollection = baseeeimagecollection
        if verbose: print(f"{str(type(self).__name__)}.__init__")


    def basecollection(self):
        """
        """
        return self._baseeeimagecollection


    def setbasecollection(self, baseeeimagecollection):
        """
        hook to specify or modify existing collections without defining a new class.
        
        e.g. could be used for additional filtering as in 'limited s2-scl collection over a specific tile':
        prod = GEEProduct_S2scl()
        prod.setbasecollection(prod.basecollection().filter(ee.Filter.eq('MGRS_TILE', '31UFS')))

        :param baseeeimagecollection: ee.ImageCollection
        """
        self._baseeeimagecollection = baseeeimagecollection


    def _collect(self, eeimagecollection, verbose=False):
        """
        generic collect: *only for test purposes*.
        _collect 
        is to be implemented by the actual product classes.
        is expected to do some actual work: calculate, format, scale,... image collection data into the desired product.

        :param eeimagecollection: ee.ImageCollection being a filtered (temporal, spatial) subset of the basecollection
        :returns: ee.ImageCollection representing the resulting product data for the input eeimagecollection
        """
        if verbose: print(f"{str(type(self).__name__)}._collect (nop)")
        return (eeimagecollection)


    def _scaleandflag(self, eeimagecollection, verbose=False):
        """
        format the images in the collection to be exported.
        (expected to be called by getimagecollection(...) on the _collect result)

        :param eeimagecollection: ee.ImageCollection to be formatted.
        :returns: ee.ImageCollection representing the resulting data formatted to be exported to file.
        """
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag (default implementation: cast toFloat)")
        return (eeimagecollection
                .map(lambda image: image.toFloat()))
        
        
    def getimagecollection(self, eeregion, eeprojection, eedatefrom, eedatetill, doscaleandflag=True, verbose=False):
        """
        client interface of the GEEProduct class: prepare a bound, filtered and reprojected ee.ImageCollection for the product: 
        creates the product image collection for a specified region, over a specified tempaoral interval, in a specified crs:
        
            - restrict the basecollection (selected catalog, selected bands) to the specified region and date range
            - apply the (specific) _collect method for this product-s class which creates the actual product
            - mosaic the results to daily images (e.g. region can span multiple tiles with slightly different 'system:time_start')
            - optionally apply the scaling, casting, flagging to prepare the collection to be exported
            - reproject all to the specified output projection

        :param eeregion:       region of interest
        :param eeprojection:   desired crs - beware: hidden assumption is that this projection has a resolution <= native resolution
        :param eedatefrom:     start (earliest possible) date of series. 
        :param eedatetill:     end date (not included)
        :param doscaleandflag: reformat collection to be exported. use False if collection requires further processing (e.g. masking, compositing,...)
        
        """
        
        #
        #    limit base collection to roi and dates
        #
        eeimagecollection = (self.basecollection().filterBounds(eeregion).filter(ee.Filter.date(eedatefrom, eedatetill)))
        #
        #    remark: although we're using getInfo() here, it seems that it has little effect on overall (client-side) performance.
        #
        if (eeimagecollection.size().getInfo() <= 0) :
            print(f"{str(type(self).__name__)}.getimagecollection: empty collection - bailing out")
            return None
 
        if verbose: print(f"{str(type(self).__name__)}.getimagecollection: base collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        #
        #    collect specific output
        #
        eeimagecollection = self._collect(eeimagecollection, verbose=verbose)

        if verbose: print(f"{str(type(self).__name__)}.getimagecollection: product collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        #
        #    mosaic to daily
        #
        eeimagecollection = geeutils.mosaictodate(eeimagecollection, verbose=verbose)

        if verbose: print(f"{str(type(self).__name__)}.getimagecollection: mosaic collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        #
        #    reproject as specified
        #    - the product should inherit from IProjectable
        #    - in case it is a CategoricalProjectable, Reducer.median() is used
        #    - in case it is a OrdinalProjectable, Reducer.mean() is used
        #    - otherwise it is supposed to implement its own _reproject (e.g. S1 with its dB scale)
        #
        if eeprojection is not None: # condition just for test purposes. normal use *should* specify the projection
            eeimagecollection = self._reproject(eeimagecollection, eeprojection, verbose=verbose) 
        
            if verbose: print(f"{str(type(self).__name__)}.getimagecollection: reprojected collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
        #
        #    scale, clamp, cast, ... : format the collection to be exported
        #    
        #    in case this product will be exported to file, this is mandatory, otherwise masked areas
        #        will be exported as 0 (Export.image.toDrive) or -1 (Image.getDownloadUrl)
        #        regardless of its content (at least that is what we see now; ee version 0.1.248)
        #
        #    in most normal cases - the GEEProduct fully specified in its _collect - this should be done
        #
        #    in special cases this can be avoided or postponed. 
        #        e.g. when we want temporal max composite of an ndvi collection,
        #        in case no _scaleandmask was applied, this could be done straight forward by filtering 
        #        the collection into date ranges, and apply the max reducer (ee.ImageCollection.max())
        #        in case _scaleandmask was already applied, we'd first need undo all flagging (via updateMask(flagvalue)), 
        #        and re-apply unmask(flagvalue, True) again after the reduction.
        #
        if doscaleandflag:
            eeimagecollection = self._scaleandflag(eeimagecollection, verbose=verbose)

            if verbose: print(f"{str(type(self).__name__)}.getimagecollection: scaled and flagged collection: {geeutils.szimagecollectioninfo(eeimagecollection)}")
#         #
#         #    introduce masked area for test purposes
#         #
#         eeimagecollection=eeimagecollection.map(
#             lambda image: geeutils.maskimageinsidegeometry(image, eeregion.buffer(ee.Number(-20).multiply(eeprojection.nominalScale()))))
        #
        #
        #
        return eeimagecollection


# class GEEProduct_S1tbd(GEEProduct, IProjectable):
#     """
#     TBD
#     worldcereal:
#     - filter: 
#         instrumentSwath': 'IW'
#         'transmitterReceiverPolarisation': both VV' and 'VH'
#         orbitProperties_pass: 'ASCENDING', 'DESCENDING'
#     - remove 'black border' from old registrations
#     - daily aggregation
#     - 'gamma': .subtract(img.select('angle').multiply(3.1415/180.0).cos().log10().multiply(10.))
#     - reduce resolution: reduceResolution(ee.Reducer.mean() and reproject to 20 m
#     - scale and convert: multiply(10000), cast to int32
#     
#     
#     TODO:
#     - VV/VH only?
#     - togamma0 optional
#     - relativeOrbitNumber_start selection
#     """
#     def __init__(self, imagecollection, verbose=False):
#         super().__init__(imagecollection)
# 
#         if verbose: print(f"{str(type(self).__name__)}.__init__ {geeutils.szimagecollectioninfo(self._baseeeimagecollection, verbose=verbose)}")
# 
# 
#     def _collect(self, eeimagecollection, verbose=False):
#         """
#         """
#         if verbose: print(f"{str(type(self).__name__)}._collect (TBD)")
# 
#         #
#         #    BEWARE: here the angle gets dropped
#         #
#         def togamma0(image):
#             return (image.select(['VV', 'VH']).subtract(image.select('angle').multiply(3.1415/180.0).cos().log10().multiply(10.))
#                     .rename('VV', 'VH')
#                     .copyProperties(image)
#                     .copyProperties(image, ['system:id', 'system:time_start']))
#         
#         eeimagecollection = eeimagecollection.map(togamma0)
# 
#         if verbose: print( f"{str(type(self).__name__)}._collect - histo relativeOrbitNumber : {eeimagecollection.aggregate_histogram('relativeOrbitNumber_start').getInfo()}" )
# 
#         return eeimagecollection
# 
#     
#     def _reproject(self, eeimagecollection, eeprojection, verbose=False):
#         """
#         reproject the collection - for S1 we need to convert and reconvert from/to dB
#         """
#         if verbose: print(f"{str(type(self).__name__)}._reproject ({geeutils.szprojectioninfo(eeprojection)})")
# 
#         print (eeimagecollection.first().bandNames().getInfo())        
#         def undodbprojredodb(image):
#             return (ee.Image(10.0).pow(image.divide(10.0))
#                     .reduceResolution(ee.Reducer.mean(), maxPixels=4096)
#                     .reproject(eeprojection)
#                     .log10().multiply(10.0)
#                     .rename(image.bandNames()) # gotcha: eeimagecollection 2 bands: no problem, 1 band: name becomes 'constant': "The output bands are named for the longer of the two inputs, or if they're equal in length, in image1's order."
#                     .copyProperties(image)
#                     .copyProperties(image, ['system:id', 'system:time_start']))
#         
#         eeimagecollection = eeimagecollection.map(undodbprojredodb)
#         print (eeimagecollection.first().bandNames().getInfo())        
# 
#         return eeimagecollection
# 
#     
#     def _scaleandflag(self, eeimagecollection, verbose=False):
#         """
#         without scaling: qgis Float64 - Sixty four bit floating point
#         ee.Image.toFloat:     Float32 - Thirty two bit floating point
#         """
#         if verbose: print(f"{str(type(self).__name__)}._scaleandflag (TBD)")
#        
#         def scaleandflag(image):
#             return (image
#                     .multiply(10000)
#                     .toInt32()
#                     .copyProperties(image)                                        # multiply looses all properties
#                     .copyProperties(image, ['system:id', 'system:time_start']))
# 
#         eeimagecollection = eeimagecollection.map(scaleandflag)
# 
#         if verbose: print( f"{str(type(self).__name__)}._scaleandflag - histo relativeOrbitNumber : {eeimagecollection.aggregate_histogram('relativeOrbitNumber_start').getInfo()}" )
# 
#         return eeimagecollection
# 
# 
# class GEEProduct_S1Asce(GEEProduct_S1tbd):
#     def __init__(self, verbose=False):
#         super().__init__((ee.ImageCollection('COPERNICUS/S1_GRD')
#                       .filter(ee.Filter.eq('instrumentSwath', 'IW'))
#                       .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
#                       .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
#                       .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
#                       .select(['VV', 'VH', 'angle'])), verbose=verbose)
# 
# 
# class GEEProduct_S1Desc(GEEProduct_S1tbd):
#     def __init__(self, verbose=False):
#         super().__init__((ee.ImageCollection('COPERNICUS/S1_GRD')
#                       .filter(ee.Filter.eq('instrumentSwath', 'IW'))
#                       .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
#                       .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
#                       .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
#                       .select(['VV', 'VH', 'angle'])), verbose=verbose)

        
class GEEProduct_S1(GEEProduct, IProjectable):
    """
    """
    def __init__(self, verbose=False):
        super().__init__((ee.ImageCollection('COPERNICUS/S1_GRD')
                          .filter(ee.Filter.eq('instrumentSwath', 'IW'))), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._collect")

        #
        #    BEWARE: here the angle gets dropped
        #
        def togamma0(image):
            return (image.select(image.bandNames().remove('angle'))
                    .subtract(image.select('angle').multiply(3.1415/180.0).cos().log10().multiply(10.))
                    .rename(image.bandNames().remove('angle'))
                    .copyProperties(image)
                    .copyProperties(image, ['system:id', 'system:time_start']))
        
        eeimagecollection = eeimagecollection.map(togamma0)

        #
        #    hack metadata into band names
        #
        def renamebands(image):
            srcbandnames = image.bandNames()
            def renameband(bandname):
                return (ee.String(image.get('orbitProperties_pass')).slice(0,3)
                        .cat("_")
                        .cat(ee.Number(image.get('relativeOrbitNumber_start')).round().format("%03d"))
                        .cat("_")
                        .cat(ee.String(bandname)))
            dstbandnames = srcbandnames.map(renameband)
            return image.select(srcbandnames, dstbandnames)

        eeimagecollection = eeimagecollection.map(renamebands)

        #
        #
        #            
        return eeimagecollection

    
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        reproject the collection - for S1 we need to convert and reconvert from/to dB
        """
        if verbose: print(f"{str(type(self).__name__)}._reproject ({geeutils.szprojectioninfo(eeprojection)})")

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

    
    def _scaleandflag(self, eeimagecollection, verbose=False):
        """
        without scaling: qgis Float64 - Sixty four bit floating point
        ee.Image.toFloat:     Float32 - Thirty two bit floating point
        """
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag (TBD)")
       
#         def scaleandflag(image):
#             return (image
#                     .multiply(10000)
#                     .toInt32()
#                     .copyProperties(image)                                        # multiply looses all properties
#                     .copyProperties(image, ['system:id', 'system:time_start']))
        def scaleandflag(image):
            return image.toFloat()

        eeimagecollection = eeimagecollection.map(scaleandflag)

        return eeimagecollection        


class GEEProduct_S2scl(GEEProduct, CategoricalProjectable):
    """
    Sentinel 2 SCL band as-is
    remark: "S2 half tiles" (e.g. 31UES on '2020-01-29')
            have limited their footprint to the area where data lives, thus *NOT* the full 31UES footprint
            when exporting these images, we'll mask the empty area with 0 - being the SCENE CLASSIFICATION NO-DATA value

    scaling: none. scene classes: 0-11, no data: 0
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('COPERNICUS/S2_SR').select(['SCL']), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        if verbose: print(f"{str(type(self).__name__)}._collect (nop)")
        return eeimagecollection

    def _scaleandflag(self, eeimagecollection, verbose=False):
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag (uint8 scenes: 1-11, no data: 0)")
        return (eeimagecollection
                .map(lambda image: image.unmask(0, False).toUint8()))


class GEEProduct_S2sclconvmask(GEEProduct, CategoricalProjectable):
    """
    ConvMask on SCL band - TODO: params in __init__.
      0: not masked (clear sky)
      1: masked     (belgian sky)
    255: no data    (belgian politics)
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('COPERNICUS/S2_SR').select(['SCL']), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        if verbose: print(f"{str(type(self).__name__)}._collect (ConvMask on SCL band)")
        
        def convmask(image):
            return (geemask.ConvMask( [[2, 4, 5, 6, 7], [3, 8, 9, 10, 11]], [20*9, 20*101] ,[-0.057, 0.025] )
                    .makemask(image)
                    .rename('MASK')
                    .copyProperties(image, ['system:id', 'system:time_start']))

        return eeimagecollection.map(convmask)

    def _scaleandflag(self, eeimagecollection, verbose=False):
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag (uint8 [0:not masked, 1:masked], no data: 255)")
        return (eeimagecollection
                .map(lambda image: image.unmask(255, False).toUint8()))


class GEEProduct_S2ndvi(GEEProduct, OrdinalProjectable):
    """
    NDVI = (B8 - B4) / (B8 + B4)

    scaling as in Copernicus to https://land.copernicus.eu/global/products/NDVI
        min:    -0.08  (digital 0   - lower values are clipped to digital 0)
        max:     0.92  (digital 250 - higher values are clipped to digital 250)
        scale:   0.004
        offset: -0.08  (ndvi = offset + scale * digital)
        no data: 255
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('COPERNICUS/S2_SR').select(['B4', 'B8']), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._collect (calculate NDVI = (B8 - B4) / (B8 + B4))")

        def _ndvi(image):
            return ((image.select('B8').subtract(image.select('B4'))).divide(image.select('B8').add(image.select('B4')))
                    .rename('NDVI')
                    .copyProperties(image, ['system:id', 'system:time_start']))

        return eeimagecollection.map(_ndvi)

    def _scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag(uint8 0-250, no data: 255)")

        def scaleandflag(image):
            return (image
                    .add(0.08).multiply(250).clamp(0,250)
                    .unmask(255, False)
                    .toUint8()
                    .copyProperties(image, ['system:id', 'system:time_start']))

        return eeimagecollection.map(scaleandflag)


class GEEProduct_S2fapar(GEEProduct, OrdinalProjectable):
    """
    fapar NN in geebiopar - 3 bands implementation using bands B3, B4 and B8
    scaling
        min:     0     (digital 0   - lower values are clipped to digital 0)
        max:     1     (digital 200 - higher values are clipped to digital 200)
        scale:   0.005
        offset:  0     (fapar = offset + scale * digital)
        no data: 255
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('COPERNICUS/S2_SR').select(['B3', 'B4', 'B8']), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._collect (calculate fapar)")

        def _fapar(image):
            return (geebiopar.get_s2fapar3band(image)
                    .rename('FAPAR')
                    .copyProperties(image, ['system:id', 'system:time_start']))

        return eeimagecollection.map(_fapar)

    def _scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag(uint8 0-200, no data: 255)")
       
        def scaleandflag(image):
            return (image
                    .multiply(200).clamp(0,200)
                    .unmask(255, False)
                    .toUint8()
                    .copyProperties(image, ['system:id', 'system:time_start']))
            
        return eeimagecollection.map(scaleandflag)

       
class GEEProduct_PVndvi(GEEProduct, OrdinalProjectable):
    """
    NDVI = (NIR-RED)/(NIR+RED)
    scaling as in Copernicus to https://land.copernicus.eu/global/products/NDVI
        min:    -0.08  (digital 0   - lower values are clipped to digital 0)
        max:     0.92  (digital 250 - higher values are clipped to digital 250)
        scale:   0.004
        offset: -0.08  (ndvi = offset + scale * digital)
        no data: 255
    """
    def __init__(self, imagecollection, verbose=False):
        super().__init__(imagecollection.select(['NIR', 'RED']), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._collect (calculate NDVI = (NIR-RED)/(NIR+RED))")

        def ndvi(image):
            return ((image.select('NIR').subtract(image.select('RED'))).divide(image.select('NIR').add(image.select('RED')))
                    .rename('NDVI')
                    .copyProperties(image, ['system:id', 'system:time_start']))

        return eeimagecollection.map(ndvi)

    def _scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag(uint8 0-250, no data: 255)")
       
        def scaleandflag(image):
            return (image
                    .add(0.08).multiply(250).clamp(0,250)
                    .unmask(255, False)
                    .toUint8()
                    .copyProperties(image, ['system:id', 'system:time_start']))
            
        return eeimagecollection.map(scaleandflag)


class GEEProduct_PV100Mndvi(GEEProduct_PVndvi):
    """
    100M version
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_100M'), verbose=verbose)        


class GEEProduct_PV333Mndvi(GEEProduct_PVndvi):
    """
    300M version
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M'), verbose=verbose)

       
class GEEProduct_PVsm(GEEProduct, OrdinalProjectable):
    """
    Bits 0-2: Cloud/ice snow/shadow flag    :  0: Clear  1: Shadow  2: Undefined  3: Cloud4: Ice
    Bit    3: Land/sea                      :  0: Sea    1: Land (pixels with this value may include areas of sea)
    Bit    4: Radiometric quality SWIR flag :  0: Bad    1: Good
    Bit    5: Radiometric quality NIR flag  :  0: Bad    1: Good
    Bit    6: Radiometric quality RED flag  :  0: Bad    1: Good
    Bit    7: Radiometric quality BLUE flag :  0: Bad    1: Good
    """
    def __init__(self, imagecollection, verbose=False):
        super().__init__(imagecollection.select(['SM']), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._collect (nop)")
        return eeimagecollection

    def _scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag (GEE mask to 00000010 - all bad, sea, undefined)")
        return (eeimagecollection
                .map(lambda image: image.unmask(2, False).toUint8()))


class GEEProduct_PV100Msm(GEEProduct_PVsm):
    """
    100M version
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_100M'), verbose=verbose)        


class GEEProduct_PV333Msm(GEEProduct_PVsm):
    """
    300M version
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M'), verbose=verbose)

       
class GEEProduct_PVsmsimplemask(GEEProduct, CategoricalProjectable):
    """
    SM:
        Bits 0-2: Cloud/ice snow/shadow flag    :  0: Clear  1: Shadow  2: Undefined  3: Cloud4: Ice
        Bit    3: Land/sea                      :  0: Sea    1: Land (pixels with this value may include areas of sea)
        Bit    4: Radiometric quality SWIR flag :  0: Bad    1: Good
        Bit    5: Radiometric quality NIR flag  :  0: Bad    1: Good
        Bit    6: Radiometric quality RED flag  :  0: Bad    1: Good
        Bit    7: Radiometric quality BLUE flag :  0: Bad    1: Good
        
    MASK: not masked:
        0111 0000 : 112 Radiometric all but blue ok. sea.  clear sky.
        0111 1000 : 120 Radiometric all but blue ok. land. clear sky.
        1111 0000 : 240 Radiometric all ok.          sea.  clear sky. 
        1111 1000 : 248 Radiometric all ok.          land. clear sky. 
    """
    def __init__(self, imagecollection, verbose=False):
        super().__init__(imagecollection.select(['SM']), verbose=verbose)

    def _collect(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._collect (SimpleMask on PV SM)")
        def simplemask(image):
            return (geemask.SimpleMask([112, 120, 240, 248])
                    .makemask(image)
                    .Not()
                    .rename('MASK')
                    .copyProperties(image, ['system:id', 'system:time_start']))

        return eeimagecollection.map(simplemask)

    def _scaleandflag(self, eeimagecollection, verbose=False):
        """
        """
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag (uint8 [0:not masked, 1:masked], no data: 255)")
        return (eeimagecollection
                .map(lambda image: image.unmask(255, False).toUint8()))


class GEEProduct_PV100Msmsimplemask(GEEProduct_PVsmsimplemask):
    """
    100M version
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_100M'), verbose=verbose)        


class GEEProduct_PV333Msmsimplemask(GEEProduct_PVsmsimplemask):
    """
    300M version
    """
    def __init__(self, verbose=False):
        super().__init__(ee.ImageCollection('VITO/PROBAV/C1/S1_TOC_333M'), verbose=verbose)
