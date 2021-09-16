import os
import logging

import geopandas
import datetime

import ee
if not ee.data._credentials: ee.Initialize()

import geeproduct
import geeexport


#
#
#
IAMRUNNINGONTHEMEP = False

#
#    available products
#
EXPORTABLEPRODUCTS = ["S2ndvi", "S2ndvi_he", "S2fapar", "S2fapar_he", "S2scl", "S2sclconvmask", "S2tcirgb",
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
    specifies S2 20m (GEECol_s2scl()) as referenc collection
    eexporting 1280m (64 pix) diameter roi's
"""
class GEEExporter():
    #
    #
    #
    def __init__(self, *szproducts):
        """
        e.g. exporter = GEEExporter("S2ndvi", "S1sigma0")
        """
        self.szproducts = saneproducts(*szproducts)
    #
    #
    #
    def _getgeecollections(self, eedatefrom, eedatetill, eepoint, verbose=False):
        """
        generator yielding collections for specifed products
        """
        #
        #    using sentinel 2 20m as reference
        #
        refcol    = geeproduct.GEECol_s2scl()
        refcolpix = 64
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
        if "S2ndvi"            in self.szproducts: yield geeproduct.GEECol_s2ndvi().getcollection(             eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2ndvi_he"         in self.szproducts: yield geeproduct.GEECol_s2ndvi_he().getcollection(          eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2fapar"           in self.szproducts: yield geeproduct.GEECol_s2fapar().getcollection(            eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2fapar_he"        in self.szproducts: yield geeproduct.GEECol_s2fapar_he().getcollection(         eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2scl"             in self.szproducts: yield geeproduct.GEECol_s2scl().getcollection(              eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2sclconvmask"     in self.szproducts: yield geeproduct.GEECol_s2sclconvmask().getcollection(      eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2tcirgb"          in self.szproducts: yield geeproduct.GEECol_s2rgb().getcollection(              eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
 
        if "S1sigma0"          in self.szproducts: yield geeproduct.GEECol_s1sigma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0"          in self.szproducts: yield geeproduct.GEECol_s1sigma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0"          in self.szproducts: yield geeproduct.GEECol_s1sigma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0"          in self.szproducts: yield geeproduct.GEECol_s1sigma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"          in self.szproducts: yield geeproduct.GEECol_s1gamma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"          in self.szproducts: yield geeproduct.GEECol_s1gamma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"          in self.szproducts: yield geeproduct.GEECol_s1gamma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0"          in self.szproducts: yield geeproduct.GEECol_s1gamma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1rvi"             in self.szproducts: yield geeproduct.GEECol_s1rvi().getcollection(              eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
         
        if "PV333ndvi"         in self.szproducts: yield geeproduct.GEECol_pv333ndvi().getcollection(          eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333ndvi_he"      in self.szproducts: yield geeproduct.GEECol_pv333ndvi_he().getcollection(       eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333sm"           in self.szproducts: yield geeproduct.GEECol_pv333sm().getcollection(            eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333smsimplemask" in self.szproducts: yield geeproduct.GEECol_pv333simplemask().getcollection(    eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333rgb"          in self.szproducts: yield geeproduct.GEECol_pv333rgb().getcollection(           eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)     

    #
    #    export methods
    #     
    def exportimages(self, eepoint, eedatefrom, eedatetill, szoutputdir, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimages(geecollection, szoutputdir, szfilenameprefix=szfilenameprefix, verbose=verbose)
 
    def exportimagestack(self, eepoint, eedatefrom, eedatetill, szoutputdir, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimagestack(geecollection, szoutputdir, szfilenameprefix=szfilenameprefix, verbose=verbose)
 
    def exportimagestodrive(self, eepoint, eedatefrom, eedatetill, szgdrivefolder, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimagestodrive(geecollection, szgdrivefolder, szfilenameprefix=szfilenameprefix, verbose=verbose)
         
    def exportimagestacktodrive(self, eepoint, eedatefrom, eedatetill, szgdrivefolder, szfilenameprefix="", verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimagestacktodrive(geecollection, szgdrivefolder, szfilenameprefix=szfilenameprefix, verbose=verbose)


"""
demonstrator - including logging & furniture: simple export for single point
"""
def export_point(lstszproducts, lstszmethods, szdatefrom, szdatetill, pointlon, pointlat, szoutputdir, szgdrivedir=None, verbose=False):
    """
    e.g.: export_point(["S2ndvi", "S1sigma0"], "exportimages", "2019-01-01", "2020-01-01", 4.90782, 51.20069, r"C:\tmp")
    """
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
        logging.info(f"    point: (lon {szpointlon} lat {szpointlat} )")
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
"""
def demo_export_point():
    #
    #
    #
    testproducts = ["S2ndvi", "S2ndvi_he", "S2fapar", "S2fapar_he", "S2scl", "S2sclconvmask", "S2tcirgb",
                    "S1sigma0", "S1gamma0", "S1rvi",
                    "PV333ndvi", "PV333ndvi_he", "PV333sm", "PV333smsimplemask", "PV333rgb"]

    testmethods  = ["exportimages", "exportimagestack", "exportimagestacktodrive"]

    szdatefrom   = '2020-01-29'
    szdatetill   = '2020-02-05'

    pointlon     = 3.56472
    pointlat     = 50.83872
    
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
def main():
    demo_export_point()
    #demo_export_shape()
    
"""
"""    
if __name__ == '__main__':
    print('starting main')
    main()
    print('finishing main')

