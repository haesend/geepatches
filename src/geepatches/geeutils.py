
"""
some utilities and typical collections 
"""
import ee
if not ee.data._credentials: ee.Initialize()

import pathlib
import datetime
import multiprocessing
import time
import logging



#########################################################
#
#    test purposes
#
#########################################################


"""
some reference collections for test purposes
"""

#
#    base collections
#

"""
S1 Ground Range Detected (GRD)
https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD
"""
s1ImageCollection = ee.ImageCollection('COPERNICUS/S1_GRD')

"""
S2 Surface Reflectance
https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR
"""
s2ImageCollection = ee.ImageCollection('COPERNICUS/S2_SR')

"""
https://developers.google.com/earth-engine/datasets/catalog/VITO_PROBAV_C1_S1_TOC_100M
https://developers.google.com/earth-engine/datasets/catalog/VITO_PROBAV_C1_S1_TOC_333M

BEWARE:   ee.ImageCollection("VITO/PROBAV/C1/S1_TOC_100M") -> a lot of missing data (masked)

"""
pv100ImageCollection = ee.ImageCollection("VITO/PROBAV/C1/S1_TOC_100M")
pv333ImageCollection = ee.ImageCollection("VITO/PROBAV/C1/S1_TOC_333M")


"""
some sample (sub) collections for test purposes
"""
#
#    
# BEWARE:
#
#    s1&s2: tenzij geografisch beperkt (filterBounds) duren de meest operaties ontiegelijk lang.
#
#    s1rbgImageCollection: "did not match any bands." - 'VV', 'VH', 'angle' are not always there!
#        e.g. aggregate_histogram over one week (from '2018-05-26' on):
#            '[HH, HV, angle]' : 1366, 
#            '[HH, angle]'     : 396, 
#            '[VV, VH, angle]' : 5189, 
#            '[VV, angle]'     : 5
#
#    s2sclImageCollection and s2rgbImageCollection: some areas (e.g. tennvenlopoint) are covered in multiple tiles
#
#    pvrgbImageCollection: world cover (hence large) - especially for 100m more masked than data
#
s1rbgImageCollection    = (s1ImageCollection
                           .filter(ee.Filter.listContains('system:band_names','VV'))
                           .filter(ee.Filter.listContains('system:band_names','VH'))
                           .filter(ee.Filter.listContains('system:band_names','angle'))
                           .select(['VV', 'VH', 'angle']))                                  # False Color - not everywhere available
s2sclImageCollection    = s2ImageCollection.select(['SCL'])                                 #
s2rgbImageCollection    = s2ImageCollection.select(['B4', 'B3', 'B2'])                      #
pv100rgbImageCollection = pv100ImageCollection.select(['RED', 'NIR', 'BLUE'])               # False Color
pv333rgbImageCollection = pv333ImageCollection.select(['RED', 'NIR', 'BLUE'])               # False Color

"""
some visParams sets for geemap.Map.addLayer
"""
s2sclvisParams = { 'min':0, 'max':11, 'palette': [
                                        '#000000', # no_data
                                        '#ff0000', # saturated_or_defective
                                        '#404040', # dark_area_pixels
                                        '#833c0c', # cloud_shadows
                                        '#00ff00', # vegetation
                                        '#ffff00', # not_vegetated
                                        '#0000cc', # water
                                        '#757171', # unclassified
                                        '#aeaaaa', # cloud_medium_probability
                                        '#d0cece', # cloud_high_probability
                                        '#00ccff', # thin_cirrus
                                        '#ff66ff', # snow
                                        ]}
ndvivisParamsPalette = ['#000000',
                        '#a50026',
                        '#d73027',
                        '#f46d43',
                        '#fdae61',
                        '#fee08b',
                        '#ffffbf',
                        '#d9ef8b',
                        '#a6d96a',
                        '#66bd63',
                        '#1a9850',
                        '#006837']

faparvisParamsPalette = ['#a85000',
                         '#bd7c00',
                         '#d3a700',
                         '#e9d300',
                         '#ffff00',
                         '#c8de00',
                         '#91bd00',
                         '#5b9d00',
                         '#247c00',
                         '#336600',
                         '#d2d2d2']

"""
some famous points near lichtaart, mol and elsewhere for test purposes

    ee.Geometry.Point(coords, proj)
        coords: A list of two [x,y] coordinates in the given projection
        proj: optional projection -  EPSG:4326 if unspecified.
        e.g. ee.Geometry.Point(longitude, latitude)

https://latitudelongitude.org/
"""
bobspoint       = ee.Geometry.Point( 4.90782, 51.20069)  # our favorite spot at Lichtaart
hogerielenpoint = ee.Geometry.Point( 4.93741, 51.24179)  # where we live
tapspoint       = ee.Geometry.Point( 5.07924, 51.21848)  # where we work
pannekoekpoint  = ee.Geometry.Point( 5.16577, 51.23480)  # where there are pannekoeken
tennvenlopoint  = ee.Geometry.Point( 6.19947, 51.37140)  # special 4-S2-tile point (at the tennisclub in Venlo)
half31UESpoint  = ee.Geometry.Point( 3.56472, 50.83872)  # border of S2 31UES tile on 2020-01-29
hoogeheydepoint = ee.Geometry.Point( 4.91380, 51.20715)  # point near bobspoint, 2-S1-DESC tiles edge on 2018-07-25, 2-S1-ASC tiles on 2018-07-16
pastacosipoint  = ee.Geometry.Point( 3.98940, 50.49995)  # point somwhere around Mons, 2-S1-DESC tiles edge on 2018-02-24 (about 25% of observations in 2018)
brusselspoint   = ee.Geometry.Point( 4.34878, 50.85045)  # brussels
antwerppoint    = ee.Geometry.Point( 4.40346, 51.21989)  # antwerp
snauangard      = ee.Geometry.Point(10.15508, 63.37856)  # snauan gard norway
orenburgskaya   = ee.Geometry.Point(55.06687, 51.67971)  # klaverblad ergens in rusland (Orenburgskaya oblast)
taminspoint     = ee.Geometry.Point( 9.40632, 46.82809)  # Tamins, Switzerland near Sankt Moritz

fleecycloudsday = ee.Date('2018-07-12')                 # schapenwolkjes over Belgium
half31UESday    = ee.Date('2020-01-29')                 # S2 31UES only upper left containing data
hoogeheydeASCday= ee.Date('2018-07-16')                 # 2-S1-ASC  tiles edge @hoogeheydepoint
hoogeheydeDESday= ee.Date('2018-07-25')                 # 2-S1-DESC tiles edge @hoogeheydepoint
clearskyday     = ee.Date('2019-08-24')                 # nice day, at least in brussels, dessel and lichtaart


"""
some convenience functions to create test images
"""
def _ndvi(image, sznir, szred):
    """
    proba V and sentinel 2 ndvi
    """
    return ee.Image(((image.select(sznir).subtract(image.select(szred))).divide(image.select(sznir).add(image.select(szred)))
            .rename('NDVI')
            .copyProperties(image, ['system:id', 'system:time_start'])))

def _rvi(s1image):
    """
    sentinel 1 'Radar Vegetation index' 
    https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-1/radar_vegetation_index/
    """
    vv = ee.Image(10).pow(s1image.select('VV').divide(10)) # get rid of dB's
    vh = ee.Image(10).pow(s1image.select('VH').divide(10))
    return ee.Image((vh.multiply(4).divide(vh.add(vv))
            .rename('RVI')
            .copyProperties(s1image, ['system:id', 'system:time_start'])))

def someS2ndviImageNear(date, eepoint=None, verbose=False):
    return _ndvi(someImageNear(s2ImageCollection.select(['B4', 'B8']), date, eepoint, verbose=verbose),'B8','B4') # B4~Red B8~Nir
def somePV333ndviImageNear(date, eepoint=None, verbose=False):
    return _ndvi(someImageNear(pv333ImageCollection.select(['NIR', 'RED']), date, eepoint, verbose=verbose),'NIR','RED')
def someS1rviImageNear(date, eepoint=None, verbose=False):
    return _rvi(someImageNear(s1rbgImageCollection.select(['VV','VH']), date, eepoint, verbose=verbose)) # s1rbgImageCollection - guaranteed to contain both VV and VH


#########################################################
#
#    actual utilities
#
#########################################################

#
#    utility functions
#
def maskimageoutsidegeometry(eeimage, eegeometry):
    """
    geemask region outside the geometry
    """
    return eeimage.updateMask( (ee.Image(0).paint(ee.FeatureCollection(ee.Feature(eegeometry)), color=25)).eq(25) )


def maskimageinsidegeometry(eeimage, eegeometry):
    """
    geemask region inside the geometry
    """
    return eeimage.updateMask(((ee.Image(1).paint(ee.FeatureCollection(ee.Feature(eegeometry)), color=25)).eq(25)).Not())


def pixelcenterpoint(eepoint, eerefimage, verbose=False):
    """
    center point of the pixel in the reference image close to the eepoint

    BEWARE: eerefimage must have one single band, or all bands must have identical projections.
    """
    if verbose: print(f"{pathlib.Path(__file__).stem}:pixelcenterpoint  eepoint: {szgeometryinfo(eepoint)} \n\t eerefimage: {szprojectioninfo(eerefimage)}")
    #
    #    center of the sampled pixel in the image
    #    result in 'crs':'EPSG:4326', 'transform': [1, 0, 0, 0, 1, 0], 'nominalScale': 111319.49079327357
    #
    #    BEWARE: 'unmask' before 'sample': 'masked' pixels are not considered and give an empty geometry. nice.
    #
    #
    centerpoint = eerefimage.unmask().sample(region = eepoint, geometries = True).geometry()
    #
    #    transform back to its own projection
    #
    centerpoint = centerpoint.transform(eerefimage.projection())
    #
    #    in this projection, the coordinates should end *exactly* on .5
    #
    centerpointcoordinateslist = centerpoint.coordinates().map(lambda coord: ee.Number(coord).multiply(2).round().divide(2))
    #
    #    assemble the *exact* centerpoint
    #
    centerpoint = ee.Geometry.Point(centerpointcoordinateslist, proj=eerefimage.projection())
    if verbose: print(f"{pathlib.Path(__file__).stem}:pixelcenterpoint out {szgeometryinfo(centerpoint)}")
    #
    #
    #
    return centerpoint


def pixelinterspoint(eepoint, eerefimage, verbose=False):
    """
    intersection of pixels (raster) in the reference image close to the eepoint
    remark:
        this method does not give the 'nearest' intersection: scale(2, 2) will double the
        pixels in size, next the center of the result is used. these centers coincide (only) with
        the "odd" intersections in the original scale. hence the "even" intersections will never be used.
    BEWARE: eerefimage must have one single band, or all bands must have identical projections.
    """
    if verbose: print(f"{pathlib.Path(__file__).stem}:pixelinterspoint  eepoint: {szgeometryinfo(eepoint)} \n\t eerefimage: {szprojectioninfo(eerefimage)}")
    interspoint = (pixelcenterpoint(eepoint, eerefimage.reproject(eerefimage.projection().scale(2, 2)), verbose=verbose)
                   .transform(eerefimage.projection()))
    if verbose: print(f"{pathlib.Path(__file__).stem}:pixelinterspoint out: {szgeometryinfo(interspoint)}")
    return interspoint


def squareareaboundsroi(eepoint, metersradius, eeprojection=None, verbose=False):
    """
    'square' geometry (ee.geometry.Geometry) in the coordinate system of the specified eeprojection (may be ee.Image), 
    or defaulting to the eepoint.projection().
    
    ee.Point.buffer(distance, maxError, proj): 
     distance:  If no projection is specified, the unit is meters. Otherwise the unit is in the coordinate system of the projection.
     proj:      If specified, the buffering will be performed in this projection 
                and the distance will be interpreted as units of the coordinate system of this projection. 
                Otherwise the distance is interpreted as meters and the buffering is performed in a spherical coordinate system.

    ee.Geometry.bounds(maxError, proj)
     proj: If specified, the result will be in this projection. Otherwise it will be in WGS84.

    BEWARE: eerefimage can be used instead of eeprojection,
            but then the eerefimage must have one single band, 
            or all bands must have identical projections. (client could avoid problem with .select(0) - deliberately not done here).
            
            and whatever one thinks of, on pixel borders there will always be problems.
    """
    #
    #    get projection. default if needed
    #    if specified via eerefimage, keep the image for debug/verbose
    #
    eerefimage = None
    if isinstance(eeprojection, ee.Image):
        eerefimage   = eeprojection
        eeprojection = eeprojection.projection()

    if eeprojection is None:
        #
        # TODO: - better "ee.Projection('EPSG:4326')" ?
        #       - should we check/modify the transform ?
        #
        eeprojection = eepoint.projection()
    #
    #    (default) buffer around a point, "buffering in a spherical coordinate system"
    #        will look like a circle in mercators
    #        will look like a wide oval in epsg:4326
    #
    default_circle = eepoint.buffer(metersradius, maxError=0.001)
    #
    #    bounds returning the bounding box of this default_circle in the projection of the reference image  
    #        for s2 reference images: will look like a square in mercators
    #                                 will look like a tilted parallelogram in epsg:4326
    #        for pv reference images: will look like a tilted square in mercators
    #                                 will look like a rectangle in epsg:4326
    #
    #    maxError seems mandatory:
    #       " Geometry.bounds: Can't apply reprojection with edge subdivision with a zero error margin.
    #
    #    and we cannot make it arbitrary small:
    #        "ErrorMargin: Invalid ErrorMargin value: 1.0E-4. When units are 'meters', value must be either >= 0.001, or 0 to disallow any lossy reprojection.
    #    
    refproj_bounds = default_circle.bounds(maxError=0.001, proj=eeprojection)
    #
    #
    #
    if verbose:
        if eerefimage is None:
            print(f"{pathlib.Path(__file__).stem}:squareareaboundsroi({metersradius} meters radius) - area: {refproj_bounds.area(maxError=0.001).getInfo()}")
        else:
            #
            #    https://developers.google.com/earth-engine/guides/reducers_reduce_region#pixels-in-the-region
            #    "Unweighted reducers (e.g. ee.Reducer.count() or ee.Reducer.mean().unweighted()): 
            #    pixels are included if their centroid is in the region and the image's mask is non-zero."
            #
            pixelcount = eerefimage.select(0).unmask(sameFootprint=False).reduceRegion(ee.Reducer.count(), refproj_bounds)
            print(f"{pathlib.Path(__file__).stem}:squareareaboundsroi({metersradius} meters radius) - area: {refproj_bounds.area(maxError=0.001).getInfo()} - covering {pixelcount.getInfo()} pixels in ref image")
    #
    #
    #
    return refproj_bounds


def squarerasterboundsroi(eepoint, pixelsradius, eeprojection, verbose=False):
    """
    still expecting problems - why can I work without maxError here? TODO: check (e.g. would it work on ...mosaic().projection)

    BEWARE: eerefimage can be used instead of eeprojection,
            but then the eerefimage must have one single band, or all bands must have identical projections.
    """
    #
    #    get projection. ***no*** default
    #    if specified via eerefimage, keep it for debug/verbose
    #
    eerefimage = None
    if isinstance(eeprojection, ee.Image):
        eerefimage   = eeprojection.select(0)
        eeprojection = eeprojection.projection()
    #
    #    buffer around a point, "buffering will be performed in this (eerefimage) projection"
    #        for s2 reference images: will look like a circle in mercators
    #                                 will look like a wide oval in epsg:4326
    #        for pv reference images: will look like a tall oval in mercators
    #                                 will look like a circle in epsg:4326
    #
    refproj_circle = eepoint.buffer(pixelsradius, proj=eeprojection)
    #
    #    bounds returning the bounding box of this thing in the projection of the reference image  
    #        for s2 reference images: will look like a square in mercators
    #                                 will look like a wide tilted parallelogram in epsg:4326
    #        for pv reference images: will look like a tall tilted rectangle in mercators
    #                                 will look like a square in epsg:4326
    #
#        refproj_bounds = refproj_circle.bounds(maxError=ee.ErrorMargin(0.001, 'projected'), proj=eerefimage.projection())
#        refproj_bounds = refproj_circle.bounds(maxError=ee.ErrorMargin(0.001, 'projected'), proj=eerefimage.projection())
#        refproj_bounds = refproj_circle.bounds(maxError=1, proj=eerefimage.projection())
    refproj_bounds = refproj_circle.bounds(proj=eeprojection)
    #
    #
    #
    if verbose:
        if eerefimage is None:
            print(f"{pathlib.Path(__file__).stem}:squarerasterboundsroi({pixelsradius} pixels radius) - area: {refproj_bounds.area(maxError=0.001).getInfo()}")
        else:
            pixelcount = eerefimage.select(0).unmask(sameFootprint=False).reduceRegion(ee.Reducer.count(), refproj_bounds)
            print(f"{pathlib.Path(__file__).stem}:squarerasterboundsroi({pixelsradius} pixels radius) - area: {refproj_bounds.area(maxError=0.001).getInfo()} - covering {pixelcount.getInfo()} pixels in ref image")
    #
    #
    #
    return refproj_bounds


def mosaictodate(eeimagecollection, szmethod=None, verbose=False):
    """
    mosaic images of same date (day).
        composite type can be specified as one of 'mean', 'max', 'min', 'mode', 'median', 'first' (testpurposes) or 'mosaic' (default) 
        images are labeled with their (daily) date. per unique day, the images are mosaiced/composited with the specified method.

    ee.ImageCollection.mosaic():
        Composites all the images in a collection, using the mask.
        mosaic() composites overlapping images according to their order in the collection (last on top). 
        To control the source of pixels in a mosaic (or a composite), use image masks.

        this is no real composite; overlapping (but non masked) area's will get the value of one image.
        e.g. case where a geometry intersects multiple sentinel 2 tiles. crude.

    ee.ImageCollection.mode():
        Reduces an image by calculating the most common value at each pixel across the stack of all matching bands. Bands are matched by name.

    ee.ImageCollection.mean/median/max/min():
        Reduces an image by calculating the mean/median/max/min of all values at each pixel across the stack of all matching bands.

    ee.ImageCollection.first():
        Reduces an image by selecting the first of the collection. (mainly test purposes).

    BEWARE: (TODO: check if)
        result is unbounded (print(image.geometry().getInfo()) gives [[[-180, -90], [180, -90], [180, 90], [-180, 90], [-180, -90]]])
    """
    #
    #    return (empty) collection AS-IS to avoid weird ee.ee_exception.EEException-s 
    #    such as "Image.select: Parameter 'input' is required." later on.
    #
    if verbose:
        if eeimagecollection.size().getInfo() <= 0:
            #    beware: "mosaictodate takes a lot of time" - is partially due to this test
            #            since .getInfo() will force the collection to be evaluated
            #
            #    TODO: would using ee.Algorithms.If be significant faster? one server-client swap less?
            #
            if verbose: print(f"{pathlib.Path(__file__).stem}:mosaictodate ({szmethod}) empty input collection - return as-is")
            return eeimagecollection
        else:
            return _mosaictodate(eeimagecollection, szmethod=szmethod, verbose=True)
    #
    #    normal (non-verbose) case: no "eeimagecollection.size().getInfo()" which seems to cost a lot of time
    #
    return ee.ImageCollection(ee.Algorithms.If(
        ee.Number(eeimagecollection.size()).lte(0),
        eeimagecollection, 
        _mosaictodate(eeimagecollection, szmethod=szmethod, verbose=False)))

def _mosaictodate(eeimagecollection, szmethod=None, verbose=False):
    #
    #    szmethod's
    #
    def _mosaicdaily_method_mosaic(eeimagecollection): return eeimagecollection.mosaic()
    def _mosaicdaily_method_mean(eeimagecollection):   return eeimagecollection.mean()
    def _mosaicdaily_method_max(eeimagecollection):    return eeimagecollection.max()
    def _mosaicdaily_method_min(eeimagecollection):    return eeimagecollection.min()
    def _mosaicdaily_method_mode(eeimagecollection):   return eeimagecollection.mode()
    def _mosaicdaily_method_median(eeimagecollection): return eeimagecollection.median()
    def _mosaicdaily_method_first(eeimagecollection):  return eeimagecollection.first()
    #
    #
    #
    if szmethod is None: szmethod = "mosaic"
    
    if   szmethod == "mosaic": _method=_mosaicdaily_method_mosaic
    elif szmethod == "mean":   _method=_mosaicdaily_method_mean
    elif szmethod == "max":    _method=_mosaicdaily_method_max
    elif szmethod == "min":    _method=_mosaicdaily_method_min
    elif szmethod == "mode":   _method=_mosaicdaily_method_mode
    elif szmethod == "median": _method=_mosaicdaily_method_median
    elif szmethod == "first":  _method=_mosaicdaily_method_first
    else: 
        raise ValueError("szmethod must be specified as one of 'mosaic', 'mean', 'max', 'min', 'mode', 'median' or 'first'")

        #
        #    previous implementation. new implementation (below) seems marginally faster (and far more impressive using these 'join's :)
        #

        #
        # #
        # #    obsolete since split-up in mosaictodate and _mosaictodate
        # #
        # # #
        # # #
        # # #
        # # if eeimagecollection.size().getInfo() <= 0:
        # #     #
        # #     #    return empty collection as is to avoid weird ee.ee_exception.EEException-s 
        # #     #    such as "Image.select: Parameter 'input' is required." later on.
        # #     #
        # #     #    beware: "mosaictodate takes a lot of time" - is partially due to this test
        # #     #            since .getInfo() will force the collection to be evaluated
        # #     #
        # #     #    TODO: would using ee.Algorithms.If be significant faster? one server-client swap less?
        # #     #
        # #     if verbose: print(f"{pathlib.Path(__file__).stem}:mosaictodate ({szmethod}) empty input collection - return as-is")
        # #     return eeimagecollection
        #
        # #
        # #    sort: to be sure of a reproducible collection - add day-granular 'gee_date' as property ( format('YYYY-MM-dd') takes care of 'day-granularity')
        # #
        # eeimagecollection = eeimagecollection.map(lambda image: image.set('gee_date', ee.Date(image.date().format('YYYY-MM-dd')))).sort('system:time_start')
        # #
        # #    map-able list of distinct dates 
        # #
        # eelistdistinctdates = ee.List(eeimagecollection.distinct('gee_date').aggregate_array('gee_date'))
        # #
        # #    reference projection from earliest image in the collection - we might be at an UTM-border 
        # #    use first band to avoid problems in special case of multiband products with different resolutions(expected to be used for testcases only.)
        # #
        # eeprojectionreference = eeimagecollection.first().select(0).projection()
        #
        # if verbose: print(f"{pathlib.Path(__file__).stem}:mosaictodate ({szmethod}) input collection: \n{szimagecollectioninfo(eeimagecollection)}")
        #
        # def _mosaic(eedate):
        #     thisdate            = ee.Date(eedate)
        #     thisdatescollection = eeimagecollection.filter(ee.Filter.date(thisdate, thisdate.advance(1,'day')))
        #     thisdatesmosaic     = (_mosaicdaily_method_mosaic(thisdatescollection)
        #                            .reproject(eeprojectionreference)
        #                            .set('gee_date', thisdate.format('YYYY-MM-dd'))
        #                            .copyProperties(thisdatescollection.first(), ['system:time_start']))
        #     #
        #     # should we 'keep' properties from first image? could be nice for debugging, but is ambiguous
        #     #
        #     # .copyProperties(thisdatescollection.first())                                      # properties from first image
        #     # .copyProperties(thisdatescollection.first(), ['system:id', 'system:time_start'])) # including 'system:id' - ambiguous indeed
        #
        #     return thisdatesmosaic
        #
        # eeimagecollection = ee.ImageCollection(eelistdistinctdates.map(lambda eedate: _mosaic(eedate))).sort('system:time_start')
        #
        # if verbose: print(f"{pathlib.Path(__file__).stem}:mosaictodate ({szmethod}) result collection: \n{szimagecollectioninfo(eeimagecollection)}")
        #
        # return eeimagecollection

    #
    #    sort: to be sure of a reproducible collection - add day-granular 'gee_date' as property ( format('YYYY-MM-dd') takes care of 'day-granularity')
    #
    eeimagecollection = eeimagecollection.map(lambda image: image.set('gee_date', ee.Date(image.date()).format('YYYY-MM-dd'))).sort('system:time_start')
    #
    #    subset collection to images with distinct dates 
    #
    eeimagecollectiondistinctdates = eeimagecollection.distinct(['gee_date'])
    #
    #    add list of images with same dates as additional 'same_gee_date' property to these
    #
    eeimagecollectiondistinctdates = ee.Join.saveAll('same_gee_date').apply(**{
        'primary'  : eeimagecollectiondistinctdates,
        'secondary': eeimagecollection,
        'condition': ee.Filter.equals(**{'leftField': 'gee_date', 'rightField': 'gee_date'})})
    #
    #    reference projection from earliest image in the collection - we might even be at an UTM-border 
    #    use first band to avoid problems in special case of multiband products with different resolutions(expected to be used for testcases only.)
    #    todo: should we bring into account collections with unpredicatable bands (S1 'VV', 'VH', 'HV', 'HH' ...)
    #
    eeprojectionreference = eeimagecollection.first().select(0).projection()
    
    if verbose: print(f"{pathlib.Path(__file__).stem}:mosaictodate ({szmethod}) input collection: \n{szimagecollectioninfo(eeimagecollection)}")
    #
    #    actual mosaic
    #
    def _mosaic(eeimagedistinctdate):
        samegeedatecollection  = ee.ImageCollection.fromImages(eeimagedistinctdate.get('same_gee_date'))
        samegeedatemosaicimage = (_mosaicdaily_method_mosaic(samegeedatecollection)
                                  .reproject(eeprojectionreference)
                                  .copyProperties(eeimagedistinctdate, ['system:time_start', 'gee_date']))
        return samegeedatemosaicimage

    eeimagecollection = ee.ImageCollection(eeimagecollectiondistinctdates.map(_mosaic)).sort('system:time_start')

    if verbose: print(f"{pathlib.Path(__file__).stem}:mosaictodate ({szmethod}) result collection: \n{szimagecollectioninfo(eeimagecollection)}")
 
    return eeimagecollection

    
def stackcollectiontoimage(eeimagecollection, verbose=False):
    """
    stacks the images of a collection into a single multiband image
    the bands in the stacked image will be named by the original band names, 
    prefixed with the image date: 'YYYY-MM-dd_ORIGINALBANDNAME'
    
    BEWARE: 
    - this assumes maximum daily frequency
    - the 'system:time_start' property is available 

    PROBLEM: (2021-02-26)
        apparently depending on the length of the naming convention, the exported GeoTiff
        looses its band names (according to qgis and gdalinfo). nice.
        
            GEEProduct_S1tbd():
                Band 416: "20200229VH"                      416 bands ok, 418 not
                Band 410: "20200223VHG"                     410 bands ok, 412 not

            GEEProduct_PV333ndvi():
                Band 406: "20200210NDVI"                    406 bands ok, 407 not
                Band 368: "BAND_2020-01-03_NDVI"            368 bands ok, 369 not
                Band 330: "PV333ndvi_BAND_2019-11-26_NDVI"  330 bands ok, 331 not

        https://gis.stackexchange.com/questions/330708/define-layer-names-in-earth-engine-image-export/363458#363458
        'Earth Engine is exporting the band names properly.' very nice.
                
    TODO: - in case of single band images we could limit the name to yyyymmdd
          - somehow we'll be forced to implement some 'split' function
          - alternative would be to export metadata separately
    
    """
    def addimagebandstostack(nextimage, previousstack):
        def addbandnametolist(nextbandname, previouslist):
            newbandname = nextimage.date().format('YYYY-MM-dd').cat(ee.String("_")).cat(ee.String(nextbandname))
            return ee.List(previouslist).add(newbandname)
        newbandnameslist = nextimage.bandNames().iterate(addbandnametolist, ee.List([]))
        newimage = nextimage.rename(newbandnameslist)
        return ee.Image(previousstack).addBands(newimage)
    
    stackedimage = (eeimagecollection
                    .sort('system:time_start')
                    .iterate(addimagebandstostack, ee.Image(eeimagecollection.first()).select([])))

    if verbose: print(f"{pathlib.Path(__file__).stem}:stackcollectiontoimage:\n{szbandsinfo(stackedimage)}")
    
    return ee.Image(stackedimage)


def firstImageSince(eeimagecollection, date, eepoint=None, dateincluded=True, verbose=False):
    """
    select single image in collection covering the eepoint.: first since date specified (searches next year only)
    mainly for testpurposes
    BEWARE: eepoint is optional, if not specified, and
            in case the collection has not been filtered a priori by some geometry
            one never knows where in the world this 'first' image will be found,
            but there's a good chance it will not be where you're actually looking.
    """
    if eepoint is not None: eeimagecollection = eeimagecollection.filterBounds(eepoint)
    eedate  = ee.Date(date) if dateincluded else ee.Date(date).advance(1, 'day')
    eeimage = (eeimagecollection
               .filter(ee.Filter.date(eedate, eedate.advance(1, 'year')))
               .first())
    if verbose:
        if (eeimage.getInfo()): print(f"{pathlib.Path(__file__).stem}:firstImageSince {ee.Date(date).format('YYYY-MM-dd').getInfo()} (included: {dateincluded}): {eeimage.date().format('YYYY-MM-dd').getInfo()}")
        else                  : print(f"{pathlib.Path(__file__).stem}:firstImageSince {ee.Date(date).format('YYYY-MM-dd').getInfo()} (included: {dateincluded}): None found in following year")
    return eeimage


def lastImageBefore(eeimagecollection, date, eepoint=None, dateincluded=True, verbose=False):
    if eepoint is not None: eeimagecollection = eeimagecollection.filterBounds(eepoint)
    eedate  = ee.Date(date).advance(1, 'day') if dateincluded else ee.Date(date)
    eeimage = (eeimagecollection
               .filter(ee.Filter.date(eedate.advance(-1, 'year'), eedate))
               .sort('system:time_start', False)
               .first())
    if verbose:
        if (eeimage.getInfo()): print(f"{pathlib.Path(__file__).stem}:lastImageBefore {ee.Date(date).format('YYYY-MM-dd').getInfo()} (included: {dateincluded}): { eeimage.date().format('YYYY-MM-dd').getInfo()}")
        else                  : print(f"{pathlib.Path(__file__).stem}:lastImageBefore {ee.Date(date).format('YYYY-MM-dd').getInfo()} (included: {dateincluded}): None found in previous year")
    return eeimage


def someImageNear(eeimagecollection, date, eepoint=None, verbose=False):
    """
    temporal 'nearest' image in the collection covering the eepoint. 
    searches earliest image from eedate on, if none, searches backward.
    search is limited [-1 year, +1 year]
    
    BEWARE: eepoint is optional, in case the collection has not been filtered a priori by some geometry this can take forever
    TODO: discover decent workaround for ee.Algorithms.If
    """
    if eepoint is not None: eeimagecollection = eeimagecollection.filterBounds(eepoint)
    eeimage = firstImageSince(eeimagecollection, date)
    if not eeimage.getInfo() : eeimage = lastImageBefore(eeimagecollection, date) # check at client side: ee.Algorithms.If will always evaluate both branches 
    if verbose:
        if (eeimage.getInfo()): print(f"{pathlib.Path(__file__).stem}:someImageNear {ee.Date(date).format('YYYY-MM-dd').getInfo()}: { eeimage.date().format('YYYY-MM-dd').getInfo()}")
        else                  : print(f"{pathlib.Path(__file__).stem}:someImageNear {ee.Date(date).format('YYYY-MM-dd').getInfo()}: None found in [-1 year, +1 year] range")
    return eeimage


class Pulse(object):
    """
    simple shared variable object used to monitor long-running processes.
    - child process indicates it is alive by .pulse()
    - monitoring process can verify (and reset) this by .check()
    
    eg. 
        def endless(pulse):
            while True:
                do_some_work
                pulse.pulse()
        mypulse = Pulse()
        wrapasprocess(endless, args=(mypulse,), pulse=mypulse)
        
    """
    def __init__(self, verbose=True):
        self._verbose = verbose
        self._pulse   = multiprocessing.Value('i', 1)
        if self._verbose: print(f"{str(type(self).__name__)}")

    def pulse(self):
        self._pulse.value = 1
        if self._verbose: print(f"{str(type(self).__name__)}.pulse()")

    def check(self):
        value = self._pulse.value
        if self._verbose: print(f"{str(type(self).__name__)}.check({(value==True)})")
        if not value: return False
        self._pulse.value = 0
        return True


def wrapasprocess(func, args=(), kwargs={}, *, timeout=5, attempts=1, pulse=None, verbose=True):
    """
    execute a function in a child process, guard it with a timeout and allow for retries.
    the return value of the function (if any) itself is ignored, only the exitcode is evaluated and interpreted as
    == 0: no error, < 0: killed via some signal, > 0: some error  (Processes that raise an exception get an exitcode of 1).
    aim is not start multiple processes, but just to have some control over the launching of server tasks, accounting for 
    server downtime, hanging calls, overflowing task queue-s,... and own kemels.
    
    :param func: the target function to be wrapped - this function should use exit(returncode) retrurncode = 0:success, other: fail
    :param args: the argument tuple for the target invocation. Defaults to ()
    :param kwargs: a dictionary of keyword arguments for the target invocation. Defaults to {}
    :param timeout: timeout in seconds. Defaults to 5.
    :param attempts: maximum number of retries. Specify None for endless. Defaults to 1
    :param pulse: Pulse object shared with target function to indicate its sanity. Defaults to None
    :param verbose: print debug information if True. Defaults to False
    
    :return: True in case the target has exited, with return code 0, within the specified number of attempts, within the specified time. False otherwise.

    BEWARE: 
    - func must be top-level (avoid: 'Can't pickle local object' jokes).
    - "def main(): , if __name__ == '__main__': main()" idiom is a necessity, or import target from an other script.
    - be generous with timeout. a process needs time to start up. 'wrapasprocess' was thought to operate with timeouts in a magnitude of an hour.
    
    remarks: 
    - as my multithreading experiments (task queue & worker thead) crashed and burned, I'm lead to believe that gee is not threads-safe.
    - we can work around this by grouping all ee-server-side things in the same (single) thread, meaning other threads shoudn't even call getInfo().
    - being sick and tired of all "but not on Windows" threading issues, spawning a process might bring some peace and quiet.
    - decorators and multiprocessing don't go together well, hence no further 'decorators with parameters' attempts for me.
    - law of conservation of misery still holds.
    """
    if verbose:
        print(f"wrapasprocess:    func: {func}")
        for iIdx, arg in enumerate(args): print(f"        args {iIdx}: {str(arg)}")
        for key, value in kwargs.items(): print(f"        kwargs key {str(key)}: {str(value)}")
        print(f"        timeout : {timeout} seconds")
        print(f"        attempts: {attempts if attempts is not None else 'endless'}")
        print(f"        pulse   : {'specified' if pulse else 'None'}")
        print(f"        verbose : {verbose}")

    attempt   = 1
    continues = 0
    while True:
        if verbose: print(f"wrapasprocess: attempt {attempt} of {attempts if attempts is not None else 'endless'} {'starts' if continues==0 else ('continued (' + str(continues) + ' time(s))')} ")
        try:
            datetime_tick  = datetime.datetime.now()
            if continues == 0:
                process = multiprocessing.Process(target=func, args=args, kwargs=kwargs)
                process.start()
            #
            # wait for it
            #
            process.join(timeout)
            #
            # evaluate what is happening
            #
            if not process.is_alive():
                #
                # in time and not alive. most probably all went well, but might have been an exception
                #
                print(f"wrapasprocess: attempt {attempt} exitcode: {process.exitcode}")
                if 0 == process.exitcode:
                    #
                    # assuming success - exit
                    #
                    if verbose: print(f"wrapasprocess: attempt {attempt} SUCCESS with exitcode {process.exitcode} - in time, after {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")
                    return True # exit from endless (with 'True' - success)
                else:
                    #
                    # assume crash (we'll retry)
                    #
                    if verbose: print(f"wrapasprocess: attempt {attempt} FAILED with exitcode {process.exitcode} - in time, after {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")
                    pass # check retry
            else:
                #
                # still alive. might have timed out. return code expected to be 'None', but we'll ignore it anyway
                #
                if verbose: print(f"wrapasprocess: attempt {attempt} {'CHECKING' if pulse else 'FAILED - TIMED OUT'} after {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")
                #
                # in case a pulse was specified, we might continue without restart
                #
                if pulse:
                    if pulse.check():
                        if verbose: print(f"wrapasprocess: attempt {attempt} STILL PULSING - continue")
                        continues += 1
                        continue
                    else:
                        if verbose: print(f"wrapasprocess: attempt {attempt} NO PULSE DETECTED")
                        pass # kill and check retry
                #
                # 
                #
                process.kill() # yes, terminate should do. probably. in most cases. whatever.
                process.join()
                pass # check retry

        except Exception as e:
            # this shouldn't happen: it would be an exception from own internals, not from func which lived somewhere else 
            if verbose: print(f"wrapasprocess: attempt {attempt} FAILED on exception: {str(e)}")
            pass # check retry
        
        # check retry
        attempt  += 1
        if (attempts is not None) and (attempts < attempt):
            if verbose: print(f"wrapasprocess: attempt {attempt-1} FAILED - exits")
            return False # exit from endless (with 'False' - failed)
        # do retry
        if verbose: print(f"wrapasprocess: attempt {attempt-1} FAILED - retry")
        continues = 0


"""
wrapretry: 
    retry wrapped function in case an exception is thrown
    in 'this' implementation, targets functions containing ee-calls which occasionally fail due to hiccups, e.g.:
        "status code(500)"
        "Earth Engine capacity exceeded."
        "HTTPSConnectionPool(host='earthengine.googleapis.com', port=443): Max retries exceeded..."
        "Exception([Errno 101] Network is unreachable..."

NoRetryException: 
    base class for hierarchy of 'known' exception types for which retries are not relevant
    can be used in the wrapped function (hence function is assumed to 'know' it might be wrapped)
    in 'this' implementation, daughters focus on ee-specific problems (e.g. empty ee.ImageCollection's)
"""
class NoRetryException(Exception):                         pass
class NoRetryEmptyCollectionException(NoRetryException):   pass
class NoRetryNoImageException(NoRetryException):           pass
class NoRetryInvalidCollectionException(NoRetryException): pass

def wrapretry(func, args=(), kwargs={}, *, attempts=3, backoffseconds=10, backofffactor=1, verbose=False):
    """
    execute a function and allow for retries in case it throws an exception
    example:
        def foo(a, k=0, verbose=False):
            ...
            return res
        res = wrapretry(foo, args=(1,), kwargs={'k1':1, 'verbose':True), attempts=2, backoffseconds=60, verbose=True)
    
    :param func: the target function to be wrapped
    :param args: the argument tuple for the target invocation. Defaults to ()
    :param kwargs: a dictionary of keyword arguments for the target invocation. Defaults to {}
    :param attempts: maximum number of retries. Defaults to 3
    :param backoffseconds: backoff time before retry in seconds. Defaults to 10.
    :param backofffactor: increase backoff time for each attempt by multiplying previous value with backofffactor. Defaults to 1.
    :param verbose: print debug information if True. Defaults to False
    
    TODO: this could be painful for stupid errors which cannot recover anyway. perhaps we should implement some specific exception
          class indicating the retries can be stopped (StopIteration ?), but then the client should be aware of being wrapped.

    """
    if False:
        #
        #    debug only (actually: won't even work for json ComputedObject's)
        #
        print(f"wrapretry:        func: {func.__name__}")
        for iIdx, arg in enumerate(args): print(f"        args {iIdx}: {str(arg)}")
        for key, value in kwargs.items(): print(f"        kwargs key {str(key)}: {str(value)}")
        print(f"        attempts: {attempts}")
        print(f"        backoff : {backoffseconds}")
        print(f"        bofactor: {backofffactor}")
        print(f"        verbose : {verbose}")

    totalbackoffseconds = 0
    for attempt in range(1, attempts+1):
        if (attempt > 1):
            if verbose: print(f"wrapretry( {func.__name__} ) - sleep {backoffseconds} seconds before retry")
            time.sleep(backoffseconds)
            totalbackoffseconds += backoffseconds
            backoffseconds = backoffseconds*backofffactor

        try:
            if verbose: print(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} starts")
            result = func(*args, **kwargs)
            if verbose: print(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} SUCCESS (total backoff {totalbackoffseconds})")
            if (attempt > 1): logging.info(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} SUCCESS  (total backoff {totalbackoffseconds})")
            break
        except NoRetryException as e:
            #
            # our very own exception
            #
            if verbose: print(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds}) - re-raising NoRetryException({str(e)})")
            logging.error(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds}) - re-raising NoRetryException({str(e)})")
            raise
        except TypeError as e:
            #
            #    assuming there is no sense in retrying in case of TypeError: probably syntax fault in signature
            #
            if verbose: print(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds}) - re-raising TypeError({str(e)})")
            logging.error(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds}) - re-raising TypeError({str(e)})")
            raise
        except Exception as e:
            #
            #    might be more specific, but  where would it all end...
            #
            if verbose: print(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds})")
            logging.warning(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds}): Exception({str(e)})")
            last_exception = e

    else: # for - else (for loop did not 'break')
        if verbose: print(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds}) - re-raising last Exception({str(last_exception)})")
        logging.error(f"wrapretry( {func.__name__} ) - attempt {attempt} of {attempts} FAILED (total backoff {totalbackoffseconds}) - re-raising last Exception({str(last_exception)})")
        raise last_exception

    return result


#
#    debug functions
#
def szISO8601Date(date):
    return ee.Date(date).format('YYYY-MM-dd').getInfo()


def szimagecollectioninfo(eeimagecollection, verbose=True):
    """
    ee.ImageCollection.size()           is an ee.Number
    ee.ImageCollection.size().getInfo() is an int
    """
    sz  = ''

    if isinstance(eeimagecollection, ee.Image): 
        sz  = 'single image:'
        eeimagecollection = ee.ImageCollection(eeimagecollection)
    elif(isinstance(eeimagecollection, ee.ImageCollection)):
        sz  = 'image collection:'
    else:
        if verbose: print(f"{pathlib.Path(__file__).stem}:szimagecollectioninfo 'eeimagecollection' parameter invalid type ({type(eeimagecollection)})")

    try:
        imagecollectionsize = eeimagecollection.size().getInfo()
    except Exception as e:
        return f"Invalid collection ({str(e)})"
    
    if (imagecollectionsize <= 0): 
        sz += " size: 0. Empty collection. \n"
        return sz
    sz += f" size: {imagecollectionsize}"
    
    if eeimagecollection.first().get('system:time_start').getInfo() is None:
        sz += " from/till: 'system:time_start' not found - not date info available. \n"
    else:
        eeimagecollection = (eeimagecollection
                             .sort('system:time_start')
                             .map(lambda image: image.set('gee_date', ee.Date(image.date()).format('YYYY-MM-dd'))))
        sz += f" from: {eeimagecollection.limit(1, 'system:time_start', True).first().date().format('YYYY-MM-dd').getInfo()}"
        sz += f" till: {eeimagecollection.limit(1, 'system:time_start', False).first().date().format('YYYY-MM-dd').getInfo()}"
        sz += f" unique dates: {eeimagecollection.distinct('gee_date').size().getInfo()}"
        #sz += f"\n"

    
    if verbose:
#         #
#         #    server side: everlasting "ee.ee_exception.EEException: ...does not have a ... property" problems.
#         #
#         def iterimageinfo(currentiterationobject, previousreturnobject):
#             currentimage     = ee.Image(currentiterationobject)
#             newinfostring    = (ee.String(previousreturnobject)
#                                 .cat("    id:")
#                                 .cat(currentimage.id())
#                                 .cat(" date:")
#                                 .cat(currentimage.date().format('YYYY-MM-dd'))
#                                 .cat("\n"))
#             return newinfostring
#         sz += eeimagecollection.limit(10).iterate(iterimageinfo, ee.String('')).getInfo()
        maxfeaturestomention = 4
        for iIdx, featuredict in enumerate(eeimagecollection.limit(maxfeaturestomention).getInfo()['features']):
            #
            #    mind you: ee.image.id() gives only the last part of ee.image.get('id'...)
            #    e.g.: '20180712' vs 'VITO/PROBAV/C1/S1_TOC_333M/20180712'
            #
            sz += f"\n    feature({iIdx}) id({featuredict.get('id', '-')})"
        if maxfeaturestomention < imagecollectionsize:
            sz += f"\n    ... ({imagecollectionsize-maxfeaturestomention} more)"
            


    return sz


def szimagesperdateinfo(eeimagecollection):
    """
    count number of images per date in collection
    """
    #
    #    sort: to be sure of a reproducible collection - add day-granular 'gee_date' as property ( format('YYYY-MM-dd') takes care of 'day-granularity')
    #
    eeimagecollection = eeimagecollection.sort('system:time_start').map(lambda image: image.set('gee_date', ee.Date(image.date()).format('YYYY-MM-dd')))
    #
    #    map-able list of distinct dates 
    #
    eelistdistinctdates = ee.List(eeimagecollection.distinct('gee_date').aggregate_array('gee_date'))
    #
    #    iterator function to build string
    #    
    def addline(sznextdate, previousstring):
        count = eeimagecollection.filter(ee.Filter.date(ee.Date(sznextdate), ee.Date(sznextdate).advance(1,'day'))).size()
        return (ee.String(previousstring)
                .cat("date: ")
                .cat(ee.Date(sznextdate).format('YYYY-MM-dd'))
                .cat(" images: ")
                .cat(count.format("%d") )
                .cat("\n"))

    return eelistdistinctdates.iterate(addline, ee.String('')).getInfo()


def szprojectioninfo(eeproj):
    """
    """
    if isinstance(eeproj, ee.Image):
        #
        # ee.Image can have multiple bands with different projections
        #
        lenmaxszbandname = 0
        for bandname in eeproj.bandNames().getInfo():
            lenmaxszbandname = max(lenmaxszbandname, len(bandname))
        lenmaxszbandname += 1

        sz = ''
        for iIdx, bandname in enumerate(eeproj.bandNames().getInfo()):
            sz += f" band({iIdx:3d}) "
            sz += f"{bandname:{lenmaxszbandname}s}: "
            sz += szprojectioninfo(eeproj.select(iIdx).projection())
            sz += "\n"
        return sz[:-1]

    sz  = ''
    if  isinstance(eeproj, ee.Geometry): eeproj = eeproj.projection()
    sz += f" crs: {eeproj.crs().getInfo()}"
    sz += f" nominalScale: {eeproj.nominalScale().getInfo()}"
    sz += f" transform: {eeproj.getInfo()['transform']}" # sz += f" transform: {eeproj.transform().getInfo()}" anticipates non-affine transforms
    #sz += f"\n info: {eeproj.getInfo()}"
    return sz


def szbandsinfo(eeimage):
    """
    ee.Image.bandNames()           is an ee.List        
    ee.Image.bandNames().getInfo() is a list
    ee.Image.getInfo()             is a dict - keys(['type', 'bands', 'id', 'version', 'properties'])
    ee.Image.getInfo()['bands']    is a list
    ee.Image.getInfo()['bands'][0] is a dict - keys(['id', 'data_type', 'dimensions', 'crs', 'crs_transform'])
    """
    try:
        eeimage.getInfo()
    except Exception as e:
        return f"Invalid image ({str(e)})"
    
    sz  = ''
    for iIdx, banddict in enumerate(eeimage.getInfo()['bands']):
        sz += f"band({iIdx:3d}) "
        for key, value in banddict.items():
            sz += f"{key}: {value}  "
        sz +="\n"
    return sz


def szestimatevaluesinfo(eeimagecollection, verbose=True):
    """
    estimate the value ranges over the bands of the images in a collection
    'estimate' since we'll be using 
    - the scale of the projection of first band of the first image,
    - the geometry of the the first image, (works only for bounded images - prevent problem by clipping to a region)
    - let gee do its 'bestEffort' ("User memory limit exceeded.")
    - and the mystic 'tileScale' ("Output of image computation is too large")
    
    Beware:
    - "Output of image computation is too large"
    - "User memory limit exceeded."
    - "Provide 'geometry' parameter when aggregating over an unbounded image." - works only for bounded images
    - reducers giving "None", even for constant images: works only in case there is a relevant number of pixels
      in the (bounded) image (e.g. problems if bounds < nominalScale)
    - and with each new collection one tries, one can expect a brand new set of crashes.
    """
    if isinstance(eeimagecollection, ee.Image): eeimagecollection = ee.ImageCollection(eeimagecollection)

    try:
        imagecollectionsize = eeimagecollection.size().getInfo()
    except Exception as e:
        return f"Invalid collection ({str(e)})"
    
    if (imagecollectionsize <= 0): return 'Cannot estimate values: Empty collection.'
    #
    #   reduceRegion does not like unbounded geometries
    #
    eeimagecollection   = eeimagecollection.map(lambda image: image.set('isUnbounded', image.geometry().isUnbounded()))
    eeimagecollection   = eeimagecollection.filter(ee.Filter.eq('isUnbounded', False))
    imagecollectionsize = eeimagecollection.size().getInfo()
    if (imagecollectionsize <= 0): return 'Cannot estimate values: All images are unbounded.'
    #
    # yes. i should use combine. i know. go away. ik heb een banaan in mijn oor.
    #
    minovercollectionimage = eeimagecollection.reduce(ee.Reducer.min())
    maxovercollectionimage = eeimagecollection.reduce(ee.Reducer.max())
    meaovercollectionimage = eeimagecollection.reduce(ee.Reducer.mean())
    medovercollectionimage = eeimagecollection.reduce(ee.Reducer.median())

    minpixelvalue = minovercollectionimage.reduceRegion(
        ee.Reducer.min(),
        geometry=eeimagecollection.first().geometry(),
        scale=eeimagecollection.first().select(0).projection().nominalScale(), # heuristic which can go wrong: image < nominalScale
        bestEffort=True, tileScale=8)                                          # i don't know ook niet, Noel Gorelick does.
    maxpixelvalue = maxovercollectionimage.reduceRegion(
        ee.Reducer.max(), 
        geometry=eeimagecollection.first().geometry(),
        scale=eeimagecollection.first().select(0).projection().nominalScale(),
        bestEffort=True, tileScale=8)
    meapixelvalue = meaovercollectionimage.reduceRegion(
        ee.Reducer.mean(),
        geometry=eeimagecollection.first().geometry(),
        scale=eeimagecollection.first().select(0).projection().nominalScale(),
        bestEffort=True, tileScale=8)
    medpixelvalue = medovercollectionimage.reduceRegion(
        ee.Reducer.median(),                                      # median of medians is not really what one would expect, or mathematically sane,
        geometry=eeimagecollection.first().geometry(),            # but what the heck, it's called 'estimatevalues' is it not?
        scale=eeimagecollection.first().select(0).projection().nominalScale(),
        bestEffort=True, tileScale=8)

    lenmaxszbandname = 0    # would you believe it? 'minimum_2m_air_temperature' in 'ECMWF/ERA5/DAILY'
    for bandname in eeimagecollection.first().bandNames().getInfo():
        lenmaxszbandname = max(lenmaxszbandname, len(bandname))
    lenmaxszbandname += 1
    sz = 'estimate over collection'
    sz += szimagecollectioninfo(eeimagecollection, verbose=False)
    sz += "\n"
    for iIdx, bandname in enumerate(eeimagecollection.first().bandNames().getInfo()):
        xin = minpixelvalue.get(str(bandname)+'_min').getInfo()               # min and max are 'reserved built-in symbol'
        xax = maxpixelvalue.get(str(bandname)+'_max').getInfo()
        avg = meapixelvalue.get(str(bandname)+'_mean').getInfo()
        med = medpixelvalue.get(str(bandname)+'_median').getInfo()
        szmin = f"{xin:15f}" if xin is not None else f"{'none':15s}"          # Why do we bother, Fawlty?
        szmax = f"{xax:15f}" if xax is not None else f"{'none':15s}"
        szavg = f"{avg:15f}" if avg is not None else f"{'none':15s}"
        szmed = f"{med:15f}" if med is not None else f"{'none':15s}"
        sz += f"band({iIdx:3d}) "
        sz += f"{bandname:{lenmaxszbandname}s}: "
        sz += f" min: {szmin} "
        sz += f" max: {szmax} "
        sz += f" avg: {szavg} "
        sz += f" med: {szmed} "
        sz +="\n"
        
    return sz


def szgeometryinfo(eegeometry, verbose=True):
    """
    wip
    """
    if isinstance(eegeometry, ee.Image): eegeometry = eegeometry.geometry()
    sz  = ''
    sz += f" geometry type: {eegeometry.type().getInfo()}"
    #sz += f" - perimeter: {eegeometry.perimeter(maxError=0.001).getInfo()}"
    #sz += f" - area: {eegeometry.area(maxError=0.001).getInfo()}"
    #
    #    type(eegeometry.coordinates()) -> ee.List
    #
    if (eegeometry.type().getInfo() == "Point"):
        #
        #    type(eegeometry.coordinates()) -> ee.List
        #    type(eegeometry.coordinates().length()) -> ee.Number
        #    eegeometry.coordinates().length().getInfo() -> 2
        #
        sz += f"\n\t coord: {eegeometry.coordinates().getInfo()}"
    elif (eegeometry.type().getInfo() == "Polygon"):
        sz += f" - perimeter: {eegeometry.perimeter(maxError=0.001).getInfo()}"
        sz += f" - area: {eegeometry.area(maxError=0.001).getInfo()}"
        #
        #    type(eegeometry.coordinates()) -> ee.List
        #    type(eegeometry.coordinates().length()) -> ee.Number
        #    eegeometry.coordinates().length().getInfo() -> 1
        #    type(eegeometry.coordinates().get(0)) -> ee.ComputedObject
        #    type(eegeometry.coordinates().get(0).getInfo()) -> list
        #
        sz += f" - points: {len((eegeometry.coordinates().get(0).getInfo()))}"
        for iIdx in range(len(eegeometry.coordinates().get(0).getInfo())):
            sz += f"\n\t {iIdx}: {eegeometry.coordinates().get(0).getInfo()[iIdx]}"
        
    
    sz += f"\n\t crs: {eegeometry.projection().crs().getInfo()}"
    sz += f" nominalScale: {eegeometry.projection().nominalScale().getInfo()}"
    sz += f"\n\t transform: {eegeometry.projection().getInfo()['transform']}"
    return sz


def outlinegeometryimage(eegeometry, distanceinmeters=0, width=1):
    """
    outline a geometry for visualization in geemap
    
    example: map.addLayer(geeutils.outlinegeometryimage(eegeometry, 10 , 5), {'palette':'#ff0000'})
    """
    if isinstance(eegeometry, ee.Image): eegeometry = eegeometry.geometry() # which is not documented; belongs to invisible ee.Element.geometry()
    if width is None:
        eewidth = ee.Number(1) # without width, the thing gets filled
    else:
        eewidth = ee.Number(width)

    if distanceinmeters is None or 0 == distanceinmeters:
        return ee.Image().paint(ee.FeatureCollection(ee.Feature(eegeometry)), width=eewidth)

    return ee.Image().paint(
        ee.FeatureCollection(ee.Feature(eegeometry.buffer(ee.Number(distanceinmeters), ee.Number(distanceinmeters).divide(1000)))), 
        width=eewidth)


def maskoutsidegeometry(eegeometry, eeimage, distanceinmeters=0):
    """
    mask image outside geometry (same as clip?)

    beware: using distanceinmeters is ment for visualization only; 
            e.g. eegeometry.buffer(distanceinmeters) on a rectangle will round the corners of the original rectangle
    """
    if eeimage is None: eeimage = ee.Image(1)
    if distanceinmeters is not None and 0 != distanceinmeters: eegeometry = eegeometry.buffer(distanceinmeters)
    eefeature           = ee.Feature(eegeometry)
    eefeaturecollection = ee.FeatureCollection(eefeature)
    outsidemask         = ee.Image(0).paint(eefeaturecollection, 1, None)
    return eeimage.updateMask(outsidemask)


def maskinsidegeometry(eegeometry, eeimage, distanceinmeters=0):
    """
    mask image inside geometry
    """
    if eeimage is None: eeimage = ee.Image(1)
    if distanceinmeters is not None and 0 != distanceinmeters: eegeometry = eegeometry.buffer(distanceinmeters)
    eefeature           = ee.Feature(eegeometry)
    eefeaturecollection = ee.FeatureCollection(eefeature)
    insidemask          = ee.Image(1).paint(eefeaturecollection, 0, None)
    return eeimage.updateMask(insidemask)

