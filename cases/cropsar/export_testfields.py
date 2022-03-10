"""
exporting tiffs for parcels as specified in CropSAR I shape files

assumes (source) shape files containing: 
- attribute 'fieldID'   : some unique parcel identifier
- attribute 'croptype'  : crop type id (string) representing the crop in the parcel. eg. '901' for Potato ('niet-vroeg') ...
- attribute 'area'      : area of the parcels in square meter

results in directory structure as
    szoutrootdir - croptype_X - fieldID_xxxxxxxxxxxxxxxx
                              - fieldID_xxxxxxxxxxxxxxxx
                              - ...
                 - croptype_Y - fieldID_yyyyyyyyyyyyyyyy
                              - fieldID_yyyyyyyyyyyyyyyy
                              - ...
                 - ...
"""


import os
import logging
import datetime

import geopandas

import ee
if not ee.data._credentials: ee.Initialize()
import geebatch

from utils_testfields import CropSARParcels


#
#
#
def _exportshape(szshapefile, lstszcroptypeids, szyyyyyear, szoutputrootdir, lstszproducts, verbose=False):
    """
    """
    parcelsgeodataframe = CropSARParcels.cropsar_shptopandas(szshapefile, lstszcroptypeids=lstszcroptypeids, verbose=True)
    #
    #
    #
    if parcelsgeodataframe.crs is None: 
        parcelsgeodataframe.set_crs('epsg:4326', inplace=True)
    else:
        parcelsgeodataframe.to_crs('epsg:4326', inplace=True)
    #
    #
    #
    exporter = geebatch.GEEExporter(lstszproducts)
    #
    #    assume per calendar year
    #
    szyyyymmddfrom   = str(int(szyyyyyear)    )  + "-01-01" 
    szyyyymmddtill   = str(int(szyyyyyear) + 1)  + "-01-01"
    #
    #
    #
    numberofparcels   = len(parcelsgeodataframe.index) 
    icountparcels     = 0
    #
    #
    #
    for parcel in parcelsgeodataframe.itertuples():
        icountparcels = icountparcels + 1
        datetime_tick = datetime.datetime.now()
        szfieldID     = str(parcel.fieldID)
        icroptype     = str(int(parcel.croptype))
        shapelypoint  = parcel.geometry.centroid
        eepoint       = ee.Geometry.Point(shapelypoint.x, shapelypoint.y)
        szoutputdir   = CropSARParcels.getparceldirectory(szoutputrootdir, icroptype, szfieldID)
        
        if True:
            try: 
                #
                # might be nice to have a shape file of specific patch
                #
                szparcelshapefile = os.path.join(szoutputdir, szfieldID + ".shp")
                if not os.path.isfile(szparcelshapefile): # no need if it is already there
                    CropSARParcels.pandastoshp(
                        geopandas.GeoDataFrame( geometry=[parcel.geometry], crs=parcelsgeodataframe.crs), 
                        szparcelshapefile)
            except:
                #
                # but we do not want any additional problems with this
                #
                pass

        #
        # actual export
        #
        try:
            exporter.exportimages(eepoint, ee.Date(szyyyymmddfrom), ee.Date(szyyyymmddtill), szoutputdir, verbose=verbose)
            logging.info(f"export field {szfieldID} - croptype {icroptype} parcel({icountparcels} of {numberofparcels}) done - {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")
        except:
            logging.warning(f"export field {szfieldID} - croptype {icroptype} parcel({icountparcels} of {numberofparcels}) failed - {int((datetime.datetime.now()-datetime_tick).total_seconds())} seconds")
            raise

#
#
#
def exportshape(szshapefile, lstszcroptypeids, szyyyyyear, szoutputrootdir, lstszproducts, verbose=False):
    """
    """
    if not os.path.isfile(szshapefile)    : raise ValueError(f"invalid szshapefile ({str(szshapefile)})")      # shapefile must exist
    if not os.path.isdir(szoutputrootdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputrootdir)})")  # root must exist
    #
    #
    #
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logfilehandler = logging.FileHandler(os.path.join(szoutputrootdir, f"{os.path.basename(__file__)[0:-3]}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.log"))
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler) # (don't forget to remove it!)

    logging.info(" ")
    logging.info(f"{os.path.basename(__file__)[0:-3]} exportshape: shapefile({os.path.basename(szshapefile)})")
    logging.info(f" - croptypeids: {lstszcroptypeids}")
    logging.info(f" - products:    {lstszproducts}")
    logging.info(f" - year:        {szyyyyyear}")
    logging.info(f" - output root: {szoutputrootdir}")
 
    try:
        #
        #    loop per product - gives decent performance indication
        # 
        for szproduct in lstszproducts:
            datetime_tick_all  = datetime.datetime.now()
            try:
                logging.info(" ")
                logging.info(f"{os.path.basename(__file__)[0:-3]} exportshape: product({szproduct}) start")
                #
                #
                #
                _exportshape(szshapefile, lstszcroptypeids, szyyyyyear, szoutputrootdir, [szproduct], verbose=verbose)
    
            except Exception:
                logging.error(f"{os.path.basename(__file__)[0:-3]} exportshape: product({szproduct}) exception", exc_info=True)
        
            finally:
                #
                #    remove handler we added at function start
                #
                logging.info(f"{os.path.basename(__file__)[0:-3]} exportshape: product({szproduct}) exit - {int( (datetime.datetime.now()-datetime_tick_all).total_seconds()/6/6)/100} hours")
    finally:
        logging.getLogger().removeHandler(logfilehandler)

#
#
#   
def main():
    """
    """
    if True:
        szshapefile      = r"C:\tmp\CropSARParcels\shp\CroptypesFlemishParcels_2019_20ha.shp"
        szoutrootdir     = r"C:\tmp\CropSARParcels\tif"
    else:
        szshapefile      = r"/vitodata/CropSAR/tmp/dominique/gee/CropSARParcels/shp/CroptypesFlemishParcels_2019_20ha.shp"
        szoutrootdir     = r"/vitodata/CropSAR/tmp/dominique/gee/CropSARParcels/tif"
        

    lstszcroptypeids = ['201', '202', '901', '904', '321', '91', '60']
    lstszyyyyyears   = ['2018', '2019', '2020', '2021']
    lstszproducts    = ["S2fapar", "S2ndvi", "S2sclconvmask", "S2sclcombimask", "S1gamma0", "S1sigma0"]
    verbose          = False

    for szyyyyyear in lstszyyyyyears:
        exportshape(szshapefile, lstszcroptypeids, szyyyyyear, szoutrootdir, lstszproducts, verbose=verbose)

#
#
#
if __name__ == '__main__':
    """
    """    
    print('starting main')
    main()
    print('finishing main')

