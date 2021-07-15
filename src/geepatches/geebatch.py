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
do_S2ndvi              = True
do_S2fapar             = True
do_S2scl               = True
do_S2sclconvmask       = True
do_S2tcirgb            = True

do_S1sigma0            = True
do_S1gamma0            = True
do_S1rvi               = True

do_PV333ndvi           = True
do_PV333sm             = True
do_PV333smsimplemask   = True
do_PV333rgb            = True


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
    
    def exportseparateimages(self, eepoint, eedatefrom, eedatetill, szoutputdir, verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportseparateimages(geecollection, szoutputdir, verbose=verbose)

    def exportimagestacks(self, eepoint, eedatefrom, eedatetill, szoutputdir, verbose=False):
        result = True
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            result = result and geeexport.GEEExp().exportimagestacks(geecollection, szoutputdir, verbose=verbose)
        return result

    def exportseparateimagestodrive(self, eepoint, eedatefrom, eedatetill, szoutputdir, verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportseparateimagestodrive(geecollection, verbose=verbose)
        
    def exportimagestackstodrive(self, eepoint, eedatefrom, eedatetill, szoutputdir, verbose=False):
        for geecollection in self._getgeecollections(eedatefrom, eedatetill, eepoint, verbose=verbose):
            geeexport.GEEExp().exportimagestackstodrive(geecollection, verbose=verbose)
#
#
#
def xmain():
    eepoint           = geeutils.half31UESpoint #bobspoint #tennvenlopoint
    eedatefrom        = geeutils.half31UESday #fleecycloudsday
    eedatetill        = eedatefrom.advance(1, 'year')
    verbose           = False    
    #GEEExporter().exportseparateimagestodrive(eepoint, eedatefrom, eedatetill, "C:/tmp/", verbose)
    GEEExporter().exportimagestackstodrive(eepoint, eedatefrom, eedatetill, "C:/tmp/", verbose)
    #GEEExporter().exportimagestacks(eepoint, eedatefrom, eedatetill, "C:/tmp/", verbose)
    #GEEExporter().exportseparateimages(eepoint, eedatefrom, eedatetill, "C:/tmp2/", verbose)


#
#
#
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  
    szyyyycropyear   = '2019'
    szshapefile      = r"D:\data\ref\field_selection\test_fields_sample\2019_250testfields.shp"
    #szshapefile      = r"/data/CropSAR/data/ref/shp/testfields/2019_250testfields.shp"

    szyyyymmddfrom   = str(int(szyyyycropyear)    )  + "-01-01" 
    szyyyymmddtill   = str(int(szyyyycropyear)    )  + "-02-01"
    #
    #    have pandas read the shapefile which is assumed to have fieldID
    #
    parcelsgeodataframe = geopandas.read_file(szshapefile)
    parcelsgeodataframe.set_index( 'fieldID', inplace=True, verify_integrity=True)
    parcelsgeodataframe.to_crs(epsg=4326, inplace=True)
    #
    #    root output dir on system
    #
    szoutputdir     = r"C:\tmp"
    #szoutputdir     = r"/data/CropSAR/tmp/dominique"
    
    #
    #    root output dir for tool : ..\geebatch
    #
    szoutputdir = os.path.normpath(szoutputdir)
    if not os.path.isdir(szoutputdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
    szoutputdir = os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3]}")
    if not os.path.isdir(szoutputdir) : 
        os.mkdir(szoutputdir)
        if not os.path.isdir(szoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
        os.chmod(szoutputdir, 0o777)
    #
    #    logging to file: ..\geebatch\geebatch_19990101_20000101.log
    #
    szoutputbasename=os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3] + '_' + szyyyymmddfrom + '_' + szyyyymmddtill}")
    logfilehandler = logging.FileHandler(szoutputbasename + ".log")
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler)
    #
    #    output dir for run (cropyear) : ..\geebatch\1999
    #
    szoutputdir = os.path.normpath(szoutputdir)
    if not os.path.isdir(szoutputdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
    szoutputdir = os.path.join(szoutputdir, szyyyycropyear)
    if not os.path.isdir(szoutputdir) : 
        os.mkdir(szoutputdir)
        if not os.path.isdir(szoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
        os.chmod(szoutputdir, 0o777)
    #
    #
    #
    exporter = GEEExporter()
    try:
        for fieldId, field in parcelsgeodataframe.iterrows():
            datetime_tick  = datetime.datetime.now()

            shapelygeometry = field['geometry']
            shapelypoint    = shapelygeometry.centroid
            eepoint         = ee.Geometry.Point(shapelypoint.x, shapelypoint.y)

            #
            #    output dir per field : ..\geebatch\1999\0000280859BE7A17
            #
            szfieldoutputdir = os.path.join(szoutputdir, fieldId)
            if not os.path.isdir(szfieldoutputdir) : 
                os.mkdir(szfieldoutputdir)
                if not os.path.isdir(szfieldoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
                os.chmod(szfieldoutputdir, 0o777)

            result = exporter.exportimagestacks(eepoint, ee.Date(szyyyymmddfrom), ee.Date(szyyyymmddtill), szfieldoutputdir)

            if result:
                logging.info(f"fieldId {fieldId}: SUCCESS {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")
            else:
                logging.error(f"fieldId {fieldId}: FAILED {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")
    #
    #    anyway
    #
    finally:
        #
        #    remove handler we added at function start
        #
        logging.getLogger().removeHandler(logfilehandler)



if __name__ == '__main__':
    print('starting main')
    main()
    print('finishing main')


