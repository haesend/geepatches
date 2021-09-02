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
def exportimages(eeimagecollection, szoutputdir, szfilenameprefix="", verbose=False):
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
        # actual export - per band
        #
        for szbandname in szbandnames:
            collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
            collectionsize = collection.size().getInfo()
        
            if verbose: print(f"exportimages.exportimagestacks - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
    
            #
            # download 
            #    getDownloadURL downloads a zipped GeoTIFF
            #    max file size for getDownloadURL is 32MB
            #    loop per 100 - "Number of bands (xxx) must be less than or equal to 100."
            #    remark: since 2014 Earth Engine has been nagging getDownloadURL should be deprecated 
            #
            nrbands = 100
            offset  = 0
            while offset < collectionsize:
                eelist  = collection.toList(nrbands, offset)
                offset += nrbands
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
                # export it (using geemap.ee_export_image, which uses ee.Image.getDownloadURL
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
                # TODO: we could just copy the geemap.ee_export_image code here
                #    this would not only remove a dependency
                #    but could also include some error checking/retry/message/... iso the geemap.ee_export_image 'print' output
                #
                geemap.ee_export_image(
                    stackedimage,
                    filename      = szfilename,
                    scale         = exportscale,
                    region        = exportregion,
                    file_per_band = True)

    except Exception as e:
        print(f"exportimages.exportimagestacks - unhandled exception: {str(e)}")
        return False

    return True


"""
"""
class GEEExp(object):
    """
    """

    def _getcommonexportparams(self, eeimagecollection, verbose=False):
        """
        """
        #
        # GEECol imagecollections are supposed to have these properties available
        #
        eeregion     = ee.Geometry(eeimagecollection.get('gee_refroi'))
        eeprojection = ee.Projection(eeimagecollection.get('gee_projection'))
        #
        # everlasting war between pixel_as_surface vs pixel_as_point: 
        #    - export seems to use 'pixel_as_point'
        #    - our roi represents the pixel_as_surface bounding box
        #    - rounding errors can introduce an extra row/column in our exported image
        #    => shinking the original roi with 10% of its own pixel size and prayer might take care of this
        #
        exportregion = eeregion.buffer(-0.1, proj=eeprojection)
        exportscale  = eeprojection.nominalScale()
        #
        # description used in filenames
        #
        szcollectiondescription = eeimagecollection.get('gee_description').getInfo()
        #
        # enable loop over bandnames - normal GEECol collections are expected to be single-band - but just in case
        #
        szbandnames = eeimagecollection.aggregate_array('system:band_names').flatten().distinct().getInfo()
        #
        #
        #
        return exportregion, exportscale, szcollectiondescription, szbandnames


    def _starteetask(self, task, iattempt=0):
        """
        """

        SLEEPTOOMUCHTASKSSECONDS = 120
        SLEEPAFTEREXCEPTION      = 120
        MAXACTIVETASKS           = 250
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

    
    def exportseparateimages(self, eeimagecollection, szoutputdir, szfilenameprefix="", verbose=False):
        """
        """
        #
        # filenames filenames... I hate filenames...
        # - normalize the path (remove redundant separators, collapse up-level references, handle everlasting '/' '\', ...)
        # - verfify the path is an existing directory
        #
        szoutputdir = os.path.normpath(szoutputdir)
        if not os.path.isdir(szoutputdir) :
            raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
        #
        #
        #
        exportregion, exportscale, szcollectiondescription, szbandnames = self._getcommonexportparams(eeimagecollection, verbose=verbose)
        #
        #
        #
        for szbandname in szbandnames:
            collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
            collectionsize = collection.size().getInfo()
        
            if verbose: print(f"{str(type(self).__name__)}.exportseparateimages - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
    
            #
            # export each image in the collection separately - seems to take a lot of time.
            #
            eelist = collection.toList(collection.size())
            for iIdx in range(collection.size().getInfo()):
                eeimage     = ee.Image(eelist.get(iIdx))
                #
                # filenames again; 
                #    using weird ".yyyymmdd.tif" to get same filenames as exportimagestacks, where 'file_per_band' rules.
                #
                szyyyymmdd  = geeutils.szISO8601Date(eeimage.get('gee_date'))
                if 1 < len(szbandnames):
                    # multi band images (exceptional)
                    szfilename  = os.path.join(szoutputdir, f"exportseparateimages_{szfilenameprefix}_{szcollectiondescription}_{szbandname}.{szyyyymmdd}.tif")
                else:
                    # single band images (expected)
                    szfilename  = os.path.join(szoutputdir, f"exportseparateimages_{szfilenameprefix}_{szcollectiondescription}.{szyyyymmdd}.tif")
                geemap.ee_export_image(
                    eeimage,
                    filename = szfilename,
                    scale    = exportscale,
                    region   = exportregion,
                    file_per_band=False)
    
    
    def exportimagestacks(self, eeimagecollection, szoutputdir, szfilenameprefix="", verbose=False):
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
            # retrieve properties from GEECol imagecollection
            #
            exportregion, exportscale, szcollectiondescription, szbandnames = self._getcommonexportparams(eeimagecollection, verbose=verbose)
            #
            # loop over bands
            #    normally these collections contain but one band,  
            #    in case there are more, each band is exported separately
            #
            for szbandname in szbandnames:
                collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
                collectionsize = collection.size().getInfo()
            
                if verbose: print(f"{str(type(self).__name__)}.exportimagestacks - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
        
                #
                # download 
                #    getDownloadURL downloads a zipped GeoTIFF
                #    max filesize for getDownloadURL is 32MB
                #    loop per 100 - "Number of bands (xxx) must be less than or equal to 100."
                #    remark: since 2014 Earth Engine has been nagging getDownloadURL should be deprecated 
                #
                nrbands = 100
                offset  = 0
                while offset < collectionsize:
                    eelist  = collection.toList(nrbands, offset)
                    offset += nrbands
                    print(collectionsize, eelist.size().getInfo())
                    #
                    # stack multiple single-band images into single multi-band image - exports faster than separate images
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
                    geemap.ee_export_image(
                        stackedimage,
                        filename      = szfilename,
                        scale         = exportscale,
                        region        = exportregion,
                        file_per_band = True)

        except Exception as e:
            if verbose: print(f"{str(type(self).__name__)}.exportimagestacks - unhandled exception: {str(e)}")
            return False

        return True
    
#         
#         def ee_export_image(
#             ee_object, filename, scale=None, crs=None, region=None, file_per_band=False
#         ):
#             """Exports an ee.Image as a GeoTIFF.
#         
#             Args:
#                 ee_object (object): The ee.Image to download.
#                 filename (str): Output filename for the exported image.
#                 scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
#                 crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
#                 region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
#                 file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
#             """
#             import requests
#             import zipfile
#         
#             if not isinstance(ee_object, ee.Image):
#                 print("The ee_object must be an ee.Image.")
#                 return
#         
#             filename = os.path.abspath(filename)
#             basename = os.path.basename(filename)
#             name = os.path.splitext(basename)[0]
#             filetype = os.path.splitext(basename)[1][1:].lower()
#             filename_zip = filename.replace(".tif", ".zip")
#         
#             if filetype != "tif":
#                 print("The filename must end with .tif")
#                 return
#         
#             try:
#                 print("Generating URL ...")
#                 params = {"name": name, "filePerBand": file_per_band}
#                 if scale is None:
#                     scale = ee_object.projection().nominalScale().multiply(10)
#                 params["scale"] = scale
#                 if region is None:
#                     region = ee_object.geometry()
#                 params["region"] = region
#                 if crs is not None:
#                     params["crs"] = crs
#         
#                 url = ee_object.getDownloadURL(params)
#                 print("Downloading data from {}\nPlease wait ...".format(url))
#                 r = requests.get(url, stream=True)
#         
#                 if r.status_code != 200:
#                     print("An error occurred while downloading.")
#                     return
#         
#                 with open(filename_zip, "wb") as fd:
#                     for chunk in r.iter_content(chunk_size=1024):
#                         fd.write(chunk)
#         
#             except Exception as e:
#                 print("An error occurred while downloading.")
#                 print(e)
#                 return
#         
#             try:
#                 z = zipfile.ZipFile(filename_zip)
#                 z.extractall(os.path.dirname(filename))
#                 z.close()
#                 os.remove(filename_zip)
#         
#                 if file_per_band:
#                     print("Data downloaded to {}".format(os.path.dirname(filename)))
#                 else:
#                     print("Data downloaded to {}".format(filename))
#             except Exception as e:
#                 print(e)
    
    """
    """
    def exportseparateimagestodrive(self, eeimagecollection, szfilenameprefix="", verbose=False):
        #
        #    TODO - folder
        #
#         #
#         # - normalize the path (remove redundant separators, collapse up-level references, handle everlasting '/' '\', ...)
#         # - verfify the path is an existing directory
#         #
#         szoutputdir = os.path.normpath(szoutputdir)
#         if not os.path.isdir(szoutputdir) :
#             raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
        #
        #
        #
        exportregion, exportscale, szcollectiondescription, szbandnames = self._getcommonexportparams(eeimagecollection, verbose=verbose)
        #
        #
        #
        for szbandname in szbandnames:
            collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
            collectionsize = collection.size().getInfo()
        
            if verbose: print(f"{str(type(self).__name__)}.exportseparateimagestodrive - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")

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
                    folder         = f"geepatches",
                    scale          = exportscale,
                    skipEmptyTiles = False,
                    fileNamePrefix = szfilename,
                    fileFormat     = 'GeoTIFF')
    
                if not self._starteetask(eetask):
                    if verbose: print(f"{str(type(self).__name__)}.exportimagestackstodrive: abandoned.")
                    return False

    
    """
    """
    def exportimagestackstodrive(self, eeimagecollection, szgooglething, szfilenameprefix="", verbose=False):
        try:
    
            #
            #    TODO - folder
            #
    #         #
    #         # - normalize the path (remove redundant separators, collapse up-level references, handle everlasting '/' '\', ...)
    #         # - verfify the path is an existing directory
    #         #
    #         szoutputdir = os.path.normpath(szoutputdir)
    #         if not os.path.isdir(szoutputdir) :
    #             raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
            #
            #
            #
            exportregion, exportscale, szcollectiondescription, szbandnames = self._getcommonexportparams(eeimagecollection, verbose=verbose)
            #
            #
            #
            for szbandname in szbandnames:
                collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
                collectionsize = collection.size().getInfo()
            
                if verbose: print(f"{str(type(self).__name__)}.exportimagestackstodrive - collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
    
                #
                #    TODO: are there limits to number of bands in export to drive?
                #
                def addimagebandstostack(nextimage, previousstack):
                    nextimage = ee.Image(nextimage)
                    return ee.Image(previousstack).addBands(nextimage.rename(nextimage.date().format('YYYY-MM-dd')))
                stackedimage = ee.Image(collection.iterate(addimagebandstostack, ee.Image().select()))
    
                if 1 < len(szbandnames):
                    # multi band images collection (exceptional)
                    szfilename  = f"{szfilenameprefix}{szcollectiondescription}_{szbandname}_{szgooglething}"
                else:
                    # single band images collection (expected)
                    szfilename  = f"{szfilenameprefix}{szcollectiondescription}_{szgooglething}"
    
                eetask = ee.batch.Export.image.toDrive(
                    image          = stackedimage,
                    region         = exportregion,
                    description    = szfilename[0:50],
                    folder         = "geepatches",
                    scale          = exportscale,
                    skipEmptyTiles = False,
                    fileNamePrefix = szfilename,
                    fileFormat     = 'GeoTIFF')
    
                if not self._starteetask(eetask):
                    if verbose: print(f"{str(type(self).__name__)}.exportimagestackstodrive: abandoned.")
                    return False

        except Exception as e:
            if verbose: print(f"{str(type(self).__name__)}.exportimagestackstodrive - unhandled exception: {str(e)}")
            return False

        return True

# 
# 
# """
# """
# def _getexportparams(eeimagecollection, szoutputdir, verbose=False):
#     #
#     # filenames filenames... I hate filenames...
#     # - normalize the path (remove redundant separators, collapse up-level references, handle everlasting '/' '\', ...)
#     # - verfify the path is an existing directory
#     #
#     szoutputdir = os.path.normpath(szoutputdir)
#     if not os.path.isdir(szoutputdir) :
#         raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
#     
#     #
#     # GEECol imagecollections are supposed to have these properties available
#     #
#     eeregion     = ee.Geometry(eeimagecollection.get('gee_refroi'))
#     eeprojection = ee.Projection(eeimagecollection.get('gee_projection'))
#     #
#     # everlasting war between pixel_as_surface vs pixel_as_point: 
#     #    - export seems to use 'pixel_as_point'
#     #    - our roi represents the pixel_as_surface bounding box
#     #    - rounding errors can introduce an extra row/column in our exported image
#     #    => shinking the original roi with 10% of its own pixel size and prayer might take care of this
#     #
#     exportregion = eeregion.buffer(-0.1, proj=eeprojection)
#     exportscale  = eeprojection.nominalScale()
#     #
#     # description used in filenames
#     #
#     szcollectiondescription = eeimagecollection.get('gee_description').getInfo()
#     #
#     # enable loop over bandnames - normal GEECol collections are expected to be single-band - but just in case
#     #
#     szbandnames = eeimagecollection.aggregate_array('system:band_names').flatten().distinct().getInfo()
#     #
#     #
#     #
#     return szoutputdir, exportregion, exportscale, szcollectiondescription, szbandnames
#     
# """
# """
# def exportseparateimages(eeimagecollection, szoutputdir, szfilenameprefix="", verbose=False):
#     #
#     #
#     #
#     szoutputdir, exportregion, exportscale, szcollectiondescription, szbandnames = _getexportparams(eeimagecollection, szoutputdir, verbose=verbose)
# #     #
# #     # filenames filenames... I hate filenames...
# #     # - normalize the path (remove redundant separators, collapse up-level references, handle everlasting '/' '\', ...)
# #     # - verfify the path is an existing directory
# #     #
# #     szoutputdir = os.path.normpath(szoutputdir)
# #     if not os.path.isdir(szoutputdir) :
# #         raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
# #     
# #     #
# #     # GEECol imagecollections are supposed to have these properties available
# #     #
# #     eeregion     = ee.Geometry(eeimagecollection.get('gee_refroi'))
# #     eeprojection = ee.Projection(eeimagecollection.get('gee_projection'))
# #     #
# #     # everlasting war between pixel_as_surface vs pixel_as_point: 
# #     #    - export seems to use 'pixel_as_point'
# #     #    - our roi represents the pixel_as_surface bounding box
# #     #    - rounding errors can introduce an extra row/column in our exported image
# #     #    => shinking the original roi with 10% of its own pixel size and prayer might take care of this
# #     #
# #     exportregion = eeregion.buffer(-0.1, proj=eeprojection)
# #     exportscale  = eeprojection.nominalScale()
# #     #
# #     # loop over bandnames - normal GEECol collections are expected to be single-band - but just in case
# #     #
# #     szbandnames = eeimagecollection.aggregate_array('system:band_names').flatten().distinct().getInfo()
# 
#     for szbandname in szbandnames:
#         collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
#         collectionsize = collection.size().getInfo()
#     
#         print(f"collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
# 
#         #
#         # export each image in the collection separately - seems to take a lot of time.
#         #
#         eelist = eeimagecollection.toList(collection.size())
#         for iIdx in range(collection.size().getInfo()):
#             eeimage     = ee.Image(eelist.get(iIdx))
#             #
#             # filenames - again
#             #
#             szyyyymmdd  = geeutils.szISO8601Date(eeimage.get('gee_date'))
#             if 1 < len(szbandnames):
#                 # multi band images (exceptional)
#                 szfilename  = os.path.join(szoutputdir, f"exportseparateimages_{szfilenameprefix}_{szcollectiondescription}_{szbandname}.{szyyyymmdd}.tif")
#             else:
#                 # single band images (expected)
#                 szfilename  = os.path.join(szoutputdir, f"exportseparateimages_{szfilenameprefix}_{szcollectiondescription}.{szyyyymmdd}.tif")
#             geemap.ee_export_image(
#                 eeimage,
#                 filename = szfilename,
#                 scale    = exportscale,
#                 region   = exportregion,
#                 file_per_band=False)
# 
# 
# """
# """
# def exportimagestacks(eeimagecollection, szoutputdir, szfilenameprefix="", verbose=False):
#     #
#     #
#     #
#     szoutputdir, exportregion, exportscale, szcollectiondescription, szbandnames = _getexportparams(eeimagecollection, szoutputdir, verbose=verbose)
# #     #
# #     # filenames filenames... I hate filenames...
# #     # - normalize the path (remove redundant separators, collapse up-level references, handle everlasting '/' '\', ...)
# #     # - verfify the path is an existing directory
# #     #
# #     szoutputdir = os.path.normpath(szoutputdir)
# #     if not os.path.isdir(szoutputdir) :
# #         raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
# #     
# #     #
# #     # GEECol imagecollections are supposed to have these properties available
# #     #
# #     eeregion     = ee.Geometry(eeimagecollection.get('gee_refroi'))
# #     eeprojection = ee.Projection(eeimagecollection.get('gee_projection'))
# #     #
# #     # everlasting war between pixel_as_surface vs pixel_as_point: 
# #     #    - export seems to use 'pixel_as_point'
# #     #    - our roi represents the pixel_as_surface bounding box
# #     #    - rounding errors can introduce an extra row/column in our exported image
# #     #    => shinking the original roi with 10% of its own pixel size and prayer might take care of this
# #     #
# #     exportregion = eeregion.buffer(-0.1, proj=eeprojection)
# #     exportscale  = eeprojection.nominalScale()
# #     #
# #     # loop over bandnames - normal GEECol collections are expected to be single-band - but just in case
# #     #
# #     szbandnames = eeimagecollection.aggregate_array('system:band_names').flatten().distinct().getInfo()
# 
#     
#     for szbandname in szbandnames:
#         collection     = eeimagecollection.filter(ee.Filter.listContains('system:band_names', szbandname)).select([szbandname])
#         collectionsize = collection.size().getInfo()
#     
#         print(f"collection: {szcollectiondescription} band: {szbandname} images: {collectionsize}")
# 
#         offset = 0
#         while offset < collectionsize:
#             eelist  = collection.toList(100, offset)
#             offset += 100
#             print(eelist.size().getInfo())
#             #
#             # stack multiple single-band images into single multi-band image - exports faster than separate images
#             #
#             def addimagebandstostack(nextimage, previousstack):
#                 nextimage = ee.Image(nextimage)
#                 return ee.Image(previousstack).addBands(nextimage.rename(nextimage.date().format('YYYY-MM-dd')))
#             stackedimage = ee.Image(eelist.iterate(addimagebandstostack, ee.Image().select()))
#             print(stackedimage.bandNames().getInfo())
#     
#             #
#             # filenames - again
#             #
#             if 1 < len(szbandnames):
#                 # multi band images collection (exceptional)
#                 szfilename  = os.path.join(szoutputdir, f"exportimagestacks_{szfilenameprefix}_{szcollectiondescription}_{szbandname}.tif")
#             else:
#                 # single band images collection (expected)
#                 szfilename  = os.path.join(szoutputdir, f"exportimagestacks_{szfilenameprefix}_{szcollectiondescription}.tif")
#             geemap.ee_export_image(
#                 stackedimage,
#                 filename      = szfilename,
#                 scale         = exportscale,
#                 region        = exportregion,
#                 file_per_band = True)



"""
"""
def export(eeimagecollection):
    #
    #
    #
    eeregion = eeimagecollection.get('region')

    eelist = eeimagecollection.toList(eeimagecollection.size())
    for iIdx in range(eeimagecollection.size().getInfo()):
        eeimage  = ee.Image(eelist.get(iIdx))
        
        imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
        for iIdx in range(eeimagecollectionofstacks.size().getInfo()):
            exportimage = ee.Image(imageslist.get(iIdx))
            exportband  = exportimage.get('band').getInfo()
            eeregion    = ee.Geometry(exportimage.get('region'))
            geemap.ee_export_image(
                exportimage,
                filename=szfilename, 
                scale=exportimage.projection().nominalScale(),   # this scale only will determine the pixel size of the ***exported*** image
                region=exportregion, file_per_band=False)        # the ***exported*** region which is just a teeny-tiny bit smaller than it should be.

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


# """
# """
# class GEEExport(object):
#     def __init__(self, geeproduct, eedatefrom, eedatetill, refprodroiradius, refprodscale = 1, maxrefprodscale = 1, refproduct = None, refprodroiradunits = 'pixels'):
#         """
#         starts from the obscure assumption that there will be one 'more-important' GEEProduct to be exported, 
#         referred to as the "reference", typically with a high resolution,
#         and that there will be exports of "related" GEEProduct-s, which should align with the reference-ses roi as good as possible,
#         but with a resolution of their own original order of magnitude. e.g. self-PV333m (EPSG:4326) vs ref-S2 should become an UTM of approximately 300m.
#         which can align with the S2 10m without generating too much redundant pixel data.
#         :param geeproduct: instance of a GEEProduct to be exported
#         :param refprodroiradius: half-size of the more-ore-less square roi
#         :param refprodscale: self-projection will be the refproduct projection downscaled by this factor. e.g. self-PV333m vs ref-S2 could be 32 or 16
#         :param maxrefprodscale: maximum downscale factor that will be used in all related exports with same refproduct
#         :param refproduct: instance of reference GEEProduct. defaults to self. normally the one with the highest resolution. exports will (try to) mirror its projection and roi
#         :param refprodroiradunits: units of refprodroiradius. 'pixels' or 'meters'. defaults to 'pixels'. and whatever we do, off-by-ones will remain with us until the universe collapses.
#         """
#         self._geeproduct  = geeproduct
#         self._eedatefrom  = eedatefrom
#         self._eedatetill  = eedatetill
#         self._refroirad   = refprodroiradius
#         self._refroiunits = 'meters' if refprodroiradunits=='meters' else 'pixels'
#         self._actrefscale = 1 if refprodscale is None else refprodscale 
#         self._maxrefscale = 1 if maxrefprodscale is None else maxrefprodscale
#         self._refproduct  = geeproduct if refproduct is None else refproduct
# 
# 
#     def _starttask(self, task, iattempt=0):
#         """
#         """
#         SLEEPTOOMUCHTASKSSECONDS = 120
#         SLEEPAFTEREXCEPTION      = 120
#         MAXACTIVETASKS           = 15
#         MAXATTEMPTS              = 2
# 
#         def _activertaskscount():
#             taskslist       = ee.batch.Task.list()
#             activetaskslist = [task for task in taskslist if task.state in (
#                 ee.batch.Task.State.READY,
#                 ee.batch.Task.State.RUNNING,
#                 ee.batch.Task.State.CANCEL_REQUESTED)]
#             activertaskscount = len(activetaskslist)
#             print(f"{str(type(self).__name__)}._starttask._activertaskscount: {activertaskscount} tasks active")
#             return activertaskscount
# 
#         try:
#             while _activertaskscount() >= MAXACTIVETASKS:
#                 print(f"{str(type(self).__name__)}._starttask: sleep a while for gee")
#                 time.sleep(SLEEPTOOMUCHTASKSSECONDS)
#             print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): starting task")
#             task.start()
#             print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): task started")
#             return True
# 
#         except Exception as e:
#             print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): exception: {str(e)}")
#             iattempt += 1
#             if iattempt < MAXATTEMPTS:
#                 #
#                 #    sleep a while, and try again.
#                 #
#                 time.sleep(SLEEPAFTEREXCEPTION)
#                 print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt-1}): exception - retry")
#                 self._starttask(task, iattempt)
#             #
#             #    give it up.
#             #
#             print(f"{str(type(self).__name__)}._starttask(attempt:{iattempt}): exception - exits")
#             return False
# 
# 
#     def _getexportimage(self, eepoint, verbose=False):
#         """
#         """
#         #      
#         #    TODO: 
#         #    - clip _maxrefscale on 1?
#         #
# 
#         #
#         #    Yet Another aTTempt trying to solve the oldest problem in imagery: obtain a reproducable, reasonable, simple roi:
#         #
#         #    start by selecting a reference image: in the reference product we search for an image
#         #        temporal 'near' to the export start date, covering the eepoint to be exported for
#         #
#         #    BEWARE: 
#         #    - eerefimage is limited to the first band of the reference product base collection
#         #      this is *NOT* a clean solution. at the moment it is only needed for S1 where we need VV, VH + the 'angle'
#         #      but 'angle' has a different resolution. we might consider to rethink the 'base collection' concept,
#         #      remove it from the constructor, overload _export, ... if this problem persists.
#         #
#         #    - selecting a eerefimage works in most cases, but is not fail-safe. e.g. S1 can give 2 different images
#         #      in the same region around an eepoint, with minor difference in start-time, but having a different crs. 
#         #      e.g.
#         #        ee.Image("COPERNICUS/S1_GRD/S1B_IW_GRDH_1SDV_20180716T172348_20180716T172413_011839_015CA0_02B2"): EPSG:32632 2018-07-16
#         #        ee.Image("COPERNICUS/S1_GRD/S1B_IW_GRDH_1SDV_20180716T172413_20180716T172438_011839_015CA0_2CC9"): EPSG:32631 2018-07-16
#         #
#         #      this means that in case S1 or alikes, exporting different time series for the same point could cover 
#         #      a different roi. this can be avoided by selecting an appropriate reference product.
#         #      mind you: S2 is expected to have the same problem (at an UTM border with overlapping tiles) but far less often
#         #
#         #      if this turns out to be a showstopper, we can work around by implementing a simple "setrefimage(eeimage)" method
#         #      and a condition "if not eerefimage: eerefimage = ..." but then the user is left out in the cold.
#         #
#         eerefimage = geeutils.someImageNear(self._refproduct.basecollection(), self._eedatefrom, eepoint).select(0)
#         if verbose: print(f"{str(type(self).__name__)}._getexportimage: eerefimage\n {geeutils.szprojectioninfo(eerefimage)} id:{eerefimage.id().getInfo()}")
#         #
#         #    from this (single banded) eerefimage we obtain the projection to be used throughout the rest of the story
#         #
#         eerefproj  = eerefimage.projection()
#         if verbose: print(f"{str(type(self).__name__)}._getexportimage: eerefproj\n {geeutils.szprojectioninfo(eerefproj)}")
#         #
#         #    the center of the roi to be exported, will be the center of a (theoretical) pixel of the (theoretical)
#         #    reference image, reprojected to half its own resolution. this means that this eerefpoint is positioned exactly
#         #    at the pixel borders of the (actual) reference image, near to the eepoint for which the roi is to be exported.
#         #    in the eerefimage, in its own eerefproj, the roi will be symetrical around this eerefpoint.
#         #
#         eerefpoint = geeutils.pixelcenterpoint(eepoint, eerefimage.reproject(eerefproj.scale(2*self._maxrefscale, 2*self._maxrefscale)))
#         if verbose: print(f"{str(type(self).__name__)}._getexportimage: eerefpoint\n {geeutils.szprojectioninfo(eerefpoint)}")
# 
#         if (self._refroiunits == 'meters'):
#             #
#             #    ok, when starting to fiddle with "meters" iso pixels, 'symetrical' is relative, and off by one will not be solved in this lifetime.
#             #    for now, when looking at the resulting area(), squareareaboundsroi seems more accurate,
#             #    however, results from squarerasterboundsroi( meters/nominalScale) seem to match out intuition better
#             #    in terms of dimensions and pixel-count
#             #
#             eeregion = geeutils.squareareaboundsroi(eerefpoint, self._refroirad, eerefimage, verbose=verbose)
#             #eeregion = geeutils.squarerasterboundsroi(eerefpoint, self._refroirad/eerefproj.nominalScale().getInfo(), eerefimage)
#         else:
#             #
#             #    if all goes well, we'll have even square dimensions
#             #
#             eeregion = geeutils.squarerasterboundsroi(eerefpoint, self._refroirad, eerefimage, verbose=verbose)
#         if verbose: print(f"{str(type(self).__name__)}._getexportimage: eeregion\n {geeutils.szprojectioninfo(eeregion)}")
#         
#         eeimagecollection = self._geeproduct.getimagecollection(
#                             eeregion, 
#                             eerefproj.scale(self._actrefscale, self._actrefscale), # this scale (projection) will  will determine the pixel size of the ***internal*** image
#                             self._eedatefrom, self._eedatetill, 
#                             doscaleandflag=True, verbose=verbose)
# 
#         if eeimagecollection is None:
#             print(f"{str(type(self).__name__)}._getexportimage: nothing to export - bailing out")
#             return None
# 
#         #         #
#         #         #    stack collection into single multiband image
#         #         #
#         #         eeimage = geeutils.stackcollectiontoimage(eeimagecollection, verbose=verbose)
#         #         if verbose: print(f"{str(type(self).__name__)}._getexportimage: export image: {geeutils.szbandsinfo(eeimage)}")
# 
#         #
#         #    stack collection into collection of multiband (timeseries) images, one per band
#         #
#         def addimagebandstostack(nextimage, previousstack):
#             return ee.Image(previousstack).addBands(nextimage.rename(nextimage.date().format('YYYY-MM-dd')))
# 
#         eelistofallbandnames      = eeimagecollection.aggregate_array('system:band_names').flatten().distinct() # works (?) even if images have different band(name)s
#         eeimagecollectionofstacks = ee.ImageCollection(eelistofallbandnames.map(lambda bandname: 
#                                                                                 (ee.Image(eeimagecollection
#                                                                                           .filter(ee.Filter.listContains('system:band_names', bandname))
#                                                                                           .select([bandname])
#                                                                                           .sort('system:time_start')
#                                                                                           .iterate(addimagebandstostack, ee.Image().select()))
#                                                                                           .set('band', bandname))))
#         #
#         #    exporting requires the region; 
#         #        Export.image.toDrive default would be 'the region defaults to the viewport at the time of invocation.'
#         #        whatever that might be in python context.
#         #        ee.batch.Export.image.toDrive comments say: 'Defaults to the image's region.' Nice.
#         #
#         #    at this point, the image has no ".geometry()" - seems to be unbound
#         #    we could use .set('system:footprint', eeregion), then ".geometry()" is there
#         #
#         #         if False:
#         #             print ("initial")
#         #             print ("- stacked image - footprint", eeimage.get('system:footprint').getInfo())   # None
#         #             print ("- stacked image - geometry",  eeimage.geometry().getInfo())                # unbound ( [[[-180, -90], [180, -90]...)
#         #             print ("- stacked image - 'region'",  eeimage.get('region').getInfo())             # None
#         #             print ("setting 'region' property")
#         #             eeimage = eeimage.set('region', eeregion)
#         #             print ("- stacked image - footprint", eeimage.get('system:footprint').getInfo())   # None
#         #             print ("- stacked image - geometry",  eeimage.geometry().getInfo())                # unbound ( [[[-180, -90], [180, -90]...)
#         #             print ("- stacked image - 'region'",  eeimage.get('region').getInfo())             # our eeregion
#         #             print ("setting 'system:footprint' property")
#         #             eeimage = eeimage.set('system:footprint', eeregion)
#         #             print ("- stacked image - footprint", eeimage.get('system:footprint').getInfo())   # our eeregion
#         #             print ("- stacked image - geometry",  eeimage.geometry().getInfo())                # our eeregion
#         #             print ("- stacked image - 'region'",  eeimage.get('region').getInfo())             # our eeregion
#         #
#         #    but its not clear where and how gee internals use this 'system:footprint'; 
#         #        should the image be clipped to this footprint too to have a consistent entity? 
#         #        is 'system:footprint' just-another-property?
#         #        what if 'system:footprint' is inconsistent with the crs in the image bands?
#         #        ...
#         #
#         #    for the time being, we'll use an additional 'region' property
#         #    so we can pass the eeregion we calculated by putting it in this property,
#         #    without fearing a collapse of the known universe with the next gee update.
#         #
#         eeimagecollectionofstacks = eeimagecollectionofstacks.map(lambda eeimage: eeimage.set('region', eeregion))
#         
#         return eeimagecollectionofstacks
# 
#     
#     def exportpoint(self, szid, eepoint, verbose=False):
#         """
#         """
#         eeimagecollectionofstacks = self._getexportimage(eepoint, verbose=verbose)
# 
#         #
#         #    exportimage is unbounded. we'll clip it to the region specified when instantiating the GEEExport,
#         #    hoping this will give results consistent with the image tif obtained via exportpointtofile/exportpointtodrive
#         #    (by clipping, its footprint and geometry seem to be updated to our region)
#         #
#         #         print ("- exportpoint image - footprint", exportimage.get('system:footprint').getInfo())   # None
#         #         print ("- exportpoint image - geometry",  exportimage.geometry().getInfo())                # unbound ( [[[-180, -90], [180, -90]...)
#         #         print ("- exportpoint image - 'region'",  exportimage.get('region').getInfo())             # our eeregion
#         #         exportimage = exportimage.clip(exportimage.get('region'))
#         #         print ("- clipped image - footprint", exportimage.get('system:footprint').getInfo())       # our eeregion
#         #         print ("- clipped image - geometry",  exportimage.geometry().getInfo())                    # our eeregion
#         #         print ("- clipped image - 'region'",  exportimage.get('region').getInfo())                 # our eeregion
# 
#         eeimagecollectionofstacks = eeimagecollectionofstacks.map(lambda eeimage: eeimage.clip(eeimage.get('region')))
# 
#         #
#         #    test/debug purposes
#         #
#         if True:
#             imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
#             for iIdx in range(eeimagecollectionofstacks.size().getInfo()):
#                 exportimage = ee.Image(imageslist.get(iIdx))
#                 geemap.ee_export_image(
#                     exportimage,
#                     filename=f"C:/Users/HAESEND/tmp/{str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill) + '_' + exportimage.get('band').getInfo() }.tif", 
#                     scale=exportimage.projection().nominalScale(),                      # this scale only will determine the pixel size of the ***exported*** image
#                     region=exportimage.geometry(), file_per_band=False)
# 
#         return eeimagecollectionofstacks
# 
# 
#     def exportpointtofile(self, szid, eepoint, szdstpath, verbose=False):
#         """
#         :param szdstpath: destination filename or director name.
#         
#         in case szdstpath is an existing directory, a default filename will be generated,
#         otherwise, in case the parent directory of szdstpath  is an existing directory, szdstpath will be considered as a base filename,
#         otherwise an exception is raised
#         """
#         #
#         #    filenames filenames filenames... I hate filenames...
#         #
#         szdstpath = os.path.normpath(szdstpath)
#         if os.path.isdir(szdstpath) :
#             szbasefilename = os.path.join(szdstpath, (str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill)))
#         elif os.path.isdir(os.path.dirname(szdstpath)):
#             szbasefilename = szdstpath
#         else:
#             raise ValueError(f"invalid szdstpath ({szdstpath})")
#         if szbasefilename.lower().endswith(".tif"): szbasefilename = szbasefilename[:-4]
#         if verbose: print(f"{str(type(self).__name__)}.exportpointtofile: base filename: {szbasefilename}")
# 
#         eeimagecollectionofstacks  = self._getexportimage(eepoint, verbose=verbose)
#         imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
#         for iIdx in range(eeimagecollectionofstacks.size().getInfo()):
#             exportimage = ee.Image(imageslist.get(iIdx))
#             exportband  = exportimage.get('band').getInfo()
#             eeregion    = ee.Geometry(exportimage.get('region'))
#             #
#             #    and Yet Again: Terminal Touching pixels will be exported. Shinking the original roi with 1% of its pixel size... and pray.
#             #    TODO: implement in exportpointtodrive too
#             #
#             exportregion = eeregion.buffer(-0.01, proj=exportimage.projection())
#             if verbose:
#                 eeregionpixelcount     = exportimage.select(0).unmask(sameFootprint=False).reduceRegion(ee.Reducer.count(), eeregion)
#                 exportregionpixelcount = exportimage.select(0).unmask(sameFootprint=False).reduceRegion(ee.Reducer.count(), exportregion)
#                 print(f"{str(type(self).__name__)}.exportpointtofile (earliest image band {exportband} in stack):")
#                 print(f"- actual region: {geeutils.szprojectioninfo(eeregion)}")
#                 print(f"- area: {eeregion.area(maxError=0.001).getInfo()}")
#                 print(f"- covering {eeregionpixelcount.getInfo()} pixels in src image")
#                 print(f"- export region: {geeutils.szprojectioninfo(exportregion)}")
#                 print(f"- area: {exportregion.area(maxError=0.001).getInfo()}")
#                 print(f"- covering {exportregionpixelcount.getInfo()} pixels in src image")
#             #
#             #    exportpointtofile is mainly for debug; works only for few bands ( < 100 ), small files, fast processes 
#             #
#             szfilename = szbasefilename + "_" + exportband + ".tif"
#             geemap.ee_export_image(
#                 exportimage,
#                 filename=szfilename, 
#                 scale=exportimage.projection().nominalScale(),   # this scale only will determine the pixel size of the ***exported*** image
#                 region=exportregion, file_per_band=False)        # the ***exported*** region which is just a teeny-tiny bit smaller than it should be.
#             #
#             #    some nursing due to quirks in ee.Image.getDownloadURL (current versions: ee 0.1.248, gee 0.8.12) 
#             #    
#             try:
#                 import osgeo.gdal
#                 src_ds = osgeo.gdal.Open(szfilename)
#                 dst_ds = src_ds.GetDriver().CreateCopy(szfilename + ".tmp.tif", src_ds)
#                 #
#                 #    restore band descriptions which are mysteriously lost in the ee.Image.getDownloadURL (current versions: ee 0.1.248, gee 0.8.12)
#                 #
#                 lstbandnames = exportimage.bandNames().getInfo()
#                 for iband in range(src_ds.RasterCount):
#                     dst_ds.GetRasterBand(iband+1).SetDescription(lstbandnames[iband])
#                 #
#                 #    qgis chokes on '-inf' which is default for masked values in Float32 and Float64 images (current versions: ee 0.1.248, gee 0.8.12)
#                 #
#                 datatype = dst_ds.GetRasterBand(1).DataType
#                 if (datatype == osgeo.gdalconst.GDT_Float32) or (datatype == osgeo.gdalconst.GDT_Float64):
#                     rasterArray = dst_ds.GetRasterBand(iband+1).ReadAsArray()
#                     rasterArray[rasterArray == -math.inf] = math.nan
#                     dst_ds.GetRasterBand(iband+1).WriteArray(rasterArray)
#                     dst_ds.GetRasterBand(iband+1).SetNoDataValue(math.nan)
#                     
#                 dst_ds = None
#                 src_ds = None
#                 os.remove(szfilename)
#                 os.rename(szfilename + ".tmp.tif", szfilename)
#     
#             except Exception as e:
#                 #
#                 #    happens all the time e.g. some file is open in qgis
#                 #
#                 print(f"{str(type(self).__name__)}.exportpointtofile: updating band names FAILED with exception: {str(e)}")
#                 pass
#     
#             #
#             #    debug. export the shape file of the eeregion (and exportregion) too.
#             #
#             if verbose:                                          # yes. verbose. yes. if I verbose, I am debugging, ain't I?
#                 geemap.ee_to_shp(
#                     ee.FeatureCollection([ee.Feature(eeregion), ee.Feature(exportregion)]),
#                     szfilename[0:-4] + ".shp")
#         #
#         #
#         #
#         return eeimagecollectionofstacks
#         
# 
#     def exportpointtodrive_1(self, szid, eepoint, szdstfolder, verbose=False):
#         """
#         """
#         eeimagecollectionofstacks  = self._getexportimage(eepoint, verbose=verbose)
#         imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
#         for iIdx in range(eeimagecollectionofstacks.size().getInfo()):
#             exportimage = ee.Image(imageslist.get(iIdx))
#             #
#             #    real world batch task
#             #
#             szbasefilename = str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill)
#             szfilename = szbasefilename + "_" + exportimage.get('band').getInfo()
#             if verbose : print(f"{str(type(self).__name__)}.exportpointtodrive: exporting {szfilename}")
#             
#             eetask = ee.batch.Export.image.toDrive(
#                 image          = exportimage,
#                 region         = ee.Geometry(exportimage.get('region')),
#                 description    = szfilename,
#                 folder         = szdstfolder, #f"geeyatt_2020_{str(type(self._geeproduct).__name__)}",
#                 scale          = exportimage.projection().nominalScale().getInfo(),
#                 skipEmptyTiles = False,
#                 fileNamePrefix = szfilename,
#                 fileFormat     = 'GeoTIFF')
#             self._starttask(eetask)
# 
#         return eeimagecollectionofstacks
# 
#     def exportpointtodrive(self, szid, eepoint, szdstfolder, verbose=False):
#         """
#         """
#         verbose = True
#         eeimagecollectionofstacks  = self._getexportimage(eepoint, verbose=False)
#         imageslist = eeimagecollectionofstacks.toList(eeimagecollectionofstacks.size())
#         iIdx = 0
#         while True:
#             try:
#                 exportimage = ee.Image(imageslist.get(iIdx))
#                 szbandname  = exportimage.get('band').getInfo() # this will trigger the "ee.ee_exception.EEException: List.get" exception
#                 #
#                 #    real world batch task
#                 #
#             except Exception as e:
#                 if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: exported {iIdx} bands")
#                 return True
# 
#             try:
#                 szbasefilename = str(szid) + '_' + str(type(self._geeproduct).__name__) + '_' + geeutils.szISO8601Date(self._eedatefrom) + '_' + geeutils.szISO8601Date(self._eedatetill)
#                 szfilename = szbasefilename + "_" + szbandname
#                 if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: exporting band {szbandname} to {szfilename}")
#                 
#                 eetask = ee.batch.Export.image.toDrive(
#                     image          = exportimage,
#                     region         = ee.Geometry(exportimage.get('region')),
#                     description    = szfilename,
#                     folder         = szdstfolder, #f"geeyatt_2020_{str(type(self._geeproduct).__name__)}",
#                     scale          = exportimage.projection().nominalScale(), #.getInfo(),
#                     skipEmptyTiles = False,
#                     fileNamePrefix = szfilename,
#                     fileFormat     = 'GeoTIFF')
#                 
#                 if not self._starttask(eetask):
#                     if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: abandoned. {iIdx} bands were already exported")
#                     return False
#             except Exception as e:
#                 if verbose: print(f"{str(type(self).__name__)}.exportpointtodrive: exception. {iIdx} bands were already exported")
#                 return False
# 
#             iIdx += 1
#             pass # continue while

