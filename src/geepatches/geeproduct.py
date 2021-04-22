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
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        depending on the nature of the (images in) the collection,
        reprojecting (to larger pixels) will be done by averaging (ordinal images),
        selecting the median (categorical images) or by a specific algorithm (e.g. log scaled images).

        TODO: check that these reductions reduce to nop in case native projection.nominalScale > target projection.nominalScale
        TODO: check that median uses existing values only
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
class CategoricalProjectable(IProjectable):
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        reproject categorical collection
        """
        if verbose: print(f"{str(type(self).__name__)}._reproject - using Reducer.median() - ({geeutils.szprojectioninfo(eeprojection)})")
        def reproject(image):
            return (image
                    .reduceResolution(ee.Reducer.median(), maxPixels=4096)
                    .reproject(eeprojection))
         
        eeimagecollection = eeimagecollection.map(reproject)
        return eeimagecollection


"""
"""
class OrdinalProjectable(IProjectable):
    def _reproject(self, eeimagecollection, eeprojection, verbose=False):
        """
        reproject ordinal collection
        """
        if verbose: print(f"{str(type(self).__name__)}._reproject - using Reducer.mean() - ({geeutils.szprojectioninfo(eeprojection)})")
        def reproject(image):
            return (image
                    .reduceResolution(ee.Reducer.mean(), maxPixels=4096)
                    .reproject(eeprojection))
         
        eeimagecollection = eeimagecollection.map(reproject)
        return eeimagecollection


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
        if verbose: print(f"{str(type(self).__name__)}._scaleandflag (default cast toFloat)")
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
