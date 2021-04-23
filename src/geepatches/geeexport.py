#
#  
#
import ee
import geemap
import geeutils
import os
import time
import math


"""
"""
class GEEExport(object):
    def __init__(self, geeproduct, eedatefrom, eedatetill, refprodroiradius, refprodscale = 1, maxrefprodscale = 1, refproduct = None, refprodroiradunits = 'pixels'):
        """
        starts from the obscure assumption that there will be one 'more-important' GEEProduct to be exported, 
        referred to as the reference (vet gaaf!), typically with a high resolution,
        and that there will be exports of 'related' GEEProduct-s, which should align with the reference-ses roi as good as possible,
        but with a resolution of their own original order of magnitude. e.g. self-PV333m (EPSG:4326) vs ref-S2 should become an UTM of approximately 300m.
        :param geeproduct: instance of a GEEProduct to be exported
        :param refprodroiradius: half-size of the more-ore-less square roi
        :param refprodscale: self-projection will be the refproduct projection downscaled by this factor. e.g. self-PV333m vs ref-S2 could be 32 or 16
        :param maxrefprodscale: maximum downscale factor that will be used in all related exports with same refproduct
        :param refproduct: instance of reference GEEProduct. defaults to self. normally the one with the highest resolution. exports will (try to) mirror its projection and roi
        :param refprodroiradunits: units of refprodroiradius. 'pixels' or 'meters'. defaults to 'pixels'. and whatever we do, off-by-ones will remain with us until the universe collapses.
        """
        self._geeproduct  = geeproduct
        self._eedatefrom  = eedatefrom
        self._eedatetill  = eedatetill
        self._refroirad   = refprodroiradius
        self._refroiunits = 'meters' if refprodroiradunits=='meters' else 'pixels'
        self._actrefscale = 1 if refprodscale is None else refprodscale 
        self._maxrefscale = 1 if maxrefprodscale is None else maxrefprodscale
        self._refproduct  = geeproduct if refproduct is None else refproduct


    def _starttask(self, task, iattempt=0):
        """
        """
        SLEEPTOOMUCHTASKSSECONDS = 120
        SLEEPAFTEREXCEPTION      = 120
        MAXACTIVETASKS           = 15
        MAXATTEMPTS              = 2

        def _activertaskscount():
            taskslist       = ee.batch.Task.list()
            activetaskslist = [task for task in taskslist if task.state in (
                ee.batch.Task.State.READY,
                ee.batch.Task.State.RUNNING,
                ee.batch.Task.State.CANCEL_REQUESTED)]
            activertaskscount = len(activetaskslist)
            print(f"{str(type(self).__name__)}._starttask._activertaskscount: {activertaskscount} tasks active")
            return activertaskscount

        try:
            while _activertaskscount() >= MAXACTIVETASKS:
                print(f"{str(type(self).__name__)}._starttask: sleep a while for gee")
                time.sleep(SLEEPTOOMUCHTASKSSECONDS)
            print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): starting task")
            task.start()
            print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): task started")
            return True

        except Exception as e:
            print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): exception: {str(e)}")
            iattempt += 1
            if iattempt < MAXATTEMPTS:
                #
                #    sleep a while, and try again.
                #
                time.sleep(SLEEPAFTEREXCEPTION)
                print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt-1}): exception - retry")
                self._starttask(task, iattempt)
            #
            #    give it up.
            #
            print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): exception - exits")
            return False


    def _getexportimage(self, eepoint, verbose=False):
        """
        """
        #      
        #    TODO: 
        #    - clip _maxrefscale on 1?
        #

        #
        #    Yet Another aTTempt trying to solve the oldest problem in imagery: obtain a reproducable, reasonable, simple roi:
        #
        #    start by selecting a reference image: in the reference product we search for an image
        #        temporal 'near' to the export start date, covering the eepoint to be exported for
        #
        #    BEWARE: 
        #    - eerefimage is limited to the first band of the reference product base collection
        #      this is *NOT* a clean solution. at the moment it is only needed for S1 where we need VV, VH + the 'angle'
        #      but 'angle' has a different resolution. we might consider to rethink the 'base collection' concept,
        #      remove it from the constructor, overload _export, ... if this problem persists.
        #
        #    - selecting a eerefimage works in most cases, but is not fail-safe. e.g. S1 can give 2 different images
        #      in the same region around an eepoint, with minor difference in start-time, but having a different crs. 
        #      e.g.
        #        ee.Image("COPERNICUS/S1_GRD/S1B_IW_GRDH_1SDV_20180716T172348_20180716T172413_011839_015CA0_02B2"): EPSG:32632 2018-07-16
        #        ee.Image("COPERNICUS/S1_GRD/S1B_IW_GRDH_1SDV_20180716T172413_20180716T172438_011839_015CA0_2CC9"): EPSG:32631 2018-07-16
        #
        #      this means that in case S1 or alikes, exporting different time series for the same point could cover 
        #      a different roi. this can be avoided by selecting an appropriate reference product.
        #      mind you: S2 is expected to have the same problem (at an UTM border with overlapping tiles) but far less often
        #
        #      if this turns out to be a showstopper, we can work around by implementing a simple "setrefimage(eeimage)" method
        #      and a condition "if not eerefimage: eerefimage = ..." but then the user is left out in the cold.
        #
        eerefimage = geeutils.someImageNear(self._refproduct.basecollection(), self._eedatefrom, eepoint).select(0)
        if verbose: print(f"{str(type(self).__name__)}._getexportimage: eerefimage\n {geeutils.szprojectioninfo(eerefimage)} id:{eerefimage.id().getInfo()}")
        #
        #    from this (single banded) eerefimage we obtain the projection to be used throughout the rest of the story
        #
        eerefproj  = eerefimage.projection()
        if verbose: print(f"{str(type(self).__name__)}._getexportimage: eerefproj\n {geeutils.szprojectioninfo(eerefproj)}")
        #
        #    the center of the roi to be exported, will be the center of a (theoretical) pixel of the (theoretical)
        #    reference image, reprojected to half its own resolution. this means that this eerefpoint is positioned exactly
        #    at the pixel borders of the (actual) reference image, near to the eepoint for which the roi is to be exported.
        #    in the eerefimage, in its own eerefproj, the roi will be symetrical around this eerefpoint.
        #
        eerefpoint = geeutils.centerpixelpoint(eepoint, eerefimage.reproject(eerefproj.scale(2*self._maxrefscale, 2*self._maxrefscale)))
        if verbose: print(f"{str(type(self).__name__)}._getexportimage: eerefpoint\n {geeutils.szprojectioninfo(eerefpoint)}")

        if (self._refroiunits == 'meters'):
            #
            #    ok, when starting to fiddle with "meters" iso pixels, 'symetrical' is relative, and off by one will not be solved in this lifetime.
            #    for now, when looking at the resulting area(), squareareaboundsroi seems more accurate,
            #    however, results from squarerasterboundsroi( meters/nominalScale) seem to match out intuition better
            #    in terms of dimensions and pixel-count
            #
            eeregion = geeutils.squareareaboundsroi(eerefpoint, self._refroirad, eerefimage, verbose=verbose)
            #eeregion = geeutils.squarerasterboundsroi(eerefpoint, self._refroirad/eerefproj.nominalScale().getInfo(), eerefimage)
        else:
            #
            #    if all goes well, we'll have even square dimensions
            #
            eeregion = geeutils.squarerasterboundsroi(eerefpoint, self._refroirad, eerefimage, verbose=verbose)
        if verbose: print(f"{str(type(self).__name__)}._getexportimage: eeregion\n {geeutils.szprojectioninfo(eeregion)}")
        
        eeimagecollection = self._geeproduct.getimagecollection(
                            eeregion, 
                            eerefproj.scale(self._actrefscale, self._actrefscale), # this scale (projection) will  will determine the pixel size of the ***internal*** image
                            self._eedatefrom, self._eedatetill, 
                            doscaleandflag=True, verbose=verbose)

        if eeimagecollection is None:
            print(f"{str(type(self).__name__)}._getexportimage: nothing to export - bailing out")
            return None

        #         #
        #         #    stack collection into single multiband image
        #         #
        #         eeimage = geeutils.stackcollectiontoimage(eeimagecollection, verbose=verbose)
        #         if verbose: print(f"{str(type(self).__name__)}._getexportimage: export image: {geeutils.szbandsinfo(eeimage)}")

        #
        #    stack collection into collection of multiband (timeseries) images, one per band
        #
        def addimagebandstostack(nextimage, previousstack):
            return ee.Image(previousstack).addBands(nextimage.rename(nextimage.date().format('YYYY-MM-dd')))

        eelistofallbandnames      = eeimagecollection.aggregate_array('system:band_names').flatten().distinct() # works (?) even if images have different band(name)s
        eeimagecollectionofstacks = ee.ImageCollection(eelistofallbandnames.map(lambda bandname: 
                                                                                (ee.Image(eeimagecollection
                                                                                          .filter(ee.Filter.listContains('system:band_names', bandname))
                                                                                          .select([bandname])
                                                                                          .sort('system:time_start')
                                                                                          .iterate(addimagebandstostack, ee.Image().select()))
                                                                                          .set('band', bandname))))
        #
        #    exporting requires the region; 
        #        Export.image.toDrive default would be 'the region defaults to the viewport at the time of invocation.'
        #        whatever that might be in python context.
        #        ee.batch.Export.image.toDrive comments say: 'Defaults to the image's region.' Nice.
        #
        #    at this point, the image has no ".geometry()" - seems to be unbound
        #    we could use .set('system:footprint', eeregion), then ".geometry()" is there
        #
        #         if False:
        #             print ("initial")
        #             print ("- stacked image - footprint", eeimage.get('system:footprint').getInfo())   # None
        #             print ("- stacked image - geometry",  eeimage.geometry().getInfo())                # unbound ( [[[-180, -90], [180, -90]...)
        #             print ("- stacked image - 'region'",  eeimage.get('region').getInfo())             # None
        #             print ("setting 'region' property")
        #             eeimage = eeimage.set('region', eeregion)
        #             print ("- stacked image - footprint", eeimage.get('system:footprint').getInfo())   # None
        #             print ("- stacked image - geometry",  eeimage.geometry().getInfo())                # unbound ( [[[-180, -90], [180, -90]...)
        #             print ("- stacked image - 'region'",  eeimage.get('region').getInfo())             # our eeregion
        #             print ("setting 'system:footprint' property")
        #             eeimage = eeimage.set('system:footprint', eeregion)
        #             print ("- stacked image - footprint", eeimage.get('system:footprint').getInfo())   # our eeregion
        #             print ("- stacked image - geometry",  eeimage.geometry().getInfo())                # our eeregion
        #             print ("- stacked image - 'region'",  eeimage.get('region').getInfo())             # our eeregion
        #
        #    but its not clear where and how gee internals use this 'system:footprint'; 
        #        should the image be clipped to this footprint too to have a consistent entity? 
        #        is 'system:footprint' just-another-property?
        #        what if 'system:footprint' is inconsistent with the crs in the image bands?
        #        ...
        #
        #    for the time being, we'll use an additional 'region' property
        #    so we can pass the eeregion we calculated by putting it in this property,
        #    without fearing a collapse of the known universe with the next gee update.
        #
        eeimagecollectionofstacks = eeimagecollectionofstacks.map(lambda eeimage: eeimage.set('region', eeregion))
        
        return eeimagecollectionofstacks

    
    def exportpoint(self, szid, eepoint, verbose=False):
        """
        """
        eeimagecollectionofstacks = self._getexportimage(eepoint, verbose=verbose)

        #
        #    exportimage is unbounded. we'll clip it to the region specified when instantiating the GEEExport,
        #    hoping this will give results consistent with the image tif obtained via exportpointtofile/exportpointtodrive
        #    (by clipping, its footprint and geometry seem to be updated to our region
        #
        #         print ("- exportpoint image - footprint", exportimage.get('system:footprint').getInfo())   # None
        #         print ("- exportpoint image - geometry",  exportimage.geometry().getInfo())                # unbound ( [[[-180, -90], [180, -90]...)
        #         print ("- exportpoint image - 'region'",  exportimage.get('region').getInfo())             # our eeregion
        #         exportimage = exportimage.clip(exportimage.get('region'))
        #         print ("- clipped image - footprint", exportimage.get('system:footprint').getInfo())       # our eeregion
        #         print ("- clipped image - geometry",  exportimage.geometry().getInfo())                    # our eeregion
        #         print ("- clipped image - 'region'",  exportimage.get('region').getInfo())                 # our eeregion

        eeimagecollectionofstacks = eeimagecollectionofstacks.map(lambda eeimage: eeimage.clip(eeimage.get('region')))

        #
        #    test/debug purposes
        #
        if True:
            imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
            for iIdx in range(eeimagecollectionofstacks.size().getInfo()):
                exportimage = ee.Image(imageslist.get(iIdx))
                geemap.ee_export_image(
                    exportimage,
                    filename=f"C:/Users/HAESEND/tmp/{str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill) + '_' + exportimage.get('band').getInfo() }.tif", 
                    scale=exportimage.projection().nominalScale(),                      # this scale only will determine the pixel size of the ***exported*** image
                    region=exportimage.geometry(), file_per_band=False)

        return eeimagecollectionofstacks


    def exportpointtofile(self, szid, eepoint, szdstpath, verbose=False):
        """
        :param szdstpath: destination filename or director name.
        
        in case szdstpath is an existing directory, a default filename will be generated,
        otherwise, in case the parent directory of szdstpath  is an existing directory, szdstpath will be considered as a base filename,
        otherwise an exception is raised
        """
        #
        #    filenames filenames filenames... I hate filenames...
        #
        szdstpath = os.path.normpath(szdstpath)
        if os.path.isdir(szdstpath) :
            szbasefilename = os.path.join(szdstpath, (str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill)))
        elif os.path.isdir(os.path.dirname(szdstpath)):
            szbasefilename = szdstpath
        else:
            raise ValueError(f"invalid szdstpath ({szdstpath})")
        if szbasefilename.lower().endswith(".tif"): szbasefilename = szbasefilename[:-4]
        if verbose: print(f"{str(type(self).__name__)}.exportpointtofile: base filename: {szbasefilename}")

        eeimagecollectionofstacks  = self._getexportimage(eepoint, verbose=verbose)
        imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
        for iIdx in range(eeimagecollectionofstacks.size().getInfo()):
            exportimage = ee.Image(imageslist.get(iIdx))
            exportband  = exportimage.get('band').getInfo()
            eeregion    = ee.Geometry(exportimage.get('region'))
            #
            #    and Yet Again: Terminal Touching pixels will be exported. Shinking the original roi with 1% of its pixel size... and pray.
            #    TODO: implement in exportpointtodrive too
            #
            exportregion = eeregion.buffer(-0.01, proj=exportimage.projection())
            if verbose:
                eeregionpixelcount     = exportimage.select(0).unmask(sameFootprint=False).reduceRegion(ee.Reducer.count(), eeregion)
                exportregionpixelcount = exportimage.select(0).unmask(sameFootprint=False).reduceRegion(ee.Reducer.count(), exportregion)
                print(f"{str(type(self).__name__)}.exportpointtofile (earliest image band {exportband} in stack):")
                print(f"- actual region: {geeutils.szprojectioninfo(eeregion)}")
                print(f"- area: {eeregion.area(maxError=0.001).getInfo()}")
                print(f"- covering {eeregionpixelcount.getInfo()} pixels in src image")
                print(f"- export region: {geeutils.szprojectioninfo(exportregion)}")
                print(f"- area: {exportregion.area(maxError=0.001).getInfo()}")
                print(f"- covering {exportregionpixelcount.getInfo()} pixels in src image")
            #
            #    exportpointtofile is mainly for debug; works only for few bands ( < 100 ), small files, fast processes 
            #
            szfilename = szbasefilename + "_" + exportband + ".tif"
            geemap.ee_export_image(
                exportimage,
                filename=szfilename, 
                scale=exportimage.projection().nominalScale(),   # this scale only will determine the pixel size of the ***exported*** image
                region=exportregion, file_per_band=False)        # the ***exported*** region which is just a teeny-tiny bit smaller than it should be.
            #
            #    some nursing due to quirks in ee.Image.getDownloadURL (current versions: ee 0.1.248, gee 0.8.12) 
            #    
            try:
                import osgeo.gdal
                src_ds = osgeo.gdal.Open(szfilename)
                dst_ds = src_ds.GetDriver().CreateCopy(szfilename + ".tmp.tif", src_ds)
                #
                #    restore band descriptions which are mysteriously lost in the ee.Image.getDownloadURL (current versions: ee 0.1.248, gee 0.8.12)
                #
                lstbandnames = exportimage.bandNames().getInfo()
                for iband in range(src_ds.RasterCount):
                    dst_ds.GetRasterBand(iband+1).SetDescription(lstbandnames[iband])
                #
                #    qgis chokes on '-inf' which is default for masked values in Float32 and Float64 images (current versions: ee 0.1.248, gee 0.8.12)
                #
                datatype = dst_ds.GetRasterBand(1).DataType
                if (datatype == osgeo.gdalconst.GDT_Float32) or (datatype == osgeo.gdalconst.GDT_Float64):
                    rasterArray = dst_ds.GetRasterBand(iband+1).ReadAsArray()
                    rasterArray[rasterArray == -math.inf] = math.nan
                    dst_ds.GetRasterBand(iband+1).WriteArray(rasterArray)
                    dst_ds.GetRasterBand(iband+1).SetNoDataValue(math.nan)
                    
                dst_ds = None
                src_ds = None
                os.remove(szfilename)
                os.rename(szfilename + ".tmp.tif", szfilename)
    
            except Exception as e:
                #
                #    happens all the time e.g. some file is open in qgis
                #
                print(f"{str(type(self).__name__)}.exportpointtofile: updating band names FAILED with exception: {str(e)}")
                pass
    
            #
            #    debug. export the shape file of the eeregion (and exportregion) too.
            #
            if verbose:                                          # yes. verbose. yes. if I verbose, I am debugging, ain't I?
                geemap.ee_to_shp(
                    ee.FeatureCollection([ee.Feature(eeregion), ee.Feature(exportregion)]),
                    szfilename[0:-4] + ".shp")
        #
        #
        #
        return eeimagecollectionofstacks
        

    def exportpointtodrive_1(self, szid, eepoint, szdstfolder, verbose=False):
        """
        """
        eeimagecollectionofstacks  = self._getexportimage(eepoint, verbose=verbose)
        imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
        for iIdx in range(eeimagecollectionofstacks.size().getInfo()):
            exportimage = ee.Image(imageslist.get(iIdx))
            #
            #    real world batch task
            #
            szbasefilename = str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill)
            szfilename = szbasefilename + "_" + exportimage.get('band').getInfo()
            if verbose : print(f"{str(type(self).__name__)}.exportpointtodrive: exporting {szfilename}")
            
            eetask = ee.batch.Export.image.toDrive(
                image          = exportimage,
                region         = ee.Geometry(exportimage.get('region')),
                description    = szfilename,
                folder         = szdstfolder, #f"geeyatt_2020_{str(type(self._geeproduct).__name__)}",
                scale          = exportimage.projection().nominalScale().getInfo(),
                skipEmptyTiles = False,
                fileNamePrefix = szfilename,
                fileFormat     = 'GeoTIFF')
            self._starttask(eetask)

        return eeimagecollectionofstacks

    def exportpointtodrive(self, szid, eepoint, szdstfolder, verbose=False):
        """
        """
        verbose = True
        eeimagecollectionofstacks  = self._getexportimage(eepoint, verbose=False)
        imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
        iIdx = 0
        while True:
            try:
                exportimage = ee.Image(imageslist.get(iIdx))
                szbandname  = exportimage.get('band').getInfo() # this will trigger the "ee.ee_exception.EEException: List.get" exception
                #
                #    real world batch task
                #
            except Exception as e:
                if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: exported {iIdx} bands")
                return True

            try:
                szbasefilename = str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill)
                szfilename = szbasefilename + "_" + szbandname
                if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: exporting band {szbandname} to {szfilename}")
                
                eetask = ee.batch.Export.image.toDrive(
                    image          = exportimage,
                    region         = ee.Geometry(exportimage.get('region')),
                    description    = szfilename,
                    folder         = szdstfolder, #f"geeyatt_2020_{str(type(self._geeproduct).__name__)}",
                    scale          = exportimage.projection().nominalScale(), #.getInfo(),
                    skipEmptyTiles = False,
                    fileNamePrefix = szfilename,
                    fileFormat     = 'GeoTIFF')
                
                if not self._starttask(eetask):
                    if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: abandoned. {iIdx} bands were already exported")
                    return False
            except Exception as e:
                if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: exception. {iIdx} bands were already exported")
                return False

            iIdx += 1
            pass # continue while

