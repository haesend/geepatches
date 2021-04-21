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
do_S1                  = True
do_S2ndvi              = True
do_S2fapar             = True
do_S2scl               = True
do_S2sclconvmask       = True
do_PV333Mndvi          = False
do_PV333Msm            = False
do_PV333Msmsimplemask  = False

#
#
#
class Exporter():
    
    def __init__(self, szyyyymmddfrom, szyyyymmddtill, refprodroiradius, refprodroiradunits = 'pixels', verbose=False):
        """
        """
        eedatefrom  = ee.Date(szyyyymmddfrom) 
        eedatetill  = ee.Date(szyyyymmddtill)
        
        product_S1                  = geeproduct.GEEProduct_S1()
        product_S2ndvi              = geeproduct.GEEProduct_S2ndvi()
        product_S2fapar             = geeproduct.GEEProduct_S2fapar()
        product_S2scl               = geeproduct.GEEProduct_S2scl()
        product_S2sclconvmask       = geeproduct.GEEProduct_S2sclconvmask()
        product_PV333Mndvi          = geeproduct.GEEProduct_PV333Mndvi()
        product_PV333Msm            = geeproduct.GEEProduct_PV333Msm()
        product_PV333Msmsimplemask  = geeproduct.GEEProduct_PV333Msmsimplemask()

        #
        #    e.g.: 128 pix refprodroiradius with product_S2ndvi reference => 128 * 2 * 10m = 256m square
        #    upsampling maximum is PV333m: 333m -> 32*10m
        #       
        self._export_S1                 = geeexport.GEEExport(product_S1,                 eedatefrom, eedatetill, refprodroiradius,   2, 32, product_S2ndvi, refprodroiradunits=refprodroiradunits) 
        self._export_S2ndvi             = geeexport.GEEExport(product_S2ndvi,             eedatefrom, eedatetill, refprodroiradius,   1, 32,                 refprodroiradunits=refprodroiradunits)
        self._export_S2fapar            = geeexport.GEEExport(product_S2fapar,            eedatefrom, eedatetill, refprodroiradius,   1, 32, product_S2ndvi, refprodroiradunits=refprodroiradunits)
        self._export_S2scl              = geeexport.GEEExport(product_S2scl,              eedatefrom, eedatetill, refprodroiradius,   2, 32, product_S2ndvi, refprodroiradunits=refprodroiradunits)
        self._export_S2sclconvmask      = geeexport.GEEExport(product_S2sclconvmask,      eedatefrom, eedatetill, refprodroiradius,   2, 32, product_S2ndvi, refprodroiradunits=refprodroiradunits)
        self._export_PV333Mndvi         = geeexport.GEEExport(product_PV333Mndvi,         eedatefrom, eedatetill, refprodroiradius,  32, 32, product_S2ndvi, refprodroiradunits=refprodroiradunits)
        self._export_PV333Msm           = geeexport.GEEExport(product_PV333Msm,           eedatefrom, eedatetill, refprodroiradius,  32, 32, product_S2ndvi, refprodroiradunits=refprodroiradunits)
        self._export_PV333Msmsimplemask = geeexport.GEEExport(product_PV333Msmsimplemask, eedatefrom, eedatetill, refprodroiradius,  32, 32, product_S2ndvi, refprodroiradunits=refprodroiradunits)

    def exportpointtofile(self, szid, eepoint, szdstpath, verbose=False):
        """
        """
        if do_S1:
            self._export_S1.exportpointtofile(                szid, eepoint, szdstpath, verbose=verbose)
        if do_S2ndvi:
            self._export_S2ndvi.exportpointtofile(            szid, eepoint, szdstpath, verbose=verbose)
        if do_S2fapar:
            self._export_S2fapar.exportpointtofile(           szid, eepoint, szdstpath, verbose=verbose)
        if do_S2scl:
            self._export_S2scl.exportpointtofile(             szid, eepoint, szdstpath, verbose=verbose)
        if do_S2sclconvmask:
            self._export_S2sclconvmask.exportpointtofile(     szid, eepoint, szdstpath, verbose=verbose)
        if do_PV333Mndvi:
            self._export_PV333Mndvi.exportpointtofile(        szid, eepoint, szdstpath, verbose=verbose)
        if do_PV333Msm:
            self._export_PV333Msm.exportpointtofile(          szid, eepoint, szdstpath, verbose=verbose)
        if do_PV333Msmsimplemask:
            self._export_PV333Msmsimplemask.exportpointtofile(szid, eepoint, szdstpath, verbose=verbose)

    def exportpointtodrive(self, szid, eepoint, szdstfolder="geepatches", verbose=False):
        """
        """
        if do_S1:
            self._export_S1.exportpointtodrive(                szid, eepoint, szdstfolder, verbose=verbose)
        if do_S2ndvi:
            self._export_S2ndvi.exportpointtodrive(            szid, eepoint, szdstfolder, verbose=verbose)
        if do_S2fapar:
            self._export_S2fapar.exportpointtodrive(           szid, eepoint, szdstfolder, verbose=verbose)
        if do_S2scl:
            self._export_S2scl.exportpointtodrive(             szid, eepoint, szdstfolder, verbose=verbose)
        if do_S2sclconvmask:
            self._export_S2sclconvmask.exportpointtodrive(     szid, eepoint, szdstfolder, verbose=verbose)
        if do_PV333Mndvi:
            self._export_PV333Mndvi.exportpointtodrive(        szid, eepoint, szdstfolder, verbose=verbose)
        if do_PV333Msm:
            self._export_PV333Msm.exportpointtodrive(          szid, eepoint, szdstfolder, verbose=verbose)
        if do_PV333Msmsimplemask:
            self._export_PV333Msmsimplemask.exportpointtodrive(szid, eepoint, szdstfolder, verbose=verbose)


#
#
#
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    szyyyycropyear   = '2019'
    szshapefile      = r"D:\data\ref\field_selection\test_fields_sample\2019_250testfields.shp"
    szyyyymmddfrom   = str(int(szyyyycropyear)    )  + "-01-01" 
    szyyyymmddtill   = str(int(szyyyycropyear) + 1)  + "-01-01"
    parcelsgeodataframe = geopandas.read_file(szshapefile)
    parcelsgeodataframe.set_index( 'fieldID', inplace=True, verify_integrity=True)

    #
    #    logging to file
    #
    szoutputdir     =f"D:\\tmp\\{os.path.basename(__file__)[0:-3]}"
    szoutputbasename=os.path.join(szoutputdir, f"{os.path.basename(__file__)[0:-3] + '_' + szyyyymmddfrom + '_' + szyyyymmddtill}")
    logfilehandler = logging.FileHandler(szoutputbasename + ".log")
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler)


    szdstfolder = "geeyatt_" + szyyyycropyear
    #
    #
    #
    exporter = Exporter(szyyyymmddfrom, szyyyymmddtill, 128)

    try:
    
        for fieldId, field in parcelsgeodataframe.iterrows():
            shapelygeometry = field['geometry']
            shapelypoint    = shapelygeometry.centroid
            eepoint         = ee.Geometry.Point(shapelypoint.x, shapelypoint.y)
            
            datetime_tick  = datetime.datetime.now()
            print (f"fieldId {fieldId}")
            """
            result = geeutils.wrapasprocess(
                exporter.exportpointtofile, 
                args = (fieldId, eepoint, szoutputdir),
                timeout=24*60*60, attempts=3, verbose=False)
            """
            result = geeutils.wrapasprocess(
                exporter.exportpointtodrive, 
                args = (fieldId, eepoint, szdstfolder),
                timeout=24*60*60, attempts=3, verbose=False) # wait one day, thanks to my greedy fellow users
            
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
#
#
#
if __name__ == '__main__':
    print('starting main')
    main()
    print('finishing main')


