"""
exporting additional tiffs for existing parcels specified by a directory structure as

    szoutrootdir - PV100LC_lua - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy - productdescription.YYYY-MM-DD.tif
                                                                   - productdescription.YYYY-MM-DD.tif
                                                                   - ...
                               - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy
                               - ...
                 - PV100LC_lub - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy
                               - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy
                               - ...
                 - ...
             - ...
"""

import os
import logging
import datetime

import ee
if not ee.data._credentials: ee.Initialize()
import geeutils

from geebatch      import GEEExporter
from utils_patches import Patches


#
#
#
IAMRUNNINGONTHEMEP = False

#
#
#
def updateexistingpatches(szsrcrootdir, lstlanduseclasses, binvertlanduse, eeregion, szdstrootdir, lstszproducts, lstszyyyyyears, verbose=False):
    """
    :param lstszproducts: list of szproduct

    """

    #
    #
    #
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    #
    # some checks
    #
    if not os.path.isdir(szsrcrootdir)                : raise ValueError(f"invalid source directory szsrcrootdir ({str(szsrcrootdir)})")       # src dir must exist

    if lstlanduseclasses is not None:
        if not isinstance(lstlanduseclasses, list)    : raise ValueError("lstlanduseclasses expected to be a list")
        for ilanduse in lstlanduseclasses:
            if not isinstance(ilanduse, int)          : raise ValueError("lstlanduseclasses expected to be a list of integers")
            if not (0 <= ilanduse <= 200)             : raise ValueError("ridicule landuse class value (expected [0,200])")
    
    if not isinstance(binvertlanduse, bool)           : raise ValueError("binvertlanduse expected to be a boolean")
    if eeregion is not None:
        if not isinstance(eeregion, ee.Geometry)      : raise ValueError("eeregion expected to be an ee.Geometry")

    if not os.path.isdir(szdstrootdir)                : raise ValueError(f"invalid destination directory szdstrootdir ({str(szdstrootdir)})")  # src dir must exist
    if not isinstance(lstszyyyyyears, list)           : raise ValueError("lstszyyyyyears expected to be a list")

    lstszyyyyyears = [ str(int(szyyyyyear)) for szyyyyyear in lstszyyyyyears if (1957 <= int(szyyyyyear) <= 2525) ]                            # if man is still alive
    if (len(lstszyyyyyears) <=0)                      : raise ValueError("lstszyyyyyears contains no valid szyyyyyears")

    lstszproducts  = GEEExporter.saneproducts(lstszproducts)  # assert at least one exportable product specified
    #
    #    logging to file
    #
    datetime_tick_all  = datetime.datetime.now()
    szoutputbasename=os.path.join(szdstrootdir, f"{os.path.basename(__file__)[0:-3]}_{datetime_tick_all.strftime('%Y%m%d%H%M%S')}")
    logfilehandler = logging.FileHandler(szoutputbasename + ".log")
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s %(levelname).4s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger().addHandler(logfilehandler) # (don't forget to remove it!)
    try:
        #
        #    initial log
        #
        logging.info(" ")
        logging.info(f"{os.path.basename(__file__)[0:-3]}")
        logging.info(f"    src root dir: {szsrcrootdir}")
        logging.info(f"    land use:     {lstlanduseclasses if lstlanduseclasses is not None else 'any'} {' - inverted' if binvertlanduse else ''}")
        logging.info(f"    roi:          {'specified region' if eeregion is not None else 'any'}")
        logging.info(f"    dst root dir: {szdstrootdir}")
        logging.info(f"    products:     {lstszproducts}")
        logging.info(f"    years:        {lstszyyyyyears}")
        logging.info(" ")
        #
        #    find land use directories in source root (szsrcrootdir) and restrict them according to (lstlanduseclasses, binvertlanduse)
        #
        landusedirectories = Patches.findlandusedirectoriesdict(szsrcrootdir)
        if lstlanduseclasses:
            if not binvertlanduse:
                landusedirectories = {ilu:lud for ilu,lud in landusedirectories.items() if ilu in lstlanduseclasses}
            else:
                landusedirectories = {ilu:lud for ilu,lud in landusedirectories.items() if ilu not in lstlanduseclasses}
        #
        #    find patch directories in source land-use directories and restrict them to the eeregion
        #
        for ilanduse, landusedirectory in landusedirectories.items(): 
            patchIDdirectories = Patches.findpatchIDdirectoriesdict(landusedirectory)
            for szpatchID in patchIDdirectories.keys():
                fpointlon, fpointlat = Patches.tuplelonlatfrompatchID(szpatchID)
                if not eeregion is None:
                    if not ee.Geometry.Point(fpointlon, fpointlat).containedIn(eeregion, maxError=1).getInfo():
                        continue
                #
                #    now we know destination ilanduse, fpointlon, fpointlat => find or make its destination directory
                #
                patchdestinationdirectory = Patches.getpatchdirectoryfromLonLat(Patches.getlandusedirectory(szdstrootdir, ilanduse), fpointlon, fpointlat)
                #
                #    evaluate potential existing products in destination
                #
                patchproductsfilesdict = Patches.findproductsfilesdict(patchdestinationdirectory) # find all products there - limit directory scans
                #
                #    
                #
                for szproduct in lstszproducts:
                    #
                    #    count existing product entries per year - if any
                    #
                    patchproductsdict = {}
                    for szcollectiondescription, productfilesdict in patchproductsfilesdict.items():
                        #
                        #    only consider entries in patchproductsfilesdict where szcollectiondescription starts with current szproduct
                        #
                        if not szcollectiondescription.startswith(szproduct):
                            continue
    
                        sziso8601dates = sorted(productfilesdict.keys())
                        szyyyyyears    = sorted(list(set([sziso8601date[0:4] for sziso8601date in sziso8601dates]))) # sets are not guaranteed to be sorted
                        if szyyyyyears:                                                                              # defense again potential bug productfilesdict = {}
                            for szyyyyyear in szyyyyyears:
                                countentries = len([sziso8601date for sziso8601date in sziso8601dates if sziso8601date.startswith(szyyyyyear)])
                                if 0 < countentries:
                                    #
                                    #
                                    #
                                    if not szcollectiondescription in patchproductsdict:
                                        patchproductsdict.update({szcollectiondescription : {}})
                                    patchproductsdict.get(szcollectiondescription).update({szyyyyyear : countentries})
                    #
                    #    example patchproductsdict: for szpatchID, szproduct 'S2ndvi'
                    #        {
                    #            'S2ndvi': {'2020': 63, '2021': 59}}
                    #        }
                    #
                    #    example patchproductsdict: for szpatchID, szproduct 'S1gamma0'
                    #        {
                    #            'S1gamma0_VV_ASC': {'2020': 60,  '2021': 55},
                    #            'S1gamma0_VH_ASC': {'2020': 60,  '2021': 55},
                    #            'S1gamma0_VV_DES': {'2020': 122, '2021': 119},
                    #            'S1gamma0_VH_DES': {'2020': 122, '2021': 119}
                    #        }
                    #
                    #    now we need a heuristic to check if the actual szproduct in the specified lstszproducts
                    #    is considered "already present" in the destination per specified year in lstszyyyyyears
                    #    bearing in mind the mismatch between the szproduct specifications of the GEEExporter
                    #    and the szcollectiondescription strings found in the actual filenames by Patches.findproductsfilesdict
                    #
                    #
                    #    we'll use the minimum over all descriptions present. this is NOT fail safe:
                    #    e.g. : assume S1gamma0_VV_ASC being the first, crashed halfway => S1gamma0_VV_DES did not start
                    #           but S1gamma0 is considered to be present.
                    #    explicit requesting both _ASC and _DES to be present does not work; for some regions only one of ASC/DES exist.
                    #
                    for szyyyyyear in lstszyyyyyears:
                        minentriesfound = None
                        for szcollectiondescription, countentriesdict in patchproductsdict.items():
                            entriesfound    = countentriesdict.get(szyyyyyear, 0)
                            minentriesfound = entriesfound if minentriesfound is None else min(minentriesfound, entriesfound)
                        if minentriesfound is None: minentriesfound = 0
                        #
                        #
                        #
                        if 0 < minentriesfound:
                            logging.info(f"szpatchID({szpatchID}) szproduct({szproduct}) szyyyyyear({szyyyyyear}) minentriesfound({minentriesfound}) - considered present")
                        else:
                            logging.info(f"szpatchID({szpatchID}) szproduct({szproduct}) szyyyyyear({szyyyyyear}) minentriesfound({minentriesfound}) - considered absent")
                            #
                            #    exporting per product requires overhead, but no way i'm going to mess with intersections of 
                            #    available dates between different products to get some marginal performance  gain
                            #
                            eepoint    = ee.Geometry.Point(fpointlon, fpointlat)
                            eedatefrom = ee.Date(str(int(szyyyyyear)    )  + "-01-01" )
                            eedatetill = ee.Date(str(int(szyyyyyear) + 1)  + "-01-01" )
                            GEEExporter([szproduct]).exportimages(eepoint, eedatefrom, eedatetill, patchdestinationdirectory, verbose=verbose)

    finally:
        #
        #    remove handler we added at function start
        #
        logging.info(f"{os.path.basename(__file__)[0:-3]} exit - {int( (datetime.datetime.now()-datetime_tick_all).total_seconds()/6/6)/100} hours")
        logging.getLogger().removeHandler(logfilehandler)
                            
#
#
#   
def main():
    """
    """
    lstszproducts     = ["S2fapar", "S2ndvi", "S2sclcombimask", "S1gamma0"]
    lstszproducts     = ["S2fapar"]
    lstszproducts     = ["S1Agamma0"]
    lstszyyyyyears    = ['2018', '2019', '2020', '2021']
    lstszyyyyyears    = ['2021',2020]
    lstszyyyyyears    = ['2021']
    lstlanduseclasses = [40]                                                 # Cultivated and managed vegetation / agriculture.
    binvertlanduse    = False
    eeregion          = geeutils.bobspoint.buffer(100000)
    szsrcrootdir      = r"/vitodata/CropSAR/tmp/dominique/gee/tmp" if IAMRUNNINGONTHEMEP else r"O:\tmp\dominique\gee\gee_points" #r"C:\tmp"
    szdstrootdir      = r"/vitodata/CropSAR/tmp/dominique/gee/tmp" if IAMRUNNINGONTHEMEP else r"C:\tmp" #r"O:\tmp\dominique\gee\gee_points" #
    verbose           = False
    updateexistingpatches(szsrcrootdir, lstlanduseclasses, binvertlanduse, eeregion, szdstrootdir, lstszproducts, lstszyyyyyears, verbose=verbose)

#
#
#
if __name__ == '__main__':
    """
    """    
    print('starting main')
    main()
    print('finishing main')