import os
import logging

import geopandas
import datetime

import ee
if not ee.data._credentials: ee.Initialize()

import geeutils
import geeproduct
import geeexport


#
#
#
IAMRUNNINGONTHEMEP = False
#
#
#
EXPORTABLEPRODUCTS = ["S2ndvi", "S2ndvi_he", "S2fapar", "S2fapar_he", "S2scl", "S2sclconvmask", "S2tcirgb",
                      "S1sigma0", "S1gamma0", "S1rvi",
                      "PV333ndvi", "PV333ndvi_he", "PV333sm", "PV333smsimplemask", "PV333rgb"]
#
#
#
EXPORTMETHODS = ["exportimages", "exportimagestack", "exportimagestodrive", "exportimagestacktodrive"]
#
#    q&d demonstrator
#
class GEEExporter():
    #
    #
    #
    def __init__(self, *szproducts):
        self.szproducts = []
        assert (0 < len(szproducts))                   # at least one product
        if isinstance(szproducts, str) : 
            szproducts = [szproducts]
        for szproduct in szproducts:
            assert (szproduct in EXPORTABLEPRODUCTS)   # only known products
            if szproduct not in self.szproducts:
                self.szproducts.append(szproduct)
    #
    #
    #
    def _getgeecollections(self, eedatefrom, eedatetill, eepoint, verbose=False):
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
        if "S2ndvi" in self.szproducts           : yield geeproduct.GEECol_s2ndvi().getcollection(             eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2ndvi_he" in self.szproducts        : yield geeproduct.GEECol_s2ndvi_he().getcollection(          eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2fapar" in self.szproducts          : yield geeproduct.GEECol_s2fapar().getcollection(            eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2fapar_he" in self.szproducts       : yield geeproduct.GEECol_s2fapar_he().getcollection(         eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S2scl" in self.szproducts            : yield geeproduct.GEECol_s2scl().getcollection(              eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2sclconvmask" in self.szproducts    : yield geeproduct.GEECol_s2sclconvmask().getcollection(      eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if "S2tcirgb" in self.szproducts         : yield geeproduct.GEECol_s2rgb().getcollection(              eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
 
        if "S1sigma0" in self.szproducts         : yield geeproduct.GEECol_s1sigma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0" in self.szproducts         : yield geeproduct.GEECol_s1sigma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0" in self.szproducts         : yield geeproduct.GEECol_s1sigma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1sigma0" in self.szproducts         : yield geeproduct.GEECol_s1sigma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0" in self.szproducts         : yield geeproduct.GEECol_s1gamma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0" in self.szproducts         : yield geeproduct.GEECol_s1gamma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0" in self.szproducts         : yield geeproduct.GEECol_s1gamma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1gamma0" in self.szproducts         : yield geeproduct.GEECol_s1gamma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if "S1rvi" in self.szproducts            : yield geeproduct.GEECol_s1rvi().getcollection(              eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
         
        if "PV333ndvi" in self.szproducts        : yield geeproduct.GEECol_pv333ndvi().getcollection(          eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333ndvi_he" in self.szproducts     : yield geeproduct.GEECol_pv333ndvi_he().getcollection(       eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333sm" in self.szproducts          : yield geeproduct.GEECol_pv333sm().getcollection(            eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333smsimplemask" in self.szproducts: yield geeproduct.GEECol_pv333simplemask().getcollection(    eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if "PV333rgb" in self.szproducts         : yield geeproduct.GEECol_pv333rgb().getcollection(           eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)     
     
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


#
#
#
def export_point(lstszproducts, lstszmethods):
    if isinstance(lstszproducts, str) : lstszproducts = [lstszproducts]
    if isinstance(lstszmethods, str)  : lstszmethods  = [lstszmethods]

    eepoint           = geeutils.half31UESpoint #bobspoint #tennvenlopoint
    eedatefrom        = geeutils.half31UESday   #fleecycloudsday
    eedatetill        = eedatefrom.advance(1, 'week')
    verbose           = True    
 
    szoutputdir       = r"/vitodata/CropSAR/tmp/dominique" if IAMRUNNINGONTHEMEP else r"C:\tmp"
    szgdrivedir       = f"{os.path.basename(__file__)[0:-3]}"
 
    geeexporter = GEEExporter(*lstszproducts)
    if "exportimages"            in lstszmethods: geeexporter.exportimages           (eepoint, eedatefrom, eedatetill, szoutputdir, verbose=verbose)
    if "exportimagestack"        in lstszmethods: geeexporter.exportimagestack       (eepoint, eedatefrom, eedatetill, szoutputdir, verbose=verbose)
    if "exportimagestodrive"     in lstszmethods: geeexporter.exportimagestodrive    (eepoint, eedatefrom, eedatetill, szgdrivedir, verbose=verbose)
    if "exportimagestacktodrive" in lstszmethods: geeexporter.exportimagestacktodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, verbose=verbose)

#
#
#
def export_shape(lstszproducts, lstszmethods):
    if isinstance(lstszproducts, str) : lstszproducts = [lstszproducts]
    if isinstance(lstszmethods, str)  : lstszmethods  = [lstszmethods]
    #
    #
    #
    verbose = False
    #
    #
    #
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #
    #    assume per calendar year
    #
    szyyyycropyear   = '2019'
    szyyyymmddfrom   = str(int(szyyyycropyear)    )  + "-01-01" 
    szyyyymmddtill   = str(int(szyyyycropyear) + 1)  + "-01-01"
    #
    #    have pandas read the shapefile which is assumed to have fieldID
    #
    szshapefile = r"/vitodata/CropSAR/data/ref/shp/testfields/2019_250testfields.shp" if IAMRUNNINGONTHEMEP else r"D:\data\ref\field_selection\test_fields_sample\2019_250testfields.shp"
    parcelsgeodataframe = geopandas.read_file(szshapefile)
    parcelsgeodataframe.set_index( 'fieldID', inplace=True, verify_integrity=True)
    parcelsgeodataframe.to_crs(epsg=4326, inplace=True)
    numberofparcels = len(parcelsgeodataframe.index)
    #
    #    some output directory on system - at least log files will live here - e.g: C:\tmp\geebatch
    #
    szoutputdir = r"/vitodata/CropSAR/tmp/dominique/tmp" if IAMRUNNINGONTHEMEP else r"C:\tmp"
    if not os.path.isdir(szoutputdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")  # root must exist
    szoutputdir = os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3]}")                     # append this scripts filename
    if not os.path.isdir(szoutputdir) : 
        os.mkdir(szoutputdir)
        if not os.path.isdir(szoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
        os.chmod(szoutputdir, 0o777)
    #
    # google drive folder: this scripts filename
    #
    szgdrivedir = f"{os.path.basename(__file__)[0:-3]}"
    #
    #
    #
    exporter           = GEEExporter(*lstszproducts)
    eedatefrom         = ee.Date(szyyyymmddfrom)
    eedatetill         = ee.Date(szyyyymmddtill)
    #
    #    logging to file - e.g: C:\tmp\geebatch\geebatch_19990101_20000101.log
    #
    szoutputbasename=os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3] + '_' + szyyyymmddfrom + '_' + szyyyymmddtill}")
    logfilehandler = logging.FileHandler(szoutputbasename + ".log")
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler)
    #
    #    initial log
    #
    logging.info(" ")
    logging.info(f"{os.path.basename(__file__)[0:-3]}")
    logging.info(f"    products:  {exporter.szproducts}")
    logging.info(f"    exports:   {lstszmethods}")
    logging.info(f"    shapefile: {os.path.basename(szshapefile)}")
    logging.info(f"    from: {szyyyymmddfrom} till: {szyyyymmddtill}")
    logging.info(f"    parcels: {numberofparcels}")
    logging.info(" ")
    #
    #    get circus on the road
    #
    datetime_tick_all  = datetime.datetime.now()
    doskip   = False # hack in case we were interrupted
    try:
        icountparcels = 0
        for fieldId, field in parcelsgeodataframe.iterrows():

            if doskip :
                print( "skipping " + fieldId)
                if fieldId == "000028085AF2E0B9":
                    doskip = False # last fieldId skipped
                continue

            datetime_tick = datetime.datetime.now()
            icountparcels += 1
            if (icountparcels > 2): return
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
        logging.info(f"{os.path.basename(__file__)[0:-3]} run {numberofparcels} parcels - {int( (datetime.datetime.now()-datetime_tick_all).total_seconds()/60/6)/10} hours")
        logging.getLogger().removeHandler(logfilehandler)


"""
"""
def main():
    #
    #    performance exportimages vs exportimagestack and S2ndvi vs S2ndvi_he
    #
    #export_shape(["S2ndvi", "S2ndvi_he"], ["exportimages", "exportimagestack"])

    allproducts = ["S2ndvi", "S2fapar", "S2scl", "S2sclconvmask",
                      "S1gamma0",
                      "PV333ndvi", "PV333smsimplemask"]

    for szproduct in allproducts:
        export_shape([szproduct], ["exportimages", "exportimagestack", "exportimagestacktodrive"])
"""
"""
if __name__ == '__main__':
    print('starting main')
    main()
    print('finishing main')

