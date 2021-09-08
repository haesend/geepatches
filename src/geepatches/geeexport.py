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
with ee.__version__(0.1.248):

GEEExp.exportimages uses getDownloadURL.
- the maximum number of bands in a file is 100 (otherwise we get: "Number of bands (xxx) must be less than or equal to 100.")
- the maximum file size is 32MB. currently we do not check this: considering the 100 band limit, 
  and assumption we're working on small patches this should be no problem.

GEEExp.exportimagestodrive uses Export.image.toDrive, to export a multiband image, with bandnames YYYY-MM-dd
- it is hard to find documentation about limitations; there are some questions in discussion groups, but no decent answers
- there seems to be a 'space' problem with bandnames:
    - from a certain number of bands in a file, the bandnames are lost
    - this number seems to depend on the size (number of characters) in the bandnames
    - example: using YYYY-MM-dd we find we can export files with 416 bands correct. files with more bands loose their bandnames
- for the time being we'll try using a 366 limit - so it should be possible to have one file per year
"""
MAXBANDS_PERDOWNLOAD = 100
MAXBANDS_PERTODRIVE  = 366


"""
"""
class GEEExp(object):
    """
    The 'GEEExp' class hosts methods to export the image collections obtained from the GEECol.getcollection method.
    - exportimages:            exports the separate images to a local directory
    - exportimagestack:        exports the images stacked as bands in a multiband image to a local directory
    - exportimagestodrive:     exports the separate images to the google drive
    - exportimagestacktodrive: exports the images stacked as bands in a multiband image to the google drive

    exportimagestodrive - should only be used for very 'short' timeseries, otherwise the ee.batch.Task.start() overhead is far too large.
    """

    """
    """
    def _getgeecolproperties(self, eeimagecollection, verbose=False):
        """
        helper method to retrieve parameters needed for export, from the GEECol imagecollection properties:
        
        """
        #
        # retrieve properties from GEECol eeimagecollection
        #    GEECol imagecollections are supposed to have these properties available
        #    - 'gee_refroi'      : ee.Geometry - used as region parameter for exports
        #    - 'gee_centerpoint' : ee.Geometry.Point - debug
        #    - 'gee_projection'  : ee.Projection - used to shrink the exported region a little, and to find the scale parameter for exports
        #    - 'gee_description' : string - used to brew filenames for exports
        #
        eeregion     = ee.Geometry(eeimagecollection.get('gee_refroi'))
        eeprojection = ee.Projection(eeimagecollection.get('gee_projection'))
        #
        # everlasting war between pixel_as_surface vs pixel_as_point: 
        #    - export seems to use 'pixel_as_point'
        #    - our roi represents the pixel_as_surface bounding box
        #    - rounding errors can introduce an extra row/column in our exported image
        #    => shrinking the original roi with 10% of its own pixel size and prayer might take care of this
        #
        exportregion = eeregion.buffer(-0.1, proj=eeprojection)
        exportscale  = eeprojection.nominalScale()
        #
        # description will be used in filenames
        #
        szcollectiondescription = eeimagecollection.get('gee_description').getInfo()
        #
        # list of band names 
        #    normal GEECol collections are expected to be single-band
        #    in case there are more, each band is exported separately
        #
        szbandnames = eeimagecollection.aggregate_array('system:band_names').flatten().distinct().getInfo()    
        #
        #
        #
        return exportregion, exportscale, szcollectiondescription, szbandnames


    #####################################################################################
    #
    #    export the GEECol imagecollection to local drive
    #
    #####################################################################################

    """
    """
    def _geemap_ee_export_image(self, ee_object, filename, scale=None, crs=None, region=None, file_per_band=False, verbose=False):
        """
        local copy from the geemap.common.ee_export_image method (https://geemap.org/)
        modified slightly to avoid unconditional 'print' statements, replace error returns with exceptions and have a simple retry for the download
        """
        import zipfile
        import requests
        if not isinstance(ee_object, ee.Image):
            raise ValueError("ee_object must be an ee.Image")
    
        filename = os.path.abspath(filename)
        basename = os.path.basename(filename)
        name = os.path.splitext(basename)[0]
        filetype = os.path.splitext(basename)[1][1:].lower()
        filename_zip = filename.replace(".tif", ".zip")
    
        if filetype != "tif":
            raise ValueError("filename must end with .tif")
    
        try:
            if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - Generating URL ...")
            params = {"name": name, "filePerBand": file_per_band}
            if scale is None:
                scale = ee_object.projection().nominalScale().multiply(10)
            params["scale"] = scale
            if region is None:
                region = ee_object.geometry()
            params["region"] = region
            if crs is not None:
                params["crs"] = crs
    
            #
            #    retries might solve sporadic download failures ?
            #
            MAXATTEMPTS = 3
            DELAY       = 10
            for attempt in range(1, MAXATTEMPTS+1):
                try:
                    url = ee_object.getDownloadURL(params)
                    if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - Downloading data from {url}\nPlease wait ...")
                    r = requests.get(url, stream=True)
            
                    if r.status_code != 200:
                        raise Exception(f"error occurred while downloading - status code({r.status_code})")
            
                    with open(filename_zip, "wb") as fd:
                        for chunk in r.iter_content(chunk_size=1024):
                            fd.write(chunk)

                    if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - Downloading data attempt {attempt} of {MAXATTEMPTS} success")
                    break

                except Exception as e:
                    if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - Downloading data attempt {attempt} of {MAXATTEMPTS} failed")
                    last_exception = e
                    time.sleep(DELAY)   

            else: # for - else (for loop did not 'break')
                if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image {attempt} of {MAXATTEMPTS} failed - re-raising last Exception({str(last_exception)})")
                raise last_exception

        except Exception as e:
            if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - An error occurred while downloading: Exception({str(e)})")
            raise

        try:
            z = zipfile.ZipFile(filename_zip)
            z.extractall(os.path.dirname(filename))
            z.close()
            os.remove(filename_zip)
    
            if file_per_band:
                if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - Data downloaded to {os.path.dirname(filename)}")
            else:
                if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - Data downloaded to {filename}")
        except Exception as e:
            if verbose: print(f"{str(type(self).__name__)}._geemap_ee_export_image - An error occurred while unzipping: Exception({str(e)})")
            raise

    """
    """
    def exportimages(self, eeimagecollection, szoutputdir, szfilenameprefix="", verbose=False):
        """
        """
        try:
            #
            # check szoutputdir
            #    normalize the path (remove redundant separators, collapse up-level references, handle everlasting '/' '\', ...)
            #    verify the path is an existing directory
            #
            szoutputdir = os.path.normpath(szoutputdir)
            if not os.path.isdir(szoutputdir) :
                raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
            #
            # retrieve properties from GEECol eeimagecollection
            #
            exportregion, exportscale, szcollectiondescription, szbandnames = self._getgeecolproperties(eeimagecollection, verbose=verbose)
            #
            # actual export - per band
            #    normal GEECol collections are expected to be single-banded
            #    in case there are more, each band is exported separately
            #
            for szbandname in szbandnames:
                collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
                collectionsize = collection.size().getInfo()
            
                if verbose: print(f"{str(type(self).__name__)}.exportimages - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
        
                #
                # download 
                #    getDownloadURL downloads a zipped GeoTIFF
                #    max file size for getDownloadURL is 32MB
                #    loop per 100 - "Number of bands (xxx) must be less than or equal to 100."
                #    remark: since 2014 Earth Engine has been nagging getDownloadURL should be deprecated 
                #
                offset  = 0
                while offset < collectionsize:
                    eelist  = collection.toList(MAXBANDS_PERDOWNLOAD, offset)
                    offset += MAXBANDS_PERDOWNLOAD
                    #
                    # stack multiple single-band images into single multi-band image 
                    #    - exports faster than separate images
                    #    - remark:
                    #        Noel Gorelick doen't approve of iteration over bands; one should use ee.ImageCollection.toBands
                    #        ee.ImageCollection.toBands uses its own band naming convention
                    #        so we'd need yet another step to rename our bands
                    #        besides that, worldcereal/worldcover uses similar iterations, and it works. ha!
                    #
                    def addimagebandstostack(nextimage, previousstack):
                        nextimage = ee.Image(nextimage)
                        return ee.Image(previousstack).addBands(nextimage.rename(nextimage.date().format('YYYY-MM-dd')))
                    stackedimage = ee.Image(eelist.iterate(addimagebandstostack, ee.Image().select()))
                    #
                    # filenames - again
                    #    file_per_band = True will create separate images per band, thereby appending .bandname to the filename parameter
                    #    => files will be: szfilename.bandname.tif - bandname being 'YYYY-MM-dd'
                    #
                    if 1 < len(szbandnames):
                        # multi band images collection (exceptional)
                        szfilename  = os.path.join(szoutputdir, f"{szfilenameprefix}{szcollectiondescription}_{szbandname}.tif")
                    else:
                        # single band images collection (expected)
                        szfilename  = os.path.join(szoutputdir, f"{szfilenameprefix}{szcollectiondescription}.tif")
                    #
                    # export it (using (local) geemap.ee_export_image (clone), which uses ee.Image.getDownloadURL
                    # remark: file_per_band (or filePerBand in getDownloadURL) must be True, because the band names get lost
                    #    they could be restored afterwards via gdal, but where would it all end...
                    #
                    #        import osgeo.gdal
                    #        src_ds = osgeo.gdal.Open(szfilename)
                    #        dst_ds = src_ds.GetDriver().CreateCopy(szfilename + ".tmp.tif", src_ds)
                    #        #
                    #        #    restore band descriptions which are mysteriously lost in the ee.Image.getDownloadURL (current versions: ee 0.1.248, gee 0.8.12)
                    #        #
                    #        lstbandnames = exportimage.bandNames().getInfo()
                    #        for iband in range(src_ds.RasterCount):
                    #            dst_ds.GetRasterBand(iband+1).SetDescription(lstbandnames[iband])
                    #        ...
                    #
                    self._geemap_ee_export_image(
                        stackedimage,
                        filename      = szfilename,
                        scale         = exportscale,
                        region        = exportregion,
                        file_per_band = True,
                        verbose       = verbose)

                if verbose: print(f"{str(type(self).__name__)}.exportimages - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize} success")
    
        except Exception as e:
            print(f"{str(type(self).__name__)}.exportimagestacks - unhandled exception: {str(e)}")
            raise
    
        return True

    """
    """
    def exportimagestack(self, eeimagecollection, szoutputdir, szfilenameprefix="", verbose=False):
        """
        """
        import osgeo.gdal
        #
        # trying to avoid irrelevant gdal warnings
        #    opening multiband exported file complains:  "Warning 1: TIFFReadDirectory:Sum of Photometric type-related color channels and ExtraSamples doesn't match SamplesPerPixel..."
        #    SetNoDataValue on multiband copy complains: "Warning 1: Setting nodata to nan on band 1, but band 2 has nodata at -inf.
        #
        osgeo.gdal.UseExceptions()                           # considering all this nonsense
        osgeo.gdal.PushErrorHandler('CPLQuietErrorHandler')  # one might be tempted to use rasterio

        try:
            #
            # check szoutputdir
            #
            szoutputdir = os.path.normpath(szoutputdir)
            if not os.path.isdir(szoutputdir) :
                raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
            #
            # retrieve properties from GEECol eeimagecollection
            #
            exportregion, exportscale, szcollectiondescription, szbandnames = self._getgeecolproperties(eeimagecollection, verbose=verbose)
            #
            # actual export - per band
            #
            for szbandname in szbandnames:
                collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
                collectionsize = collection.size().getInfo()
            
                if verbose: print(f"{str(type(self).__name__)}.exportimagestack - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
        
                #
                # download 
                #
                offset  = 0
                while offset < collectionsize:
                    subcol = ee.ImageCollection(collection.toList(MAXBANDS_PERDOWNLOAD, offset))
                    offset += MAXBANDS_PERDOWNLOAD
                    #
                    # stack multiple single-band images into single multi-band image 
                    #
                    def addimagebandstostack(nextimage, previousstack):
                        nextimage = ee.Image(nextimage)
                        return ee.Image(previousstack).addBands(nextimage.rename(nextimage.date().format('YYYY-MM-dd')))
                    stackedimage = ee.Image(subcol.iterate(addimagebandstostack, ee.Image().select()))
                    #
                    # filenames
                    #
                    szfirstdate = subcol.limit(1, 'system:time_start', True).first().date().format('YYYY-MM-dd').getInfo()
                    szlastdate  = subcol.limit(1, 'system:time_start', False).first().date().format('YYYY-MM-dd').getInfo()
                     
                    if 1 < len(szbandnames):
                        # multi band images collection (exceptional)
                        szfilename  = os.path.join(szoutputdir, f"{szfilenameprefix}{szcollectiondescription}_{szbandname}_{szfirstdate}_{szlastdate}.tif")
                    else:
                        # single band images collection (expected)
                        szfilename  = os.path.join(szoutputdir, f"{szfilenameprefix}{szcollectiondescription}_{szfirstdate}_{szlastdate}.tif")
                    #
                    # export it (using (local) geemap.ee_export_image (clone), which uses ee.Image.getDownloadURL
                    #
                    self._geemap_ee_export_image(
                        stackedimage,
                        filename      = szfilename,
                        scale         = exportscale,
                        region        = exportregion,
                        file_per_band = False,
                        verbose       = verbose)
                    #
                    # downloading a multiband image via ee.Image.getDownloadURL, loses its bandnames,
                    # we'll try to restore them via gdal ... nice.
                    #
                    src_ds = osgeo.gdal.Open(szfilename)
                    dst_ds = src_ds.GetDriver().CreateCopy(szfilename + ".tmp.tif", src_ds, options = ['COMPRESS=DEFLATE', 'PHOTOMETRIC=MINISBLACK'])
                    #
                    #    restore band descriptions which are mysteriously lost in the ee.Image.getDownloadURL (current versions: ee 0.1.248, gee 0.8.12)
                    #
                    lstbandnames = stackedimage.bandNames().getInfo()
                    for iband in range(src_ds.RasterCount):
                        dst_ds.GetRasterBand(iband+1).SetDescription(lstbandnames[iband])
                        #
                        #    qgis chokes on '-inf' which is default for masked values in Float32 and Float64 images (current versions: ee 0.1.248, gee 0.8.12)
                        #    while we're at it, we'll try to patch this too. that way the files should be compatible with exportimagestacktodrive results. 
                        #
                        datatype = dst_ds.GetRasterBand(1).DataType
                        if (datatype == osgeo.gdalconst.GDT_Float32) or (datatype == osgeo.gdalconst.GDT_Float64):
                            rasterArray = dst_ds.GetRasterBand(iband+1).ReadAsArray()
                            rasterArray[rasterArray == -math.inf] = math.nan
                            dst_ds.GetRasterBand(iband+1).WriteArray(rasterArray)
                            if (iband == 0) : dst_ds.GetRasterBand(iband+1).SetNoDataValue(math.nan)
                    #
                    #    cleanup - beware: this is bound to crash when you're viewing "previous" files e.g. in qgis.
                    #
                    dst_ds = None
                    src_ds = None
                    os.remove(szfilename)
                    os.rename(szfilename + ".tmp.tif", szfilename)                    

                    if verbose: print(f"{str(type(self).__name__)}.exportimagestack - collection: {szcollectiondescription} band: {szbandname} stack first: {szfirstdate} last: {szlastdate} success")

                if verbose: print(f"{str(type(self).__name__)}.exportimagestack - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize} success")
    
        except Exception as e:
            print(f"{str(type(self).__name__)}.exportimagestack - unhandled exception: {str(e)}")
            raise
    
        return True        


    #####################################################################################
    #
    #    export the GEECol imagecollection to google drive
    #
    #####################################################################################

    """
    """
    def _starteetask(self, task, iattempt=0, verbose=False):
        """
        helper: wrapper around ee.batch.Task.start()
        - waits SLEEPTOOMUCHTASKS in case more tasks then MAXACTIVETASKS already in queue
        - waits SLEEPAFTEREXCEPTION and retries maximum MAXATTEMPTS in case an exception occured
        remark: in case of less considerate colleague processes stuffing the queue, this might not work
        """

        SLEEPTOOMUCHTASKS        = 120
        SLEEPAFTEREXCEPTION      = 60
        MAXACTIVETASKS           = 100
        MAXATTEMPTS              = 3

        def _activertaskscount():
            taskslist       = ee.batch.Task.list()
            activetaskslist = [task for task in taskslist if task.state in (
                ee.batch.Task.State.READY,
                ee.batch.Task.State.RUNNING,
                ee.batch.Task.State.CANCEL_REQUESTED)]
            activertaskscount = len(activetaskslist)
            if verbose: print(f"{str(type(self).__name__)}._starteetask._activertaskscount: {activertaskscount} tasks active")
            return activertaskscount

        try:
            while _activertaskscount() >= MAXACTIVETASKS:
                if verbose: print(f"{str(type(self).__name__)}._starteetask: sleep a while for gee")
                time.sleep(SLEEPTOOMUCHTASKS)
            if verbose: print(f"{str(type(self).__name__)}._starteetask(attempt:{iattempt}): starting task")
            task.start()
            if verbose: print(f"{str(type(self).__name__)}._starteetask(attempt:{iattempt}): task started")
            return True

        except Exception as e:
            if verbose: print(f"{str(type(self).__name__)}._starteetask(attempt:{iattempt}): exception: {str(e)}")
            iattempt += 1
            if iattempt < MAXATTEMPTS:
                #
                #    sleep a while, and try again.
                #
                time.sleep(SLEEPAFTEREXCEPTION)
                if verbose: print(f"{str(type(self).__name__)}._starteetask(attempt:{iattempt-1}): exception - retry")
                self._starteetask(task, iattempt, verbose=verbose)
            #
            #    give it up.
            #
            if verbose: print(f"{str(type(self).__name__)}._starteetask(attempt:{iattempt}): exception - exits")
            return False      

    """
    """
    def exportimagestodrive(self, eeimagecollection, szgdrivefolder, szfilenameprefix="", verbose=False):
        """
        """
        try:
            #
            # retrieve properties from GEECol eeimagecollection
            #
            exportregion, exportscale, szcollectiondescription, szbandnames = self._getgeecolproperties(eeimagecollection, verbose=verbose)
            #
            # actual export - per band
            #    normal GEECol collections are expected to be single-banded
            #    in case there are more, each band is exported separately
            #
            for szbandname in szbandnames:
                collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
                collectionsize = collection.size().getInfo()
            
                if verbose: print(f"{str(type(self).__name__)}.exportimagestodrive - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
    
                #
                # export each image in the collection separately - seems to take a lot of time. 
                # for small files even exportseparateimages is faster
                # apparently ee.batch.Export.image.toDrive creates a lot of overhead
                #
                eelist = collection.toList(collection.size())
                for iIdx in range(collection.size().getInfo()):
                    eeimage     = ee.Image(eelist.get(iIdx))
        
                    szyyyymmdd  = geeutils.szISO8601Date(eeimage.get('gee_date'))
                    if 1 < len(szbandnames):
                        # multi band images collection (exceptional)
                        szfilename  = f"{szfilenameprefix}{szcollectiondescription}_{szbandname}.{szyyyymmdd}"
                    else:
                        # single band images collection (expected)
                        szfilename  = f"{szfilenameprefix}{szcollectiondescription}.{szyyyymmdd}"
        
                    eetask = ee.batch.Export.image.toDrive(
                        image          = eeimage,
                        region         = exportregion,
                        description    = szfilename,
                        folder         = szgdrivefolder,
                        scale          = exportscale,
                        skipEmptyTiles = False,
                        fileNamePrefix = szfilename,
                        fileFormat     = 'GeoTIFF')
        
                    if not self._starteetask(eetask, verbose=verbose):
                        if verbose: print(f"{str(type(self).__name__)}.exportimagestodrive: abandoned.")
                        raise Exception("starting ee.batch.Export.image.toDrive task failed")
                   
                    if verbose: print(f"{str(type(self).__name__)}.exportimagestodrive - collection: {szcollectiondescription} band: {szbandname} date: {szyyyymmdd} success")

                if verbose: print(f"{str(type(self).__name__)}.exportimagestodrive - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize} success")

        except Exception as e:
            print(f"{str(type(self).__name__)}.exportimagestodrive - unhandled exception: {str(e)}")
            raise
    
        return True

    """
    """
    def exportimagestacktodrive(self, eeimagecollection, szgdrivefolder, szfilenameprefix="", verbose=False):
        """
        """
        try:
            #
            # retrieve properties from GEECol eeimagecollection
            #
            exportregion, exportscale, szcollectiondescription, szbandnames = self._getgeecolproperties(eeimagecollection, verbose=verbose)
            #
            # actual export - per band
            #    normal GEECol collections are expected to be single-banded
            #    in case there are more, each band is exported separately
            #
            for szbandname in szbandnames:
                #
                #    yes, mosaic should have sorted them already, but better safe then sorry.
                #
                collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname]).sort('system:time_start')
                collectionsize = collection.size().getInfo()
            
                if verbose: print(f"{str(type(self).__name__)}.exportimagestacktodrive - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
    
                #
                # Export.image.toDrive
                #    TODO: 'real' limitations for export to drive?
                #
                offset  = 0
                while offset < collectionsize:
                    subcol = ee.ImageCollection(collection.toList(MAXBANDS_PERTODRIVE, offset))
                    offset += MAXBANDS_PERTODRIVE
                    #
                    # stack multiple single-band images into single multi-band image 
                    #
                    def addimagebandstostack(nextimage, previousstack):
                        nextimage = ee.Image(nextimage)
                        return ee.Image(previousstack).addBands(nextimage.rename(nextimage.date().format('YYYY-MM-dd')))
                    stackedimage = ee.Image(subcol.iterate(addimagebandstostack, ee.Image().select()))
                    #
                    #    need these for some distinct filename.
                    #
                    szfirstdate = subcol.limit(1, 'system:time_start', True).first().date().format('YYYY-MM-dd').getInfo()
                    szlastdate  = subcol.limit(1, 'system:time_start', False).first().date().format('YYYY-MM-dd').getInfo()
        
                    if 1 < len(szbandnames):
                        # multi band images collection (exceptional)
                        szfilename  = f"{szfilenameprefix}{szcollectiondescription}_{szbandname}_{szfirstdate}_{szlastdate}"
                    else:
                        # single band images collection (expected)
                        szfilename  = f"{szfilenameprefix}{szcollectiondescription}_{szfirstdate}_{szlastdate}"
        
                    eetask = ee.batch.Export.image.toDrive(
                        image          = stackedimage,
                        region         = exportregion,
                        description    = szfilename[0:50],
                        folder         = szgdrivefolder,
                        scale          = exportscale,
                        skipEmptyTiles = False,
                        fileNamePrefix = szfilename,
                        fileFormat     = 'GeoTIFF')
        
                    if not self._starteetask(eetask, verbose=verbose):
                        if verbose: print(f"{str(type(self).__name__)}.exportimagestacktodrive: abandoned.")
                        raise Exception("starting ee.batch.Export.image.toDrive task failed")

                    if verbose: print(f"{str(type(self).__name__)}.exportimagestacktodrive - collection: {szcollectiondescription} band: {szbandname} stack first: {szfirstdate} last: {szlastdate} success")

                if verbose: print(f"{str(type(self).__name__)}.exportimagestacktodrive - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")

        except Exception as e:
            if verbose: print(f"{str(type(self).__name__)}.exportimagestacktodrive - unhandled exception: {str(e)}")
            raise

        return True

