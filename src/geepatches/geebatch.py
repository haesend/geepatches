import os
import logging
import datetime
import random

import geopandas

import ee

import geeutils
import geeproduct
import geeexport



#
#
#
IAMRUNNINGONTHEMEP = False

#
#    available products
#
EXPORTABLEPRODUCTS = ["S2ndvi", "S2ndvi_he", "S2fapar", "S2fapar_he", "S2tcirgb",
                      "S2scl", "S2sclconvmask", "S2sclcombimask", "S2sclstaticsmask", "S2sclclassfractions",
                      "S2cloudlessmask",
                      "S1sigma0", "S1gamma0", "S1rvi",
                      "PV333ndvi", "PV333ndvi_he", "PV333sm", "PV333smsimplemask", "PV333rgb"]
#
#    available methods
#
EXPORTMETHODS = ["exportimages", "exportimagestack", "exportimagestodrive", "exportimagestacktodrive"]

#
#    sanity check products - playing with variable-length arguments
#
def saneproducts(*szproducts):
    assert (0 < len(szproducts)), "no product specified"                         # at least one product
    if (len(szproducts) == 1) and (isinstance(szproducts[0], (list, tuple))):    # unpack explicit lists or tuples
        szproducts = szproducts[0]
    saneproducts = []
    for szproduct in list(szproducts):                                           # only known products
        assert (szproduct in EXPORTABLEPRODUCTS), f"invalid product specified '{szproduct}'" 
        if szproduct not in saneproducts:                                        # no duplicates
            saneproducts.append(szproduct)
    return saneproducts

#
#    sanity check methods
#
def sanemethods(*szmethods):
    assert (0 < len(szmethods)), "no method specified"                         # at least one product
    if (len(szmethods) == 1) and (isinstance(szmethods[0], (list, tuple))):    # unpack explicit lists or tuples
        szmethods = szmethods[0]
    sanemethods = []
    for szmethod in list(szmethods):                                           # only known products
        assert (szmethod in EXPORTMETHODS), f"invalid method specified '{szmethod}'" 
        if szmethod not in sanemethods:                                        # no duplicates
            sanemethods.append(szmethod)
    return sanemethods

"""
demonstrater: exporter
    hosting all export methods
    configurable for a list of products, 
    specifies S2 20m (GEECol_s2scl()) as reference collection
    eexporting 1280m (64 pix) diameter roi's
"""
class GEEExporter():
    #
    #
    #
    def __init__(self, *szproducts, pulse=None):
        """
        e.g. exporter = GEEExporter("S2ndvi", "S1sigma0")
        """
        self.szproducts = saneproducts(*szproducts)
        self.pulse      = pulse
    #
    #
    #
    def _getgeecollections(self, eedatefrom, eedatetill, eepoint, verbose=False):
        """
        generator yielding collections for specified products
        """
        #
        #    using sentinel 2 20m as reference
        #
        refcol    = geeproduct.GEECol_s2scl()
        refcolpix = 256 #64  #128 #64
        #
        #    heuristics for other products
        #
        s2_20m_pix  = refcolpix
        s2_10m_pix  = 2 * s2_20m_pix
        s1_10m_pix  = s2_10m_pix
        pv333m_pix = int(s2_20m_pix*20/333) + 2
        #
        #    generator
        #
        if "S2ndvi"              in self.szproducts: yield geeproduct.GEECol_s2ndvi().getcollection(             eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2ndvi_he"           in self.szproducts: yield geeproduct.GEECol_s2ndvi_he().getcollection(          eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2fapar"             in self.szproducts: yield geeproduct.GEECol_s2fapar().getcollection(            eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2fapar_he"          in self.szproducts: yield geeproduct.GEECol_s2fapar_he().getcollection(         eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2scl"               in self.szproducts: yield geeproduct.GEECol_s2scl().getcollection(              eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2sclconvmask"       in self.szproducts: yield geeproduct.GEECol_s2sclconvmask().getcollection(      eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2sclcombimask"      in self.szproducts: yield geeproduct.GEECol_s2sclcombimask().getcollection(     eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
#        if "S2sclstaticsmask"  in self.szproducts: yield geeproduct.GEECol_s2sclstaticsmask().getcollection(   eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2sclstaticsmask"    in self.szproducts: 
            yield geeproduct.GEECol_s2sclstaticsmask(threshold=98,   thresholdunits="percentile").getcollection(   eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2sclstaticsmask"    in self.szproducts: 
            yield geeproduct.GEECol_s2sclstaticsmask(threshold=2.0,  thresholdunits="sigma").getcollection(   eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2sclclassfractions" in self.szproducts: yield geeproduct.GEECol_s2sclclassfractions().getcollection(    eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2cloudlessmask"     in self.szproducts: yield geeproduct.GEECol_s2cloudlessmask().getcollection(    eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)

        if "S2tcirgb"            in self.szproducts: yield geeproduct.GEECol_s2rgb().getcollection(              eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)

        if "S1sigma0"            in self.szproducts: yield geeproduct.GEECol_s1sigma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0"            in self.szproducts: yield geeproduct.GEECol_s1sigma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0"            in self.szproducts: yield geeproduct.GEECol_s1sigma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0"            in self.szproducts: yield geeproduct.GEECol_s1sigma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"            in self.szproducts: yield geeproduct.GEECol_s1gamma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"            in self.szproducts: yield geeproduct.GEECol_s1gamma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"            in self.szproducts: yield geeproduct.GEECol_s1gamma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"            in self.szproducts: yield geeproduct.GEECol_s1gamma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1rvi"               in self.szproducts: yield geeproduct.GEECol_s1rvi('ASC').getcollection(         eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1rvi"               in self.szproducts: yield geeproduct.GEECol_s1rvi('DES').getcollection(         eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
         
        if "PV333ndvi"           in self.szproducts: yield geeproduct.GEECol_pv333ndvi().getcollection(          eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333ndvi_he"        in self.szproducts: yield geeproduct.GEECol_pv333ndvi_he().getcollection(       eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333sm"             in self.szproducts: yield geeproduct.GEECol_pv333sm().getcollection(            eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333smsimplemask"   in self.szproducts: yield geeproduct.GEECol_pv333simplemask().getcollection(    eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333rgb"            in self.szproducts: yield geeproduct.GEECol_pv333rgb().getcollection(           eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)     

    #
    #    export methods
    #     
    def exportimages(self, eepoint, eedatefrom, eedatetill, szoutputdir, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimages(geecollection, szoutputdir, szfilenameprefix=szfilenameprefix, verbose=verbose)
            if self.pulse: self.pulse.pulse()
 
    def exportimagestack(self, eepoint, eedatefrom, eedatetill, szoutputdir, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimagestack(geecollection, szoutputdir, szfilenameprefix=szfilenameprefix, verbose=verbose)
            if self.pulse: self.pulse.pulse()
 
    def exportimagestodrive(self, eepoint, eedatefrom, eedatetill, szgdrivefolder, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimagestodrive(geecollection, szgdrivefolder, szfilenameprefix=szfilenameprefix, verbose=verbose)
            if self.pulse: self.pulse.pulse()
         
    def exportimagestacktodrive(self, eepoint, eedatefrom, eedatetill, szgdrivefolder, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimagestacktodrive(geecollection, szgdrivefolder, szfilenameprefix=szfilenameprefix, verbose=verbose)
            if self.pulse: self.pulse.pulse()


"""
demonstrator - including logging & furniture: simple export for single point
"""
def export_point(lstszproducts, lstszmethods, szdatefrom, szdatetill, pointlon, pointlat, szoutputdir, szgdrivedir=None, verbose=False):
    """
    e.g.: export_point(["S2ndvi", "S1sigma0"], "exportimages", "2019-01-01", "2020-01-01", 4.90782, 51.20069, r"C:\tmp")
    """
    if not ee.data._credentials: ee.Initialize()
    #
    #
    #
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #
    #
    #
    lstszproducts  = saneproducts(lstszproducts)
    lstszmethods   = sanemethods(lstszmethods)
    exporter       = GEEExporter(*lstszproducts)
    eedatefrom     = ee.Date(szdatefrom)
    eedatetill     = ee.Date(szdatetill)
    szyyyymmddfrom = eedatefrom.format('YYYYMMdd').getInfo()
    szyyyymmddtill = eedatetill.format('YYYYMMdd').getInfo()
    eepoint        = ee.Geometry.Point(pointlon, pointlat)
    szpointlon     = f"{eepoint.coordinates().get(0).getInfo():013.8f}"
    szpointlat     = f"{eepoint.coordinates().get(1).getInfo():013.8f}"
    szid           = f"Lon{szpointlon}_Lat{szpointlat}"
    #
    #    check output directory on system - at least log files will live here - e.g: C:\tmp\
    #
    if not os.path.isdir(szoutputdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")  # root must exist
    szoutputdir = os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3]}_points")              # append this scripts filename + _points
    if not os.path.isdir(szoutputdir) : 
        os.mkdir(szoutputdir)
        if not os.path.isdir(szoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
        os.chmod(szoutputdir, 0o777)
    #
    #     check google drive folder - default to script name
    #
    if szgdrivedir is None: szgdrivedir = f"{os.path.basename(__file__)[0:-3]}"
    #
    #    logging to file - e.g: C:\tmp\geebatch\geebatch_19990101_20000101.log 
    #
    szoutputbasename=os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3] + '_points_' + szyyyymmddfrom + '_' + szyyyymmddtill}")
    logfilehandler = logging.FileHandler(szoutputbasename + ".log")
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler) # (don't forget to remove it!)
    datetime_tick_all  = datetime.datetime.now()
    try:
        #
        #    initial log
        #
        logging.info(" ")
        logging.info(f"{os.path.basename(__file__)[0:-3]}")
        logging.info(f"    products:  {lstszproducts}")
        logging.info(f"    exports:   {lstszmethods}")
        logging.info(f"    point: (lon {szpointlon} lat {szpointlat})")
        logging.info(f"    from: {szyyyymmddfrom} till: {szyyyymmddtill}")
        logging.info(f"    output dir: {szoutputdir}")
        if ("exportimagestodrive" in lstszmethods or "exportimagestacktodrive" in lstszmethods):
            logging.info(f"    google drive folder: {szgdrivedir}")
        logging.info(" ")
        #
        #
        #
        if ("exportimages" in lstszmethods or "exportimagestack" in lstszmethods):
            #
            #    specific output directory per field e.g: C:\tmp\geebatch\0000280859BE7A17
            #
            szfieldoutputdir = os.path.join(szoutputdir, szid)
            if not os.path.isdir(szfieldoutputdir) : 
                os.mkdir(szfieldoutputdir)
                if not os.path.isdir(szfieldoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
                os.chmod(szfieldoutputdir, 0o777)
            if "exportimages"     in lstszmethods: exporter.exportimages(eepoint, eedatefrom, eedatetill, szfieldoutputdir, verbose=verbose)
            if "exportimagestack" in lstszmethods: exporter.exportimagestack(eepoint, eedatefrom, eedatetill, szfieldoutputdir, verbose=verbose)
        #
        #    toDrive will prepend the filenames with the fieldId
        #
        szfilenameprefix = str(szid) + "_"
        if "exportimagestodrive"     in lstszmethods: exporter.exportimagestodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, szfilenameprefix=szfilenameprefix, verbose=verbose)
        if "exportimagestacktodrive" in lstszmethods: exporter.exportimagestacktodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, szfilenameprefix=szfilenameprefix, verbose=verbose)


    finally:
        #
        #    remove handler we added at function start
        #
        logging.info(f"{os.path.basename(__file__)[0:-3]} export field {szid} done - {int((datetime.datetime.now()-datetime_tick_all).total_seconds())} seconds")
        logging.getLogger().removeHandler(logfilehandler)


"""
demonstrator - including logging & furniture: export for centroids of CropSAR-I field shapefiles
"""
def export_shape(lstszproducts, lstszmethods, szyyyyyear, szshapefile, szoutputdir, szgdrivedir=None, verbose=False):
    """
    e.g.: export_shape(["S2ndvi_he"], "exportimages", 2020, r"D:\data\ref\field_selection\test_fields_sample\2019_250testfields.shp", r"C:\tmp")
    """
    if not ee.data._credentials: ee.Initialize()
    #
    #
    #
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #
    #    assume per calendar year
    #
    szyyyymmddfrom   = str(int(szyyyyyear)    )  + "-01-01" 
    szyyyymmddtill   = str(int(szyyyyyear) + 1)  + "-01-01"
    #
    #    have pandas read the shapefile which is assumed to have fieldID
    #
    parcelsgeodataframe = geopandas.read_file(szshapefile, rows=2)
    parcelsgeodataframe.set_index( 'fieldID', inplace=True, verify_integrity=True) # throws KeyError if fieldID not available
    parcelsgeodataframe.to_crs(epsg=4326, inplace=True)
    numberofparcels = len(parcelsgeodataframe.index)
    icountparcels   = 0 # count (log) processed parcel
    #
    #    some output directory on system - at least log files will live here - e.g: C:\tmp\geebatch
    #
    if not os.path.isdir(szoutputdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")  # root must exist
    szoutputdir = os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3]}")                     # append this scripts filename
    if not os.path.isdir(szoutputdir) : 
        os.mkdir(szoutputdir)
        if not os.path.isdir(szoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
        os.chmod(szoutputdir, 0o777)
    #
    # check google drive folder - default to script name
    #
    if szgdrivedir is None: szgdrivedir = f"{os.path.basename(__file__)[0:-3]}"
    #
    #    check products and methods
    #
    lstszproducts = saneproducts(lstszproducts)
    lstszmethods  = sanemethods(lstszmethods)
    exporter      = GEEExporter(*lstszproducts)
    eedatefrom    = ee.Date(szyyyymmddfrom)
    eedatetill    = ee.Date(szyyyymmddtill)
    #
    #    logging to file - e.g: C:\tmp\geebatch\geebatch_19990101_20000101.log 
    #
    szoutputbasename=os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3] + '_' + szyyyymmddfrom + '_' + szyyyymmddtill}")
    logfilehandler = logging.FileHandler(szoutputbasename + ".log")
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler) # (don't forget to remove it!)
    datetime_tick_all  = datetime.datetime.now()
    try:
        #
        #    initial log
        #
        logging.info(" ")
        logging.info(f"{os.path.basename(__file__)[0:-3]}")
        logging.info(f"    products:  {lstszproducts}")
        logging.info(f"    exports:   {lstszmethods}")
        logging.info(f"    shapefile: {os.path.basename(szshapefile)}")
        logging.info(f"    from: {szyyyymmddfrom} till: {szyyyymmddtill}")
        logging.info(f"    parcels: {numberofparcels}")
        logging.info(f"    output dir: {szoutputdir}")
        if ("exportimagestodrive" in lstszmethods or "exportimagestacktodrive" in lstszmethods):
            logging.info(f"    google drive folder: {szgdrivedir}")
        logging.info(" ")
        #
        #    get circus on the road
        #
        doskip   = False # hack in case we were interrupted

        for fieldId, field in parcelsgeodataframe.iterrows():
            #
            #    hack in case we were interrupted - continue after fieldId
            #
            if doskip :
                print( "skipping " + fieldId)
                if fieldId == "000028085AF2E0B9":
                    doskip = False # last fieldId skipped
                continue

            datetime_tick = datetime.datetime.now()
            icountparcels += 1
            #
            #
            #
            #if (icountparcels > 1): return # debug
            #
            #
            #
            shapelygeometry = field['geometry']
            shapelypoint    = shapelygeometry.centroid
            eepoint         = ee.Geometry.Point(shapelypoint.x, shapelypoint.y)
            #
            #
            #
            if ("exportimages" in lstszmethods or "exportimagestack" in lstszmethods):
                #
                #    specific output directory per field e.g: C:\tmp\geebatch\0000280859BE7A17
                #
                szfieldoutputdir = os.path.join(szoutputdir, fieldId)
                if not os.path.isdir(szfieldoutputdir) : 
                    os.mkdir(szfieldoutputdir)
                    if not os.path.isdir(szfieldoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
                    os.chmod(szfieldoutputdir, 0o777)
                if "exportimages"     in lstszmethods: exporter.exportimages(eepoint, eedatefrom, eedatetill, szfieldoutputdir, verbose=verbose)
                if "exportimagestack" in lstszmethods: exporter.exportimagestack(eepoint, eedatefrom, eedatetill, szfieldoutputdir, verbose=verbose)
            #
            #    toDrive will prepend the filenames with the fieldId
            #
            szfilenameprefix = str(fieldId) + "_"
            if "exportimagestodrive"     in lstszmethods: exporter.exportimagestodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, szfilenameprefix=szfilenameprefix, verbose=verbose)
            if "exportimagestacktodrive" in lstszmethods: exporter.exportimagestacktodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, szfilenameprefix=szfilenameprefix, verbose=verbose)

            logging.info(f"export field {fieldId} ({icountparcels} of {numberofparcels}) done - {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")

    finally:
        #
        #    remove handler we added at function start
        #
        logging.info(f"{os.path.basename(__file__)[0:-3]} run ({icountparcels} of {numberofparcels}) parcels - {int( (datetime.datetime.now()-datetime_tick_all).total_seconds()/6/6)/100} hours")
        logging.getLogger().removeHandler(logfilehandler)



"""
demonstrator - including logging & furniture: export random points - only exportimages method supported

    uses 'COPERNICUS/Landcover/100m/Proba-V-C3/Global' 'discrete_classification' band
    - https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global
    - discarding Unknown, Snow and ice, Permanent water bodies, Oceans, seas.
    - results grouped per land-use in subdirectories

    - discrete_classification Class Table:
        
        Value    Color    Description
        0      282828    Unknown. No or not enough satellite data available.
        20     FFBB22    Shrubs. Woody perennial plants with persistent and woody stems and without any defined main stem being less than 5 m tall. The shrub foliage can be either evergreen or deciduous.
        30     FFFF4C    Herbaceous vegetation. Plants without persistent stem or shoots above ground and lacking definite firm structure. Tree and shrub cover is less than 10 %.
        40     F096FF    Cultivated and managed vegetation / agriculture. Lands covered with temporary crops followed by harvest and a bare soil period (e.g., single and multiple cropping systems). Note that perennial woody crops will be classified as the appropriate forest or shrub land cover type.
        50     FA0000    Urban / built up. Land covered by buildings and other man-made structures.
        60     B4B4B4    Bare / sparse vegetation. Lands with exposed soil, sand, or rocks and never has more than 10 % vegetated cover during any time of the year.
        70     F0F0F0    Snow and ice. Lands under snow or ice cover throughout the year.
        80     0032C8    Permanent water bodies. Lakes, reservoirs, and rivers. Can be either fresh or salt-water bodies.
        90     0096A0    Herbaceous wetland. Lands with a permanent mixture of water and herbaceous or woody vegetation. The vegetation can be present in either salt, brackish, or fresh water.
        100    FAE6A0    Moss and lichen.
        111    58481F    Closed forest, evergreen needle leaf. Tree canopy >70 %, almost all needle leaf trees remain green all year. Canopy is never without green foliage.
        112    009900    Closed forest, evergreen broad leaf. Tree canopy >70 %, almost all broadleaf trees remain green year round. Canopy is never without green foliage.
        113    70663E    Closed forest, deciduous needle leaf. Tree canopy >70 %, consists of seasonal needle leaf tree communities with an annual cycle of leaf-on and leaf-off periods.
        114    00CC00    Closed forest, deciduous broad leaf. Tree canopy >70 %, consists of seasonal broadleaf tree communities with an annual cycle of leaf-on and leaf-off periods.
        115    4E751F    Closed forest, mixed.
        116    007800    Closed forest, not matching any of the other definitions.
        121    666000    Open forest, evergreen needle leaf. Top layer- trees 15-70 % and second layer- mixed of shrubs and grassland, almost all needle leaf trees remain green all year. Canopy is never without green foliage.
        122    8DB400    Open forest, evergreen broad leaf. Top layer- trees 15-70 % and second layer- mixed of shrubs and grassland, almost all broadleaf trees remain green year round. Canopy is never without green foliage.
        123    8D7400    Open forest, deciduous needle leaf. Top layer- trees 15-70 % and second layer- mixed of shrubs and grassland, consists of seasonal needle leaf tree communities with an annual cycle of leaf-on and leaf-off periods.
        124    A0DC00    Open forest, deciduous broad leaf. Top layer- trees 15-70 % and second layer- mixed of shrubs and grassland, consists of seasonal broadleaf tree communities with an annual cycle of leaf-on and leaf-off periods.
        125    929900    Open forest, mixed.
        126    648C00    Open forest, not matching any of the other definitions.
        200    000080    Oceans, seas. Can be either fresh or salt-water bodies.

"""
def export_random_points(lstszproducts, szyyyyyear, szoutputdir, pulse=None, verbose=False):
    """
    TODO: shouldn't we move our Landcover checks into this generator?
    """
    def _newrandompointsgenerator(count=None, verbose=False):
        while True:
            #
            #
            #
            if count is not None:
                count -= 1
                if count <= 0: return 
            #
            # assume global samples
            #
            longitude  = (1 - random.random())*360. - 180.
            latitude   = random.uniform(-80,80)
            eepoint    = ee.Geometry.Point(longitude, latitude)
    
            pointlon   = float(f"{eepoint.coordinates().get(0).getInfo():013.8f}")
            pointlat   = float(f"{eepoint.coordinates().get(1).getInfo():013.8f}")
            eepoint    = ee.Geometry.Point(pointlon, pointlat)
    
            if verbose: print(f"{os.path.basename(__file__)[0:-3]}: _newrandompointsgenerator: yield Point({pointlon:013.8f}, {pointlat:013.8f})")
            yield eepoint
    #
    #    
    #
    _export_random_points(lstszproducts, szyyyyyear, szoutputdir, _newrandompointsgenerator(count=None, verbose=verbose), pulse=pulse, verbose=verbose)


def export_existing_points(lstszproducts, szyyyyyear, szrootoutputdir, pulse=None, verbose=False):
    """
    q&d solution to revisit existing 'random' points to add products
    """
    def _oldrandompointsgenerator(szrootoutputdir, verbose=False):
        verbose = True
        #
        # expect 'client' root directory
        #
        if not os.path.isdir(szrootoutputdir) : raise ValueError(f"invalid szrootoutputdir ({str(szrootoutputdir)})")  # root must exist
        #
        # expect 'suite' directory in this root directory
        #
        szoutputdir = os.path.join(szrootoutputdir, f"{os.path.basename(__file__)[0:-3]}_points")                      # append this scripts filename + _points
        if not os.path.isdir(szoutputdir)     : raise ValueError(f"invalid szoutputdir ({str(szrootoutputdir)})")      # outputdir must exist
        #
        # expect one (1) level of sub-directories for landuse: f"PV100LC_{landuseclass}"
        #
        for landuseEntry in os.scandir(szoutputdir):
            if not landuseEntry.is_dir(): continue           # ignore non-dir entries here (e.g. logfiles)
            #
            # expect point-sub-directories here: f"Lon{szpointlon}_Lat{szpointlat}"
            #
            for pointEntry in os.scandir(landuseEntry):
                if not pointEntry.is_dir(): continue         # ignore non-dir entries here (e.g. logfiles)
                #
                # q&d check and decode - expect LonXXXX.XXXXXXXX_LatXXXX.XXXXXXXX
                #
                if not len(pointEntry.name) == 33:      continue
                if not pointEntry.name[ 0: 3] == 'Lon': continue  
                if not pointEntry.name[17:20] == 'Lat': continue
                try:
                    pointlon = float(pointEntry.name[ 3:16])
                    pointlat = float(pointEntry.name[20:33])
                except:
                    continue
                #
                # here you go
                #
                eepoint = ee.Geometry.Point(pointlon, pointlat)
                if verbose: print(f"{os.path.basename(__file__)[0:-3]}: _oldrandompointsgenerator: yield Point({pointlon:013.8f}, {pointlat:013.8f}) at {pointEntry.path}")
                yield eepoint
    #
    #
    #    
    _export_random_points(lstszproducts, szyyyyyear, szrootoutputdir, _oldrandompointsgenerator(szrootoutputdir, verbose), pulse=pulse, verbose=verbose)


def _export_random_points(lstszproducts, szyyyyyear, szoutputdir, itreepoints, pulse=None, verbose=False):
    """
    e.g.: TODO export_shape(["S2ndvi_he"], "exportimages", 2020, r"D:\data\ref\field_selection\test_fields_sample\2019_250testfields.shp", r"C:\tmp")
    """
    #
    #
    #
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #
    #
    #
    if not ee.data._credentials: ee.Initialize()
    #
    #    check output directory on system - at least log files will live here - e.g: C:\tmp\
    #
    if not os.path.isdir(szoutputdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")  # root must exist
    szoutputdir = os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3]}_points")              # append this scripts filename + _points
    if not os.path.isdir(szoutputdir) : 
        os.mkdir(szoutputdir)
        if not os.path.isdir(szoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
        os.chmod(szoutputdir, 0o777)
    #
    #    check products and methods
    #
    szyyyymmddfrom = str(int(szyyyyyear)    )  + "-01-01"  # assume per calendar year
    szyyyymmddtill = str(int(szyyyyyear) + 1)  + "-01-01"
    lstszproducts  = saneproducts(lstszproducts)
    exporter       = GEEExporter(*lstszproducts, pulse=pulse)
    eedatefrom     = ee.Date(szyyyymmddfrom)
    eedatetill     = ee.Date(szyyyymmddtill)
    szyyyymmddfrom = eedatefrom.format('YYYYMMdd').getInfo()
    szyyyymmddtill = eedatetill.format('YYYYMMdd').getInfo()

    #
    #    logging to file - e.g: C:\tmp\geebatch_points\geebatch_points_19990101_20000101.log 
    #
    szoutputbasename=os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3] + '_points_' + szyyyymmddfrom + '_' + szyyyymmddtill}")
    logfilehandler = logging.FileHandler(szoutputbasename + ".log")
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler) # (don't forget to remove it!)
    datetime_tick_all  = datetime.datetime.now()
    try:
        #
        #    initial log
        #
        logging.info(" ")
        logging.info(f"{os.path.basename(__file__)[0:-3]}")
        logging.info(f"    products:  {lstszproducts}")
        logging.info(f"    from: {szyyyymmddfrom} till: {szyyyymmddtill}")
        logging.info(f"    output dir: {szoutputdir}")
        logging.info(" ")
        #
        # using discrete_classification band of most recent landcover image
        #
        eeclassification = (ee.ImageCollection('COPERNICUS/Landcover/100m/Proba-V-C3/Global')
                           .sort('system:time_start', False)  # reverse sort
                           .first()                           # most recent
                           .select('discrete_classification') # Land cover classification 0..200
                           .unmask(0, sameFootprint=False))   # 0 = Unknown; in gee used as mask
        
        #
        # assume we skip regions with mainly
        #     0 (Unknown. No or not enough satellite data available.)
        #    70 (Snow and ice. Lands under snow or ice cover throughout the year.)
        #    80 (Permanent water bodies. Lakes, reservoirs, and rivers. Can be either fresh or salt-water bodies.)
        #   200 (Oceans, seas. Can be either fresh or salt-water bodies.)
        #
        lstskiplanduseclasses = [0, 70, 80, 200]
        #
        #
        #
        cPatch = 0
        iPatch = 0
        for eepoint in itreepoints:
            #
            # assume global samples
            #
            longitude = eepoint.coordinates().get(0).getInfo()
            latitude  = eepoint.coordinates().get(1).getInfo()
            #
            # assume landuse determined by about 1km x 1 km environment
            #
            landuseclass = eeclassification.reduceRegion(
                ee.Reducer.mode().unweighted(), eepoint.buffer(500, maxError=0.001)).values().get(0).getInfo()
            #
            # skip specified land use classes
            #
            if landuseclass in lstskiplanduseclasses:
                print(f"({iPatch:5d}) - skipping patch at ({longitude:013.8f}, {latitude:013.8f}): class({landuseclass:3d}) ")
                continue

            cPatch += 1
            print(f"({iPatch:5d}) - patch at ({longitude:013.8f}, {latitude:013.8f}): class({landuseclass:3d}) patches:{cPatch:5d}")
            
            #
            #    specific output directory per land use e.g: C:\tmp\geebatch_points\PV100LC_80
            #
            szfieldoutputdir = os.path.join(szoutputdir, f"PV100LC_{landuseclass}")
            if not os.path.isdir(szfieldoutputdir) : 
                os.mkdir(szfieldoutputdir)
                if not os.path.isdir(szfieldoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szfieldoutputdir)})")
                os.chmod(szfieldoutputdir, 0o777)
 
            #
            #    specific output directory per field e.g: C:\tmp\geebatch\PV100LC_80\Lon0003.56472000_Lat0050.83872000
            #
            szpointlon     = f"{eepoint.coordinates().get(0).getInfo():013.8f}"
            szpointlat     = f"{eepoint.coordinates().get(1).getInfo():013.8f}"
            szid           = f"Lon{szpointlon}_Lat{szpointlat}"

            szfieldoutputdir = os.path.join(szfieldoutputdir, szid)
            if not os.path.isdir(szfieldoutputdir) : 
                os.mkdir(szfieldoutputdir)
                if not os.path.isdir(szfieldoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szfieldoutputdir)})")
                os.chmod(szfieldoutputdir, 0o777)
            #
            #
            #
            logging.info(f"    point: ( lon {szpointlon} lat {szpointlat} ) class( {landuseclass:3d} )")

            #
            #
            #
            exporter.exportimages(eepoint, eedatefrom, eedatetill, szfieldoutputdir, verbose=verbose)

    except Exception as e:
        #
        #
        #
        logging.warning()
        logging.warning(f"{os.path.basename(__file__)[0:-3]}  - unhandled exception: {str(e)}") 
        logging.warning()
        raise

    finally:
        #
        #    remove handler we added at function start
        #
        logging.info(f"{os.path.basename(__file__)[0:-3]} exit - {int( (datetime.datetime.now()-datetime_tick_all).total_seconds()/6/6)/100} hours")
        logging.getLogger().removeHandler(logfilehandler)

"""
"""
def demo_export_point():
    #
    #
    #
    testproducts = ["S2ndvi", "S2ndvi_he", "S2fapar", "S2fapar_he", "S2scl", "S2sclconvmask", "S2tcirgb", "S2cloudlessmask",
                    "S1sigma0", "S1gamma0", "S1rvi",
                    "PV333ndvi", "PV333ndvi_he", "PV333sm", "PV333smsimplemask", "PV333rgb"]
    testproducts = ["S2fapar"]

    testmethods  = ["exportimages", "exportimagestack", "exportimagestacktodrive"]
    testmethods  = ["exportimages"]

    # #half31UESday    = ee.Date('2020-01-29')
    # szdatefrom   = '2020-01-29'
    # szdatetill   = '2020-02-05'
    #
    # #half31UESpoint  = ee.Geometry.Point(3.56472, 50.83872) 
    # pointlon     = 3.56472
    # pointlat     = 50.83872

    #fleecycloudsday = ee.Date('2018-07-12')
    szdatefrom   = '2019-01-01'
    szdatetill   = '2020-01-01'

    szdatefrom   = '2019-01-05'
    szdatetill   = '2019-02-01'
    #bobspoint       = ee.Geometry.Point(4.90782, 51.20069)
    pointlon     = 69.05843780
    pointlat     = 39.87975752
    
    szoutrootdir = r"/vitodata/CropSAR/tmp/dominique/tmp" if IAMRUNNINGONTHEMEP else r"C:\tmp"

    szgdrivedir  = f"{os.path.basename(__file__)[0:-3]}"
    szgdrivedir  = szgdrivedir + "_points"
    
    verbose      = False    
    
    #
    #    no loop; all products & methods in one go.
    #
    export_point(testproducts, testmethods, szdatefrom, szdatetill, pointlon, pointlat, szoutrootdir, szgdrivedir=szgdrivedir, verbose=verbose)


"""
"""
def demo_export_shape():
    #
    #
    #
    testproducts = ["S2ndvi", "S2fapar", "S2scl", "S2sclconvmask",
                    "S1gamma0",
                    "PV333ndvi", "PV333smsimplemask"]

    testmethods  = ["exportimages", "exportimagestack", "exportimagestacktodrive"]

    szyyyyyear   = 2019
    
    szshapefile  = r"/vitodata/CropSAR/data/ref/shp/testfields/2019_250testfields.shp" if IAMRUNNINGONTHEMEP else r"D:\data\ref\field_selection\test_fields_sample\2019_250testfields.shp"

    szoutrootdir = r"/vitodata/CropSAR/tmp/dominique/tmp" if IAMRUNNINGONTHEMEP else r"C:\tmp"

    szgdrivedir  = f"{os.path.basename(__file__)[0:-3]}"
    
    verbose      = False

    if True:
        #
        #    loop per product, per method, so logs give an indication of performance
        #
        for szproduct in testproducts:
            for szmethod in testmethods:
                export_shape(szproduct, szmethod, szyyyyyear, szshapefile, szoutrootdir, szgdrivedir, verbose=verbose)


"""
"""
def demo_export_random_points():
    #
    #
    #
    testproducts = ["S2ndvi", "S2fapar", "S2sclconvmask",  "S1sigma0"]
    testproducts = ["s2sclstaticsmask", "s2sclclassfractions"]
    testproducts = ["S2fapar", "S2sclcombimask", "S2sclconvmask", "S2sclstaticsmask"]
#    szoutrootdir = r"/vitodata/CropSAR/tmp/dominique/gee/s2sclstaticsmask_(3 8 9 10)" if IAMRUNNINGONTHEMEP else r"C:\tmp"
    szoutrootdir = r"/vitodata/CropSAR/tmp/dominique/gee/tmp" if IAMRUNNINGONTHEMEP else r"C:\tmp"
    
    
    szyyyyyear   = 2019    
    verbose      = False    
    #
    #
    #
    pulse = geeutils.Pulse()
    geeutils.wrapasprocess(
        export_random_points,
        args=(testproducts, szyyyyyear, szoutrootdir), 
        kwargs={'pulse':pulse, 'verbose':verbose}, 
        timeout=3*60*60, attempts=None, pulse=pulse) # exportimages and getcollection both have a wrapretry with 127 minutes backoff total

"""
"""
def demo_export_existing_points():
    #
    #
    #
    testproducts = ["S2sclclassfractions"]
    szoutrootdir = r"/vitodata/CropSAR/tmp/dominique/s2sclstaticsmask_(3 8 9 10)" if IAMRUNNINGONTHEMEP else r"C:\tmp"
    szyyyyyear   = 2019    
    verbose      = False 
    #
    #
    #
    pulse = geeutils.Pulse()
    geeutils.wrapasprocess(
        export_existing_points,
        args=(testproducts, szyyyyyear, szoutrootdir), 
        kwargs={'pulse':pulse, 'verbose':verbose}, 
        timeout=3*60*60, attempts=1, pulse=pulse) # no retries here! just checking for deadlocks
"""
"""
def main():
    #demo_export_existing_points()
    demo_export_random_points()
    #demo_export_point()
    #demo_export_shape()
    
"""
"""    
if __name__ == '__main__':
    print('starting main')
    main()
    print('finishing main')

