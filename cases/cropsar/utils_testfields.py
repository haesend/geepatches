"""
utilities related to test-fields as specified in CropSAR-I 'fields' shape files
- recovered from CropSAR I project
- added ad-hoc files and directory naming convention for this case study
"""

import os
import logging

import osgeo.gdal
import geopandas


#
#
#
class CropSARParcels:
    """
    utilities to read, filter and convert the shape files describing the parcels used in CropSAR

        assumes (source) shape files containing: 
        - attribute 'fieldID'   : some unique parcel identifier
        - attribute 'croptype'  : crop type id (string) representing the crop in the parcel. eg. '901' for Potato ('niet-vroeg') ...
        - attribute 'area'      : area of the parcels in square meter
    
        gotcha's: 
        - GeoJSON & fiona have been fighting flame wars related to overwriting of existing files
        - fiona (gdal) needs to be setup properly (environment variables), otherwise crs's disappear silently


    utilities find, create and examine files and directories according ad-hoc convention:
        szoutrootdir - croptype_X - fieldID_xxxxxxxxxxxxxxxx - productdescription.YYYY-MM-DD.tif
                                                             - productdescription.YYYY-MM-DD.tif
                                                             - ...
                                  - fieldID_xxxxxxxxxxxxxxxx
                                  - ...
                     - croptype_Y - fieldID_yyyyyyyyyyyyyyyy
                                  - fieldID_yyyyyyyyyyyyyyyy
                                  - ...
                     - ...

    """

    CROPTYPESDICT = {
        201:'Maize (korrelmais)',
        202:'Maize (silomais)',
        901:'Potato (niet-vroeg)',
        904:'Potato (vroeg)',
        311:'Winter Wheat',
        321:'Winter Barley',
         71:'Fodder Beet',
         91:'Sugar Beet',
         60:'Grassland' }

    #
    #
    #
    @staticmethod
    def cropsar_shptopandas(szshapefile, lstfieldIDs=None, lstszcroptypeids=None, iminimumfieldareainsquaremeters=None, imaximumfieldareainsquaremeters=None, verbose=True):
        """
        Read and filter shape file into geopandas.GeoDataFrame. Mind you, a geojson might work too.

        :param szshapefile: input shape file (containing attributes 'fieldID', 'croptype', 'area') 
        :param lstfieldIDs: optional (filter) list of parcel identifiers e.g. ['0000280600C79D76', '0000280600C79D79']
        :param lstszcroptypeids: optional (filter) list of crops e.g. ['201', '202', '901']
        :param iminimumfieldareainsquaremeters: optional (filter) minimum area (in square meters) of the parcels
        :param imaximumfieldareainsquaremeters: optional (filter) maximum area (in square meters) of the parcels
        :param verbose: print stats
        """
        #
        #    read the shape file into geopandas.geodataframe.GeoDataFrame
        #    - actually .dbf file as table (if it is there)
        #    - extended with one additional column 'geometry' containing the shape files polygons
        #
        parcelsgeodataframe = geopandas.read_file(szshapefile)
        #
        #
        #
        cntallfields = len(parcelsgeodataframe.index)
        if verbose: 
            logging.info("")
            logging.info("CropSARParcels: initial number of fields   : %10s ( file  : %s )" % (cntallfields, os.path.basename(szshapefile)))
        #
        #    filter on field identifiers
        #
        if lstfieldIDs is not None:
            parcelsgeodataframe = parcelsgeodataframe.loc[parcelsgeodataframe.loc[:, 'fieldID'].isin(lstfieldIDs), :]
            if verbose: logging.info("- remaining with specified fieldID(s)      : %10s (selected fieldID(s) : %s)" % (len(parcelsgeodataframe.index), lstfieldIDs))
        #
        #    filter on crop types
        #
        if lstszcroptypeids is not None:
            lstcroptypeids = [str(croptypeId) for croptypeId in lstszcroptypeids] # avoid problems where user forgot it had to be strings
            parcelsgeodataframe = parcelsgeodataframe.loc[parcelsgeodataframe.loc[:, 'croptype'].isin(lstcroptypeids), :]
            if verbose: logging.info("- remaining with specified croptype(s)     : %10s (selected croptype(s) : %s)" % (len(parcelsgeodataframe.index), lstcroptypeids))
        #
        #    filter on minimal area
        #
        if iminimumfieldareainsquaremeters is not None:
            if iminimumfieldareainsquaremeters > 0 :
                parcelsgeodataframe = parcelsgeodataframe.loc[parcelsgeodataframe.loc[:, 'area'] >= iminimumfieldareainsquaremeters, :]
                if verbose: logging.info("- remaining above minimum 'area'           : %10s (area : %s)" % (len(parcelsgeodataframe.index), iminimumfieldareainsquaremeters))
        #
        #    filter on maximal area
        #
        if imaximumfieldareainsquaremeters is not None:
            if imaximumfieldareainsquaremeters > 0 :
                parcelsgeodataframe = parcelsgeodataframe.loc[parcelsgeodataframe.loc[:, 'area'] <= imaximumfieldareainsquaremeters, :]
                if verbose: logging.info("- remaining below maximum 'area'           : %10s (area : %s)" % (len(parcelsgeodataframe.index), imaximumfieldareainsquaremeters))

        if verbose and (len(parcelsgeodataframe.index) < cntallfields):  
            logging.info("- final number of fields                   : %10s" % (len(parcelsgeodataframe.index), ))
        #
        #
        #
        if verbose: logging.info("")
        return parcelsgeodataframe

    #
    #
    #
    @staticmethod
    def cropsar_shptoshp(szsrcshapefile, szdstshapefile, lstfieldIDs=None, lstszcroptypeids=None, iminimumfieldareainsquaremeters=None, imaximumfieldareainsquaremeters=None, verbose=True):
        """
        Write filtered results as a shape file.
        """
        parcelsgeodataframe = CropSARParcels.cropsar_shptopandas(szsrcshapefile, lstfieldIDs, lstszcroptypeids, iminimumfieldareainsquaremeters, imaximumfieldareainsquaremeters, verbose)
        parcelsgeodataframe.to_file(szdstshapefile, driver="ESRI Shapefile")
        if verbose: logging.info("output shape file                        : %s ( full : %s )" % (os.path.basename(szdstshapefile), szdstshapefile))
        return parcelsgeodataframe

    #
    #
    #
    @staticmethod
    def cropsar_shptojson(szshapefile, szjsonfile, lstfieldIDs=None, lstszcroptypeids=None, iminimumfieldareainsquaremeters=None, imaximumfieldareainsquaremeters=None, verbose=True):
        """
        Write filtered results as a geojson file.
        """
        parcelsgeodataframe = CropSARParcels.cropsar_shptopandas(szshapefile, lstfieldIDs, lstszcroptypeids, iminimumfieldareainsquaremeters, imaximumfieldareainsquaremeters, verbose)
        parcelsgeodataframe.to_file(szjsonfile, driver="GeoJSON") # beware: "GeoJSON driver does not overwrite existing files." problems on and off since 2016
        if verbose: logging.info("output json file                         : %s ( full : %s )" % (os.path.basename(szjsonfile), szjsonfile))
        return parcelsgeodataframe

    #
    #
    #
    @staticmethod
    def shptojson(szshapefile, szgeojsonfile):
        """
        convert shape file to geojson
        """
        geopandas.read_file(szshapefile).to_file(szgeojsonfile, driver="GeoJSON") # beware: "GeoJSON driver does not overwrite existing files."problems on and off since 2016

    @staticmethod
    def jsontoshp(szgeojsonfile, szshapefile):
        """
        convert geojson to shape file
        """
        geopandas.read_file(szgeojsonfile).to_file(szshapefile, driver="ESRI Shapefile")

    @staticmethod
    def pandastoshp(geodataframe, szshapefile):
        """
        write geopandas.GeoDataFrame as shape file
        """
        geodataframe.to_file(szshapefile, driver="ESRI Shapefile")

    @staticmethod
    def pandastojson(geodataframe, szgeojsonfile):
        """
        write geopandas.GeoDataFrame as geojson file
        """
        geodataframe.to_file(szgeojsonfile, driver="GeoJSON")


    #######################################################################################
    #
    #
    #
    #######################################################################################

    @staticmethod
    def cropsar_shptomsk_dataset(szsrcshapefile, szreftiffile, verbose=False):
        return CropSARParcels.cropsar_shptomsk_tiff(szsrcshapefile, szreftiffile, szdsttiffile=None, verbose=verbose)

    @staticmethod
    def cropsar_shptomsk_tiff(szsrcshapefile, szreftiffile, szdsttiffile, verbose=False):
        """
        """
        refdataset             = osgeo.gdal.Open(szreftiffile)
        refxsize               = refdataset.RasterXSize
        refysize               = refdataset.RasterYSize
        refprojection          = refdataset.GetProjection()
        refgeotransform        = refdataset.GetGeoTransform()

        shapefile              = osgeo.ogr.Open(szsrcshapefile)   # open shape file. 
        shapelayer             = shapefile.GetLayer(0)            # shape files are supposed to have one single layer.
        #
        #    https://gdal.org/programs/gdal_rasterize.html
        #        "Note that on the fly reprojection of vector data to the coordinate system of the raster data is only supported since GDAL 2.1.0."
        #        seemingly boiler-plate-code below is now obsolete.
        #
        # shapelayerspaticalref  = shapelayer.GetSpatialRef()                # needed for transformation to products spatial ref
        #
        # refspatialreference    = osgeo.osr.SpatialReference(wkt = refprojection)
        # xform_shape_to_ref     = osgeo.osr.CoordinateTransformation(shapelayerspaticalref, refspatialreference)
        #
        # xformdriver            = osgeo.ogr.GetDriverByName('Memory')       # beware: ogr needs 'Memory', gdal needs 'MEM'. its a brave new world. 
        # xformdatasource        = xformdriver.CreateDataSource('dummy')     # beware: mandatory argument
        # xformlayer             = xformdatasource.CreateLayer('', srs = refspatialreference, geom_type=osgeo.ogr.wkbPolygon )
        # xformlayerdefn         = xformlayer.GetLayerDefn()
        #
        # for shapefeature in shapelayer:
        #     featuregeometry = shapefeature.GetGeometryRef()                # original geometry - typically EPSG:4326
        #     featuregeometry.Transform(xform_shape_to_ref)                  # reprojected to destination according to reference
        #     feature = osgeo.ogr.Feature(xformlayerdefn)
        #     feature.SetGeometry(featuregeometry)
        #     xformlayer.CreateFeature(feature)

        if verbose: 
            logging.info("CropSARParcels: number of features         : %10s ( file  : %s )" % (shapelayer.GetFeatureCount(), os.path.basename(szsrcshapefile)))
            logging.info("                destination raster         : %10s x %10s pixels"  % (refxsize,refysize))
            
        
        if szdsttiffile:
            dstdataset = refdataset.GetDriver().Create(szdsttiffile, refxsize, refysize, 1, osgeo.gdalconst.GDT_Byte, options = ['COMPRESS=DEFLATE'])
        else:
            dstdataset = osgeo.gdal.GetDriverByName('MEM').Create('', refxsize, refysize, 1, osgeo.gdalconst.GDT_Byte) # beware: ogr needs 'Memory', gdal needs 'MEM'. always fun. 
        dstdataset.SetGeoTransform(refgeotransform)
        dstdataset.SetProjection(refprojection)
        dstdataset.GetRasterBand(1).Fill(1)
        dstdataset.GetRasterBand(1).SetNoDataValue(0)
        osgeo.gdal.RasterizeLayer(dstdataset, [1], shapelayer, burn_values=[0])

        if szdsttiffile:
            dstdataset = None
            return osgeo.gdal.Open(szdsttiffile, osgeo.gdal.GA_Update)
        else:
            return dstdataset
            

    #######################################################################################
    #
    #    output directory structure convention: rootdir\croptype_i\fieldID_nnn
    #        i integer indicating croptype
    #        n string indicationg field id
    #
    #    product filename structure convention: szdescription.YYYY-MM-DD.tif
    #
    #######################################################################################
    
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
    def findcroptypedirectoriesdict(szsrcdirpath):
        """
        search szsrcdirpath for subdirectories honoring the szsrcdirpath\croptype_i format
        returns dict e.g.:
        {
             1,  'C:\tmp\croptype_1',
             4,  'C:\tmp\croptype_4',
            60,  'C:\tmp\croptype_60',
            ...
        }
        """
        dirsdict = {}
        for szcroptype, szdir in CropSARParcels._gprefixeddirectoriestuples(szsrcdirpath, 'croptype_'):
            try:
                dirsdict.update({int(szcroptype): szdir})
            except:
                pass
        return dirsdict

    @staticmethod
    def getcroptypedirectory(szsrcdirpath, icroptype):
        """
        attempt to check whether subdirectory szsrcdirpath\croptype_icroptype exists,
        or create it if possible (just the subdirectory, not the full path)
        """
        if not os.path.isdir(szsrcdirpath) : raise ValueError(f"invalid source directory szsrcdirpath ({str(szsrcdirpath)})")      # src dir must exist
        szdir = os.path.join(szsrcdirpath, 'croptype_' + str(int(icroptype)))
        if not os.path.isdir(szdir): os.mkdir(szdir) # mode 0o777 should be default
        return szdir

    @staticmethod
    def findfieldIDdirectoriesdict(szsrcdirpath):
        """
        search szsrcdirpath for subdirectories honoring the szsrcdirpath\fieldID_nnn format
        returns dict e.g.:
        {
            '000028085CBF6319', 'C:\tmp\fieldID_000028085CBF6319',
            '000028085B5099CA', 'C:\tmp\fieldID_000028085B5099CA',
            '000028085CE61976', 'C:\tmp\fieldID_000028085CE61976',
            ...
        }
        """
        return { szfieldID:szdir for szfieldID, szdir in CropSARParcels._gprefixeddirectoriestuples(szsrcdirpath, 'fieldID_') }

    @staticmethod
    def getfieldIDdirectory(szsrcdirpath, szfieldID):
        """
        attempt to check whether subdirectory szsrcdirpath\szfieldID exists,
        or create it if possible (just the subdirectory, not the full path)
        """
        if not os.path.isdir(szsrcdirpath) : raise ValueError(f"invalid source directory szsrcdirpath ({str(szsrcdirpath)})")      # src dir must exist
        szdir = os.path.join(szsrcdirpath, 'fieldID_' + str(szfieldID))
        if not os.path.isdir(szdir): os.mkdir(szdir) # mode 0o777 should be default
        return szdir

    @staticmethod
    def getparceldirectory(szsrcdirpath, icroptype, szfieldID):
        """
        attempt to check whether subdirectory szsrcdirpath\croptype_icroptype\szfieldID exists,
        or create it if possible (just the two last subdirectories, not the full path)
        """
        return CropSARParcels.getfieldIDdirectory(CropSARParcels.getcroptypedirectory(szsrcdirpath, icroptype), szfieldID)

    @staticmethod
    def findproductsfilesdict(szsrcdirpath, verbose=False):
        """
        search szsrcdirpath for files assuming filenames being formatted : szdescription.YYYY-MM-DD.tif
        returns dict of dicts, e.g.:
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
            #
            #
            if not szcollectiondescription in productsfilesdict:
                productsfilesdict.update({szcollectiondescription : {}})
            productsfilesdict.get(szcollectiondescription).update({sziso8601date : szfullfilename})

        if verbose:
            #logging.info("CropSARParcels: number of products in dict : %10s" % (len(productsfilesdict.keys()),))
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

    #
    #    just for fun
    #
    
    @staticmethod
    def lstproductsfromproductsfilesdict(productsfilesdict):
        return productsfilesdict.keys()

    @staticmethod
    def productfilesdictfromproductsfilesdict(productsfilesdict, szproductdescription):
        return productsfilesdict.get(szproductdescription, {})
    
    @staticmethod
    def lstproductdatesfromproductsfilesdict(productsfilesdict, szproductdescription):
        return sorted(CropSARParcels.productfilesdictfromproductsfilesdict(productsfilesdict, szproductdescription).keys())

