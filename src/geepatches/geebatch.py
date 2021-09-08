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
#    export types
#
do_exportimages            = True
do_exportimagestack        = True
do_exportimagestodrive     = True  # use only for very short timeseries (e.g. single date)
do_exportimagestacktodrive = True

#
#    relevant products
#
do_S2ndvi              = False
do_S2fapar             = True
do_S2scl               = False
do_S2sclconvmask       = False #True
do_S2tcirgb            = False

do_S1sigma0            = False
do_S1gamma0            = False #True
do_S1rvi               = False

do_PV333ndvi           = False
do_PV333sm             = False
do_PV333smsimplemask   = False
do_PV333rgb            = False


#
#    q&d demonstrator
#
class GEEExporter():
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
        if do_S2ndvi           : yield geeproduct.GEECol_s2ndvi().getcollection(             eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S2fapar          : yield geeproduct.GEECol_s2fapar().getcollection(            eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S2scl            : yield geeproduct.GEECol_s2scl().getcollection(              eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if do_S2sclconvmask    : yield geeproduct.GEECol_s2sclconvmask().getcollection(      eedatefrom, eedatetill, eepoint, s2_20m_pix, refcol, refcolpix, verbose=verbose)
        if do_S2tcirgb         : yield geeproduct.GEECol_s2rgb().getcollection(              eedatefrom, eedatetill, eepoint, s2_10m_pix, refcol, refcolpix, verbose=verbose)

        if do_S1sigma0         : yield geeproduct.GEECol_s1sigma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1sigma0         : yield geeproduct.GEECol_s1sigma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1sigma0         : yield geeproduct.GEECol_s1sigma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1sigma0         : yield geeproduct.GEECol_s1sigma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1gamma0         : yield geeproduct.GEECol_s1gamma0('VV', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1gamma0         : yield geeproduct.GEECol_s1gamma0('VH', 'ASC').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1gamma0         : yield geeproduct.GEECol_s1gamma0('VV', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1gamma0         : yield geeproduct.GEECol_s1gamma0('VH', 'DES').getcollection(eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        if do_S1rvi            : yield geeproduct.GEECol_s1rvi().getcollection(              eedatefrom, eedatetill, eepoint, s1_10m_pix, refcol, refcolpix, verbose=verbose)
        
        if do_PV333ndvi        : yield geeproduct.GEECol_pv333ndvi().getcollection(          eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if do_PV333sm          : yield geeproduct.GEECol_pv333sm().getcollection(            eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if do_PV333smsimplemask: yield geeproduct.GEECol_pv333simplemask().getcollection(    eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)
        if do_PV333rgb         : yield geeproduct.GEECol_pv333rgb().getcollection(           eedatefrom, eedatetill, eepoint, pv333m_pix, refcol, refcolpix, verbose=verbose)     
    
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
def main():
    eepoint           = geeutils.half31UESpoint #bobspoint #tennvenlopoint
    eedatefrom        = geeutils.half31UESday   #fleecycloudsday
    eedatetill        = eedatefrom.advance(1, 'week')
    verbose           = False    

    szoutputdir       = r"/vitodata/CropSAR/tmp/dominique" if IAMRUNNINGONTHEMEP else r"C:\tmp"
    szgdrivedir       = f"{os.path.basename(__file__)[0:-3]}"

    if do_exportimages:            GEEExporter().exportimages           (eepoint, eedatefrom, eedatetill, szoutputdir, verbose=verbose)
    if do_exportimagestack:        GEEExporter().exportimagestack       (eepoint, eedatefrom, eedatetill, szoutputdir, verbose=verbose)
    if do_exportimagestodrive:     GEEExporter().exportimagestodrive    (eepoint, eedatefrom, eedatetill, szgdrivedir, verbose=verbose)
    if do_exportimagestacktodrive: GEEExporter().exportimagestacktodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, verbose=verbose)

#
#
#
def xmain():
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
    szyyyymmddtill   = str(int(szyyyycropyear)    )  + "-01-05"
    #
    #    have pandas read the shapefile which is assumed to have fieldID
    #
    szshapefile = r"/vitodata/CropSAR/data/ref/shp/testfields/2019_250testfields.shp" if IAMRUNNINGONTHEMEP else r"D:\data\ref\field_selection\test_fields_sample\2019_250testfields.shp"
    parcelsgeodataframe = geopandas.read_file(szshapefile)
    parcelsgeodataframe.set_index( 'fieldID', inplace=True, verify_integrity=True)
    parcelsgeodataframe.to_crs(epsg=4326, inplace=True)
    #
    #    some output directory on system - at least log files will live here - e.g: C:\tmp\geebatch
    #
    szoutputdir = r"/vitodata/CropSAR/tmp/dominique" if IAMRUNNINGONTHEMEP else r"C:\tmp"
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
    logging.info(f"    exports: {'exportimages ' if do_exportimages else ''}{'exportimagestack ' if do_exportimagestack else ''}{'exportimagestodrive ' if do_exportimagestodrive else ''}{'exportimagestacktodrive ' if do_exportimagestacktodrive else ''}")
    logging.info(f"    shapefile: {os.path.basename(szshapefile)}")
    logging.info(f"    from: {szyyyymmddfrom} till: {szyyyymmddtill}")
    logging.info(" ")
    #
    #    get circus on the road
    #
    datetime_tick_all  = datetime.datetime.now()
    exporter           = GEEExporter()
    eedatefrom         = ee.Date(szyyyymmddfrom)
    eedatetill         = ee.Date(szyyyymmddtill)
    #
    #
    #
    try:
        for fieldId, field in parcelsgeodataframe.iterrows():
            datetime_tick = datetime.datetime.now()
            if fieldId != "000028085AF2E0B9": continue
            #
            #
            #
            shapelygeometry = field['geometry']
            shapelypoint    = shapelygeometry.centroid
            eepoint         = ee.Geometry.Point(shapelypoint.x, shapelypoint.y)
            #
            #
            #
            if (do_exportimages or do_exportimagestack):
                #
                #    specific output directory per field e.g: C:\tmp\geebatch\0000280859BE7A17
                #
                szfieldoutputdir = os.path.join(szoutputdir, fieldId)
                if not os.path.isdir(szfieldoutputdir) : 
                    os.mkdir(szfieldoutputdir)
                    if not os.path.isdir(szfieldoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
                    os.chmod(szfieldoutputdir, 0o777)
                if do_exportimages:     exporter.exportimages(eepoint, eedatefrom, eedatetill, szfieldoutputdir, verbose=verbose)
                if do_exportimagestack: exporter.exportimagestack(eepoint, eedatefrom, eedatetill, szfieldoutputdir, verbose=verbose)
            #
            #    toDrive will prepend the filenames with the fieldId
            #
            szfilenameprefix = str(fieldId) + "_"
            if do_exportimagestodrive:     exporter.exportimagestodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, szfilenameprefix=szfilenameprefix, verbose=verbose)
            if do_exportimagestacktodrive: exporter.exportimagestacktodrive(eepoint, eedatefrom, eedatetill, szgdrivedir, szfilenameprefix=szfilenameprefix, verbose=verbose)

            logging.info(f"export field {fieldId} done - {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")

    finally:
        #
        #    remove handler we added at function start
        #
        logging.info(f"{os.path.basename(__file__)[0:-3]} run {int( (datetime.datetime.now()-datetime_tick_all).total_seconds()/60/6)/10} hours")
        logging.getLogger().removeHandler(logfilehandler)


"""
"""
if __name__ == '__main__':
    print('starting main')
    main()
    print('finishing main')


