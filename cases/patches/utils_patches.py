"""
utilities related to patches
- ad-hoc files and directory naming convention
- selection of random points
"""

import os
import logging
import random
import time
import pandas
import ee


#
#
#
class Patches:
    """
    utilities find, create and examine files and directories according ad-hoc convention:
        szoutrootdir - PV100LC_lua - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy - productdescription.YYYY-MM-DD.tif
                                                                       - productdescription.YYYY-MM-DD.tif
                                                                       - ...
                                   - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy
                                   - ...
                     - PV100LC_lub - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy
                                   - Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy
                                   - ...
                     - ...
        e.g. O:\tmp\dominique\gee\gee_points\PV100LC_20\Lon0000.11172572_Lat0013.16296544\S1sigma0_VH_ASC.2020-01-12.tif

        land use (lua, ... in PV100LC_lua, ...) uses 'COPERNICUS/Landcover/100m/Proba-V-C3/Global' 'discrete_classification'
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
            
        longitude and latitude coordinates (Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy) are formatted "013.8f"

    """
    
    @staticmethod
    def _gprefixeddirectoriestuples(szsrcdirpath, szprefix):
    
        if not os.path.isdir(szsrcdirpath) : raise ValueError(f"invalid source directory szsrcdirpath ({str(szsrcdirpath)})")      # src dir must exist
    
        for direntry in os.scandir(szsrcdirpath):                     # iterate DirEntry objects for given szsrcdirpath
            if not direntry.is_dir():                      continue   # only consider directories
            #
            # assume directory names format start with: 'szprefix'
            #
            if not (len(direntry.name) > len(szprefix)):   continue   # at least more than szprefix
            if not (direntry.name.startswith(szprefix)):   continue   # TODO: relax on case?
            #
            #
            #
            szkey = direntry.name[len(szprefix):]
            szdir = direntry.path
            yield (szkey, szdir)

    @staticmethod
    def findlandusedirectoriesdict(szsrcdirpath):
        """
        search szsrcdirpath for subdirectories honoring the szoutrootdir - PV100LC_ilanduse format
        returns dict e.g.:
        {
            40,  'C:\tmp\PV100LC_40',
            50,  'C:\tmp\PV100LC_50',
           111,  'C:\tmp\PV100LC_111',
            ...
        }
        """
        dirsdict = {}
        for szcroptype, szdir in Patches._gprefixeddirectoriestuples(szsrcdirpath, 'PV100LC_'):
            try:
                dirsdict.update({int(szcroptype): szdir})
            except:
                pass
        return dirsdict

    @staticmethod
    def getlandusedirectory(szsrcdirpath, ilanduse):
        """
        attempt to check whether subdirectory szsrcdirpath\PV100LC_ilanduse exists,
        or create it if possible (just the subdirectory, not the full path)
        """
        if not os.path.isdir(szsrcdirpath) : raise ValueError(f"invalid source directory szsrcdirpath ({str(szsrcdirpath)})")      # src dir must exist
        szdir = os.path.join(szsrcdirpath, 'PV100LC_' + str(int(ilanduse)))
        if not os.path.isdir(szdir): os.mkdir(szdir) # mode 0o777 should be default
        return szdir

    @staticmethod
    def szpatchIDfromLonLat(fpointlon, fpointlat):
        """
        force Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy format
        """
        szpointlon     = f"{float(fpointlon):013.8f}"
        szpointlat     = f"{float(fpointlat):013.8f}"
        szpatchID      = f"Lon{szpointlon}_Lat{szpointlat}"
        return szpatchID

    @staticmethod
    def tuplelonlatfrompatchID(szpatchID):
        """
        force Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy format
        """
        # yes, real programmers would use a regex, but I'm far too lazy...
        if not len(szpatchID) == 33:        raise ValueError(f"invalid patch ID string szpatchID ({str(szpatchID)})")
        if not szpatchID[ 0: 3] == 'Lon':   raise ValueError(f"invalid patch ID string szpatchID ({str(szpatchID)})")
        if not szpatchID[16]    == '_':     raise ValueError(f"invalid patch ID string szpatchID ({str(szpatchID)})")
        if not szpatchID[17:20] == 'Lat':   raise ValueError(f"invalid patch ID string szpatchID ({str(szpatchID)})")
        try:
            pointlon = float(szpatchID[ 3:16])
            pointlat = float(szpatchID[20:33])
            return (pointlon, pointlat)
        except:
            raise ValueError(f"invalid patch ID string szpatchID ({str(szpatchID)})")
    
    @staticmethod
    def findpatchIDdirectoriesdict(szsrcdirpath):
        """
        search szsrcdirpath for subdirectories honoring the szsrcdirpath\Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy format
        returns dict e.g.:
        {
            'Lon0024.25218162_Lat0041.04185249', 'C:\tmp\PV100LC_40\Lon0024.25218162_Lat0041.04185249',
            'Lon-008.96998508_Lat0032.23450423', 'C:\tmp\PV100LC_40\Lon-008.96998508_Lat0032.23450423',
            ...
        }
        """
        if not os.path.isdir(szsrcdirpath) : raise ValueError(f"invalid source directory szsrcdirpath ({str(szsrcdirpath)})")      # src dir must exist

        patchdirsdict = {}    
        for direntry in os.scandir(szsrcdirpath):                     # iterate DirEntry objects for given szsrcdirpath
            if not direntry.is_dir():                      continue   # only consider directories
            #
            # q&d check and decode - expect LonXXXX.XXXXXXXX_LatXXXX.XXXXXXXX ("patchID")
            #
            try:
                Patches.tuplelonlatfrompatchID(direntry.name)
            except:
                continue
            patchdirsdict.update({direntry.name: direntry.path})

        return patchdirsdict

    @staticmethod
    def getpatchdirectoryfromID(szsrcdirpath, szpatchID):
        """
        check if szpatchID honors the Lonxxxx.xxxxxxxx_Latyyyy.yyyyyyyy format,
        attempt to check whether subdirectory szsrcdirpath\szpatchID exists, and 
        or create it if possible (just the subdirectory, not the full path)
        """
        
        try:
            Patches.tuplelonlatfrompatchID(szpatchID)
        except:
            raise ValueError(f"invalid patch ID string szpatchID ({str(szpatchID)})")

        if not os.path.isdir(szsrcdirpath): raise ValueError(f"invalid source directory szsrcdirpath ({str(szsrcdirpath)})")      # src dir must exist
        
        szdir = os.path.join(szsrcdirpath, szpatchID)
        if not os.path.isdir(szdir): os.mkdir(szdir) # mode 0o777 should be default
        return szdir

    @staticmethod
    def getpatchdirectoryfromLonLat(szsrcdirpath, fpointlon, fpointlat):
        return Patches.getpatchdirectoryfromID(szsrcdirpath, Patches.szpatchIDfromLonLat(fpointlon, fpointlat))
        
    @staticmethod
    def findproductsfilesdict(szsrcdirpath, szdescriptionheader=None, verbose=False):
        """
        search szsrcdirpath for files assuming filenames being formatted : szdescription.YYYY-MM-DD.tif
        
            with 'szdescriptionheader' None (default) all different 'szdescription' will be reported
        
            with 'szdescriptionheader' specified, e.g. 'S2ndvi' or 'S1gamma0',
            anly 'szdescription' STARTING WITH 'szdescriptionheader' will be reported; there is no 1-1 relation
        
        returns dict of dicts, e.g. (szdescriptionheader=None => 'all' products:
        {
            'S2ndvi':    {
                            '2020-01-05':'C:\tmp\S2ndvi.2020-01-05.tif',
                            '2020-01-09':'C:\tmp\S2ndvi.2020-01-09.tif',
                            ...
                            '2021-12-26':'C:\tmp\S2ndvi.2021-12-26.tif'
                          },
            'S2scl':     {
                            '2020-01-05':'C:\tmp\S2scl.2020-01-05.tif',
                            '2020-01-09':'C:\tmp\S2scl.2020-01-09.tif',
                            ...
                            '2021-12-26':'C:\tmp\S2scl.2021-12-26.tif'
                          },
            ...
        }
    
        """
        if not os.path.isdir(szsrcdirpath) : raise ValueError(f"invalid source directory szsrcdirpath ({str(szsrcdirpath)})")      # src dir must exist
    
        productsfilesdict = {}
        for direntry in os.scandir(szsrcdirpath):                 # iterate DirEntry objects for given szsrcdirpath
            if not direntry.is_file():                 continue   # only consider files
            #
            # assume filenames format being: prefix.YYYY-MM-DD.tif
            #
            if not (len(direntry.name) > 15):          continue   # at least more than '.2020-02-01.tif'
            if not direntry.name.endswith('.tif'):     continue   # only consider '.tif's
            #
            #
            #
            szcollectiondescription  = direntry.name[  0 : -15]   # e.g. 'S2ndvi'
            sziso8601date            = direntry.name[-14 :  -4]   # e.g. '2020-02-01'
            szfullfilename           = direntry.path              # e.g. 'C:\tmp\S2ndvi.2020-02-01.tif'
            #
            #    skip products with szcollectiondescription not starting with (optional) szdescriptionheader
            #
            if szdescriptionheader:
                if not szcollectiondescription.startswith(szdescriptionheader):
                    continue
            #
            #
            #
            if not szcollectiondescription in productsfilesdict:
                productsfilesdict.update({szcollectiondescription : {}})
            productsfilesdict.get(szcollectiondescription).update({sziso8601date : szfullfilename})

        if verbose:
            #logging.info("Patches: number of products in dict : %10s" % (len(productsfilesdict.keys()),))
            for szcollectiondescription, productfilesdict in productsfilesdict.items():
                sziso8601dates = sorted(productfilesdict.keys())
                szyyyyyears    = sorted(list(set([sziso8601date[0:4] for sziso8601date in sziso8601dates]))) # sets are not guaranteed to be sorted
                logging.info("- product: %-20s files: %5s - first: %s last %s - years: %s" % (
                    szcollectiondescription, 
                    len(sziso8601dates),
                    sziso8601dates[0],
                    sziso8601dates[-1],
                    szyyyyyears))
            
        return productsfilesdict

    @staticmethod
    def reportpatchproductsdict(szsrcdirpath, verbose=False):
        """
        {
            'S2ndvi':    {
                            "2018": 25,
                            "2019": 36
                        },
            'S2fapar':  {
                            "2017": 3,
                            "2020": 18
                        },
            ...
        }
        """
        productsfilesdict = Patches.findproductsfilesdict(szsrcdirpath, verbose=verbose)
        
        patchproductsdict = {}
        for szcollectiondescription, productfilesdict in productsfilesdict.items():
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
        
        return patchproductsdict


#
#
#
class RandomPoints():
    """
    https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global
        "The CGLS-LC100 products in version 3 (collection 3) cover the geographic area from 
        longitude 180E to 180W and latitude 78.25N to 60S."
    
    => hence we should limit our points to the valid range.
    
    being sick and tired of it, and after a serious amount of struggling with system:footprint, image.geometry(), 
    manually specifying geodesic and non-geodesic geometries, intersections and projections, I give up on using
    image.sample(...); I cannot find a way to get a bounded geometry or image, which behaves as I want it to do; 
    just limit the image to its valid area, and take a random sample from it.
    
    => therefore this naive approach using Python random.random() which takes some time,
       but at least we (think we) know what we're doing.



    discrete_classification Class Table:
        
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
    
    def __init__(self, lstlanduseclasses=[0, 70, 80, 200], binvertlanduse=True, eeregion=None, verbose=True):
        """
        by default discarding Unknown, Snow and ice, Permanent water bodies, Oceans, seas.
        """
        
        #
        # some type checks. just to drive hard core Pythonians up the wall.
        #
        if not isinstance(lstlanduseclasses, list)    : raise ValueError("lstlanduseclasses expected to be a list")
        for ilanduse in lstlanduseclasses:
            if not isinstance(ilanduse, int)          : raise ValueError("lstlanduseclasses expected to be a list of integers")
            if not (0 <= ilanduse <= 200)             : raise ValueError("ridicule landuse class value (expected [0,200])")

        if not isinstance(binvertlanduse, bool)       : raise ValueError("binvertlanduse expected to be a boolean")
        if eeregion is not None:
            if not isinstance(eeregion, ee.Geometry)  : raise ValueError("eeregion expected to be an ee.Geometry")

        #
        # using discrete_classification band of most recent landcover image
        #
        self._eelandcoverclassification = (ee.ImageCollection('COPERNICUS/Landcover/100m/Proba-V-C3/Global')
                                           .sort('system:time_start', False)   # reverse sort
                                           .first()                            # most recent
                                           .select('discrete_classification')  # Land cover classifications 0..200
                                           .unmask(0, sameFootprint=False))    # 0 = Unknown; in gee used as mask

        self._eeregion          = eeregion
        self._lstlanduseclasses = lstlanduseclasses
        self._binvertlanduse    = binvertlanduse
        
        self._maxattempts       = None # endless
        self._verbose           = verbose


    def getpoint(self):
        """
        (try to) get a random point
        """
        iattempt = 0
        while True:
            iattempt += 1
            if self._maxattempts and self._maxattempts < iattempt:
                raise ValueError(f"RandomPoints.getpoint - failed to find valid point after {self._maxattempts} attempts.")
            #
            #
            #
            if self._eeregion is None:
                #
                #    covered geographic area from longitude 180E to 180W and latitude 78.25N to 60S.
                #
                longitude  = (1 - random.random())*360. - 180.
                latitude   = random.uniform(-60.0, 78.25)
                eepoint    = ee.Geometry.Point(longitude, latitude)
                pointlon   = float(f"{eepoint.coordinates().get(0).getInfo():013.8f}")
                pointlat   = float(f"{eepoint.coordinates().get(1).getInfo():013.8f}")
            else:
                #
                #    client specified region
                #
                eepoint  = self._eelandcoverclassification.sample(
                    region=self._eeregion, numPixels=1, seed=int(time.time()), 
                    dropNulls=True, geometries=True).geometry()
                pointlon = float(f"{eepoint.coordinates().get(0).getInfo():013.8f}")
                pointlat = float(f"{eepoint.coordinates().get(1).getInfo():013.8f}")
        
            eepoint    = ee.Geometry.Point(pointlon, pointlat)
            szpointlon = f"{eepoint.coordinates().get(0).getInfo():013.8f}"
            szpointlat = f"{eepoint.coordinates().get(1).getInfo():013.8f}"
            pointlon   = float(szpointlon)
            pointlat   = float(szpointlat)
            #
            #    check if point is in (optional) region - if "sample" works this is obsolete, especially due to the 'getInfo()'
            #
            if self._eeregion is not None:
                if not eepoint.containedIn(self._eeregion, maxError=1).getInfo():
                    if (self._verbose): print(f"RandomPoints.getpoint attempt {iattempt} - skipping point({szpointlon}, {szpointlat}): beyond specified region ")
                    continue
            #
            #    check landuse - point itself
            #
            landuseclass = self._eelandcoverclassification.reduceRegion(
                ee.Reducer.mode().unweighted(), eepoint).values().get(0).getInfo()

            if not (self._binvertlanduse ^ (landuseclass in self._lstlanduseclasses)):
                if (self._verbose): print(f"RandomPoints.getpoint attempt {iattempt} - skipping point({szpointlon}, {szpointlat}): landuse is {landuseclass} ")
                continue
            #
            #    check modal landuse - determined by about mode in 1km diameter
            #
            modallanduseclass = self._eelandcoverclassification.reduceRegion(
                ee.Reducer.mode().unweighted(), eepoint.buffer(500, maxError=1)).values().get(0).getInfo()
            
            if not (self._binvertlanduse ^ (modallanduseclass in self._lstlanduseclasses)):
                if (self._verbose): print(f"RandomPoints.getpoint attempt {iattempt} - skipping point({szpointlon}, {szpointlat}): modal landuse is {modallanduseclass} ")
                continue
            #
            #
            #
            if (self._verbose): print(f"RandomPoints.getpoint attempt {iattempt} - yielding point({szpointlon}, {szpointlat}): landuse is {landuseclass} ")
            #
            #    to fit in with our "patches" utilities, besides the actual point, we do need the (modal)landuse
            #    while we're at it, we can store some additional info as well.
            #
            point = dict()
            point['eepoint']        = eepoint
            point['szpointlon']     = szpointlon
            point['szpointlat']     = szpointlat
            point['fpointlon']      = pointlon
            point['fpointlat']      = pointlat
            point['ipointlanduse']  = landuseclass
            point['ipatchlanduse']  = modallanduseclass
            
            return point

#
#
#
if __name__ == "__main__":
    """
    example: create readable csv: for each patch_product the number of files per year

                                                                  , 2019, 2020, 2021
        Lon-004.11650575_Lat0048.15318369_S2ndvi                  ,   67,   69,   82
        Lon-004.11650575_Lat0048.15318369_S2sclconvmask           ,   67,   69,   82
        Lon0005.89060131_Lat0010.12517051_S2ndvi                  ,   84,   84,   84
        Lon0005.89060131_Lat0010.12517051_S2sclcombimask          ,   84,   84,   84
        ...

    """
    exit(0)
    #
    #
    #
    overviewdict = {}
    #
    #
    #
    landusedirectories = Patches.findlandusedirectoriesdict(r"C:\tmp")
    #
    #    {    
    #        40: 'C:\\tmp\\PV100LC_40', 
    #        50: 'C:\\tmp\\PV100LC_50',
    #        ...
    #    }
    #
    print(landusedirectories)
    for ilanduse, landusedirectory in landusedirectories.items():
        patchIDdirectories = Patches.findpatchIDdirectoriesdict(landusedirectory)
        #
        #    {
        #        'Lon-004.11650575_Lat0048.15318369': 'C:\\tmp\\PV100LC_40\\Lon-004.11650575_Lat0048.15318369', 
        #        'Lon-008.96998508_Lat0032.23450423': 'C:\\tmp\\PV100LC_40\\Lon-008.96998508_Lat0032.23450423', 
        #        'Lon-054.52156422_Lat-023.92644223': 'C:\\tmp\\PV100LC_40\\Lon-054.52156422_Lat-023.92644223',
        #        ...
        #    }
        #
        for szpatchID, patchIDdirectory in patchIDdirectories.items():
            patchproducts = Patches.reportpatchproductsdict(patchIDdirectory)
            #    {
            #        'S2ndvi': {'2019': 67, '2020': 69, '2021': 82}, 
            #        'S2sclcombimask': {'2019': 64, '2020': 69, '2021': 82}, 
            #        'S2sclconvmask': {'2019': 67, '2020': 69, '2021': 82}
            #        ...
            #    }
            #
            for szcollectiondescription, countentriesdict in patchproducts.items():
                szindex = szpatchID + "_" + f"{szcollectiondescription:40s}"
                if not szindex in overviewdict:
                    overviewdict.update({szindex : {}})
                overviewdict.get(szindex).update(countentriesdict)

    pandas.DataFrame.from_dict(overviewdict, orient='index').to_csv(r"C:\tmp\overview.csv", float_format="%5.0f", na_rep="     ")
