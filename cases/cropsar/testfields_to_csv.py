"""
read back exporting tiffs for parcels as specified in CropSAR I shape files - generated by export testfields
create csv files with all obtainable S1 and S2 data averaged over the field shapes

 
S1 csv files columns:
        S1sigma0_VV_ASC,  S1sigma0_VV_DES,  
        S1sigma0_VH_ASC,  S1sigma0_VH_DES,
        S1sigma0_VV_XXX,  
        S1sigma0_VH_XXX,  
        S1Asigma0_VV_ASC, S1Asigma0_VV_DES, 
        S1Asigma0_VH_ASC, S1Asigma0_VH_DES,
        S1Asigma0_VV_XXX, 
        S1Asigma0_VH_XXX, 
        S1Bsigma0_VV_ASC, S1Bsigma0_VV_DES, 
        S1Bsigma0_VH_ASC, S1Bsigma0_VH_DES,
        S1Bsigma0_VV_XXX, S1Bsigma0_VH_XXX, 
        S1Xsigma0_VV_ASC, S1Xsigma0_VV_DES, 
        S1Xsigma0_VH_ASC, S1Xsigma0_VH_DES,
        S1Xsigma0_VV_XXX, S1Xsigma0_VH_XXX
    
        S1gamma0_VV_ASC,  S1gamma0_VV_DES,  
        S1gamma0_VH_ASC,  S1gamma0_VH_DES,
        S1gamma0_VV_XXX,  
        S1gamma0_VH_XXX,
        S1Agamma0_VV_ASC, S1Agamma0_VV_DES, 
        S1Agamma0_VH_ASC, S1Agamma0_VH_DES,
        S1Agamma0_VV_XXX, 
        S1Agamma0_VH_XXX,
        S1Bgamma0_VV_ASC, S1Bgamma0_VV_DES, 
        S1Bgamma0_VH_ASC, S1Bgamma0_VH_DES,
        S1Bgamma0_VV_XXX, 
        S1Bgamma0_VH_XXX,
        S1Xgamma0_VV_ASC, S1Xgamma0_VV_DES, 
        S1Xgamma0_VH_ASC, S1Xgamma0_VH_DES,
        S1Xgamma0_VV_XXX, 
        S1Xgamma0_VH_XXX

S2 csv files columns:
        S2fapar,
        S2fapar_S2sclconvmask,
        S2fapar_S2sclcombimask,
        S2ndvi,
        S2ndvi_S2sclconvmask,
        S2ndvi_S2sclcombimask

"""

import os
import logging

import numpy
import osgeo.gdal
import pandas

from utils_testfields import CropSARParcels


###############################################################################
#
#    some debug aids
#
###############################################################################

def dbg_print_numpyarray(numpyarray):
    print(f"type(numpyarray):                                  {type(numpyarray)}")
    print(f"numpyarray.shape):                                 {numpyarray.shape}")
    print(f"numpyarray.dtype):                                 {numpyarray.dtype}")
    print(f"numpy.count_nonzero(numpy.isnan(numpyarray)):      {numpy.count_nonzero(numpy.isnan(numpyarray))}")
    print(f"numpy.count_nonzero(numpy.isfinite((numpyarray)):  {numpy.count_nonzero(numpy.isfinite(numpyarray))}")
    print(f"numpy.count_nonzero(~numpy.isfinite((numpyarray)): {numpy.count_nonzero(~numpy.isfinite(numpyarray))}")
    print(f"numpy.count_nonzero([numpyarray == 1]):            {numpy.count_nonzero([numpyarray == 1])}")
    print(f"numpy.count_nonzero([numpyarray == 0]):            {numpy.count_nonzero([numpyarray == 0])}")
    print(f"numpy.count_nonzero([numpyarray  > 1]):            {numpy.count_nonzero([numpyarray  > 1])}")
    print(f"numpy.count_nonzero([numpyarray <= 1]):            {numpy.count_nonzero([numpyarray <= 1])}")
    if 0 < numpy.count_nonzero(numpy.isfinite(numpyarray)):
        print(f"numpyarray[numpy.isfinite(numpyarray)].min():      {numpyarray[numpy.isfinite(numpyarray)].min()}")
        print(f"numpyarray[numpy.isfinite(numpyarray)].max():      {numpyarray[numpy.isfinite(numpyarray)].max()}")
        print(f"numpy.nanmean(numpyarray):                         {numpy.nanmean(numpyarray)}")
    print()

def dbg_print_pandasdataframe(dataframe):
    print(f"type(dataframe):                                   {type(dataframe)}")
    print(f"dataframe.index:                                   {dataframe.index}")
    print(f"dataframe.columns:                                 {dataframe.columns}")
    print(f"dataframe.dtypes:                                  {dataframe.dtypes}")
    print(f"dataframe.shape:                                   {dataframe.shape} - rows: {dataframe.shape[0]} columns: {dataframe.shape[1]}")
    print(f"dataframe.info():");                                dataframe.info()
    print(f"dataframe.head():                                \n{dataframe.head()}")
    print()



###############################################################################
#
#    averages of S1 and S2 products (parcel -> field)
#
###############################################################################

#
#
#
def parcels1productmeandict(szparceldirpath,
                            szparcelproddescription, fprodvlo=None, fprodvhi=None, 
                            szfieldshapefile=None,
                            szparcelcsvdirpath=None,
                            verbose=False):
    """
    read product files - typical S1Agamma0_VV_ASC ... S1Bsigma0_VH_DES
    convert from db to linear values
    calculate average of these values over the parcel or field (if shape was specified)
    return time series dict e.g. { '2020-01-05':0.5, '2020-01-09':0.4, ..., '2021-12-26':0.6 }
    """

    def to_linear(numpyarray_db):
        '''
        Function to transform numpy.ndarray from decibels to linear values
        :param data_db: numpy.ndarray with decibel values
        :return: numpy.ndarray with linear values
        '''
        return numpy.power(10, numpyarray_db/10)
    
    def to_db(numpyarray_linear):
        '''
        Function to transform numpy.ndarray from linear to decibel values
        :param data_linear: numpy.ndarray with linear values
        :return: numpy.ndarray with decibel values
        '''
        return 10*numpy.log10(numpyarray_linear)
    #
    #
    #
    if not os.path.isdir(szparceldirpath) : raise ValueError(f"invalid parcel directory szparceldirpath ({str(szparceldirpath)})")      # src dir must exist
    #
    #
    #
    parcelproductmeandict = {}
    
    parcelfilesdict = CropSARParcels.findproductsfilesdict(szparceldirpath)
    if not parcelfilesdict:
        logging.warning(f"no product files found in {szparceldirpath}")
        return parcelproductmeandict # {}
        
    prodfilesdict   = parcelfilesdict.get(szparcelproddescription, {})
    if not prodfilesdict:
        logging.warning(f"no product {szparcelproddescription} files found in {szparceldirpath}")
        return parcelproductmeandict # {}
    

    numpyparrayfieldmask = None
    if szfieldshapefile:
        gdalfieldmaskdataset = CropSARParcels.cropsar_shptomsk_dataset(szfieldshapefile, list(prodfilesdict.values())[0])
        numpyparrayfieldmask = gdalfieldmaskdataset.ReadAsArray().astype(bool) # "assume mask = 1 = outside field, unmasked = 0 = insidefield"
        ifieldpixelscount    = numpy.count_nonzero([numpyparrayfieldmask == 0])
        if verbose: logging.info(f"getparcels1productmeandict({szparcelproddescription}): field pixels count: {ifieldpixelscount}")
        gdalfieldmaskdataset = None

    for sziso8601date in prodfilesdict.keys():
        szprodfilename = prodfilesdict.get(sziso8601date, None)
        if not szprodfilename:
            logging.warning(f"getparcels1productmeandict({szparcelproddescription}): {sziso8601date}: skipped: missing {szparcelproddescription} product file")
            continue # skip this date
        #
        #    read product file, 
        #    remove inf's and nan's (typical flags for 'float' products)
        #    remove values outside vlo and vhi (typical flags for 'integer' products)
        #
        gdalproddataset = osgeo.gdal.Open(szprodfilename)
        numpyparrayprod = gdalproddataset.ReadAsArray().astype(numpy.float32)
        numpyparrayprod[~numpy.isfinite(numpyparrayprod)]      = numpy.nan
        if fprodvlo: numpyparrayprod[numpyparrayprod<fprodvlo] = numpy.nan
        if fprodvhi: numpyparrayprod[numpyparrayprod>fprodvhi] = numpy.nan
        #
        #    in case a field shapefile was specified (and could be read)
        #
        if numpyparrayfieldmask is not None:
            numpyparrayprod[numpyparrayfieldmask] = numpy.nan
            ifieldclearpix = numpy.count_nonzero(numpy.isfinite(numpyparrayprod))
            if verbose: logging.info(f"getparcels1productmeandict({szparcelproddescription}): {sziso8601date}: clear field fixels: {ifieldclearpix}")
    
        #
        #    finally: calculate mean value of remaining pixels and add it to the series dictionary
        #    - avoid "RuntimeWarning: Mean of empty slice"
        #    - what would be mean of [+inf, -inf, ...] ? nan them just to be sure
        #
        numpyparrayprod[~numpy.isfinite(numpyparrayprod)] = numpy.nan
        ipixels = numpy.count_nonzero(numpy.isfinite(numpyparrayprod))
        if 0 < ipixels:
            mean = to_db(numpy.nanmean(to_linear(numpyparrayprod)))
            if numpy.isfinite(mean):
                if verbose: logging.info(f"getparcels1productmeandict({szparcelproddescription}): {sziso8601date}: pixels: {ipixels} - mean value: {mean}")
                parcelproductmeandict.update({sziso8601date : mean})
    #
    #    in case csv output directory has been specified - and exists - we'll export the dictionary as csv
    #
    if szparcelcsvdirpath:
        if not os.path.isdir(szparcelcsvdirpath) : raise ValueError(f"invalid szparcelcsvdirpath ({str(szparcelcsvdirpath)})")  # root must exist
        szcsvfile = os.path.join(szparcelcsvdirpath, szparcelproddescription + ".csv")
        pandas.DataFrame.from_dict(parcelproductmeandict, orient='index', columns=[szparcelproddescription]).to_csv(szcsvfile)
        if verbose: logging.info(f"getparcels1productmeandict({szparcelproddescription}): csv file: {os.path.basename(szcsvfile)}")
    #
    #    return dict
    #
    return parcelproductmeandict

#
#
#
def parcels2productmeandict(szparceldirpath, 
                            szparcelproddescription, fprodvlo=None, fprodvhi=None, 
                            szparcelmaskdescription=None, iparcelminclearpct=0,
                            szfieldshapefile=None, ifieldminclearpct=0,
                            szparcelcsvdirpath=None,
                            verbose=False):
    """
    read product and optinal mask files - typical s2fapar, s2ndvi
    calculate average value of the (masked) product
    return time series dict e.g. { '2020-01-05':0.5, '2020-01-09':0.4, ..., '2021-12-26':0.6 }

    remark: not suited for S1 which are in db, nor for s2 scl which is a classification
    """
    #
    #
    #
    if not os.path.isdir(szparceldirpath) : raise ValueError(f"invalid parcel directory szparceldirpath ({str(szparceldirpath)})")      # src dir must exist
    #
    #
    #
    parcelproductmeandict = {}
    
    parcelfilesdict = CropSARParcels.findproductsfilesdict(szparceldirpath)
    if not parcelfilesdict:
        logging.warning(f"no product files found in {szparceldirpath}")
        return parcelproductmeandict # {}
        
    prodfilesdict   = parcelfilesdict.get(szparcelproddescription, {})
    if not prodfilesdict:
        logging.warning(f"no product {szparcelproddescription} files found in {szparceldirpath}")
        return parcelproductmeandict # {}
    
    maskfilesdict = None
    if szparcelmaskdescription:
        maskfilesdict = parcelfilesdict.get(szparcelmaskdescription, {})
        
    numpyparrayfieldmask = None
    if szfieldshapefile:
        gdalfieldmaskdataset = CropSARParcels.cropsar_shptomsk_dataset(szfieldshapefile, list(prodfilesdict.values())[0])
        numpyparrayfieldmask = gdalfieldmaskdataset.ReadAsArray().astype(bool) # "assume mask = 1 = outside field, unmasked = 0 = insidefield"
        ifieldpixelscount    = numpy.count_nonzero([numpyparrayfieldmask == 0])
        ifieldminclearpix    = int(ifieldminclearpct * ifieldpixelscount / 100.)
        if verbose: logging.info(f"getparcels2productmeandict({szparcelproddescription}): field pixels count: {ifieldpixelscount} - minimum clear: {ifieldminclearpix} ({ifieldminclearpct}pct)")
        gdalfieldmaskdataset = None

    for sziso8601date in prodfilesdict.keys():
        szprodfilename = prodfilesdict.get(sziso8601date, None)
        if not szprodfilename:
            logging.warning(f"getparcels2productmeandict({szparcelproddescription}): {sziso8601date} skipped: missing {szparcelproddescription} product file")
            continue # skip this date
        szmaskfilename = None
        if maskfilesdict:
            szmaskfilename = maskfilesdict.get(sziso8601date, None)
            if not szmaskfilename:
                logging.warning(f"getparcels2productmeandict({szparcelproddescription}): {sziso8601date} skipped: missing {szparcelmaskdescription} mask file")
                continue # skip this date
        #
        #    read product file, 
        #    remove inf's and nan's (typical flags for 'float' products)
        #    remove values outside vlo and vhi (typical flags for 'integer' products)
        #
        gdalproddataset = osgeo.gdal.Open(szprodfilename)
        numpyparrayprod = gdalproddataset.ReadAsArray().astype(numpy.float32)
        numpyparrayprod[~numpy.isfinite(numpyparrayprod)]      = numpy.nan
        if fprodvlo: numpyparrayprod[numpyparrayprod<fprodvlo] = numpy.nan
        if fprodvhi: numpyparrayprod[numpyparrayprod>fprodvhi] = numpy.nan
        #
        #    in case a mask was specified (and found)
        #
        if szmaskfilename:
            #
            #    read mask file as boolean values, reprojected to product crs
            #    todo: case mask has no data?
            #    remove masked values (mask not 0) in product
            #
            gdalSRCmaskdataset = osgeo.gdal.Open(szmaskfilename)
            gdalDSTmaskdataset = osgeo.gdal.GetDriverByName('MEM').Create( '', gdalproddataset.RasterXSize, gdalproddataset.RasterYSize, 1, gdalSRCmaskdataset.GetRasterBand(1).DataType)
            gdalDSTmaskdataset.SetGeoTransform(gdalproddataset.GetGeoTransform())
            gdalDSTmaskdataset.SetProjection(gdalproddataset.GetProjection())
            osgeo.gdal.ReprojectImage(gdalSRCmaskdataset, gdalDSTmaskdataset, gdalSRCmaskdataset.GetProjection(), gdalDSTmaskdataset.GetProjection(), osgeo.gdalconst.GRA_Mode)
            numpyparrayprodmask = gdalDSTmaskdataset.ReadAsArray().astype(numpy.bool)

            numpyparrayprod[numpyparrayprodmask] = numpy.nan

            gdalDSTmaskdataset = None
            gdalSRCmaskdataset = None

            iparcelpixelscount = numpy.size(numpyparrayprod)
            iparcelminclearpix = int(iparcelminclearpct * iparcelpixelscount / 100.)
            iparcelclearpix    = numpy.count_nonzero(numpy.isfinite(numpyparrayprod))
            if iparcelclearpix < iparcelminclearpix: 
                if verbose: logging.info(f"getparcels2productmeandict({szparcelproddescription}): {sziso8601date} skipped: unmasked parcel pixels ({iparcelclearpix}) < minimum ({iparcelminclearpix})")
                continue
            
        #
        #    in case a field shapefile was specified (and could be read)
        #
        if numpyparrayfieldmask is not None:
            numpyparrayprod[numpyparrayfieldmask] = numpy.nan
            ifieldclearpix = numpy.count_nonzero(numpy.isfinite(numpyparrayprod))
            if ifieldclearpix < ifieldminclearpix: 
                if verbose: logging.info(f"getparcels2productmeandict({szparcelproddescription}): {sziso8601date} skipped: clear field fixels ({ifieldclearpix}) < minimum ({ifieldminclearpix})")
                continue
                                
        #
        #    finally: calculate mean value of remaining pixels and add it to the series dictionary
        #    - avoid "RuntimeWarning: Mean of empty slice"
        #    - what would be mean of [+inf, -inf, ...] ? nan them just to be sure
        #
        numpyparrayprod[~numpy.isfinite(numpyparrayprod)] = numpy.nan
        ipixels = numpy.count_nonzero(numpy.isfinite(numpyparrayprod))
        if 0 < ipixels:
            mean = numpy.nanmean(numpyparrayprod)
            if numpy.isfinite(mean):
                if verbose: logging.info(f"getparcels2productmeandict({szparcelproddescription}): {sziso8601date}: pixels: {ipixels} - mean value: {mean}")
                parcelproductmeandict.update({sziso8601date : mean})
    #
    #    in case csv output directory has been specified - and exists - we'll export the dictionary as csv
    #
    if szparcelcsvdirpath:
        if not os.path.isdir(szparcelcsvdirpath) : raise ValueError(f"invalid szparcelcsvdirpath ({str(szparcelcsvdirpath)})")  # root must exist
        szcsvfile = os.path.join(szparcelcsvdirpath, szparcelproddescription + ".csv")
        pandas.DataFrame.from_dict(parcelproductmeandict, orient='index', columns=[szparcelproddescription]).to_csv(szcsvfile)
        if verbose: logging.info(f"getparcels2productmeandict({szparcelproddescription}): csv file: {os.path.basename(szcsvfile)}")
    #
    #    return dict
    #
    return parcelproductmeandict



###############################################################################
#
#    averages of S1 and S2 products (parcel -> field)
#
###############################################################################

#
#
#
def parcels1dataframe(szparceldirpath,
                      szfieldshapefile=None,
                      szparcelcsvdirpath=None,
                      verbose=False):
    """
    read all S1 product files found in szparceldirpath 
    apply parcels1productmeandict on these products
    derive combinations of orbitpasses and platforms
    return dataframe (index on dates, column for each product and derivate)
    
    remarks:
    parcels1productmeandict parameter szparcelproddescription is instantiated locally from potential 'original' products
        beware possible values depend on the implementations in geeproduct, geeexport, geebatch and export_testfield
        also, the fprodvlo and fprodvhi parameters are lost since they vary over the original products; should be hardcoded here.

    VV/VH combination not implemented since they have always been kept separate in cropsar.
    in case we want them, we need to think about the combined value: 
        VV and VH DO occur on the same date, 
        and are expressed in decibel
        => no straight formward .mean(...)
    """

    #
    #
    #
    if not os.path.isdir(szparceldirpath) : raise ValueError(f"invalid parcel directory szparceldirpath ({str(szparceldirpath)})")      # src dir must exist
    #
    #    all original products
    #
    szS1proddescriptions = ['S1' + p + s + '_'+ v + '_' + o
                            for p in ['', 'A', 'B', 'X']
                            for s in ['sigma0', 'gamma0']
                            for v in ['VV', 'VH'] 
                            for o in ['ASC', 'DES']]
 
    parceldataframe = pandas.DataFrame()

    for szparcelproddescription in szS1proddescriptions:
        productmeandict = parcels1productmeandict(szparceldirpath, szparcelproddescription,
                                                  szfieldshapefile=szfieldshapefile, verbose=verbose)
        if not productmeandict: continue
        parceldataframe = pandas.merge(parceldataframe, 
                                       pandas.DataFrame.from_dict(productmeandict, orient='index', columns=[szparcelproddescription]),
                                       how='outer', left_index=True, right_index=True) 
    #
    #    determine derived products
    #

    #
    #    combine platforms (S1A U S1B = S1X)
    #
    combinedprodsdict = {}
    for szparcelproddescription in szS1proddescriptions:
        if szparcelproddescription.startswith('S1A'):
            szparcelpartnerproddescription = 'S1B' + szparcelproddescription[3:]
            if (szparcelproddescription in parceldataframe.columns) and (szparcelpartnerproddescription in parceldataframe.columns):
                szcombinedproddescription = 'S1X' + szparcelproddescription[3:]
                combinedprodsdict.update({szcombinedproddescription:parceldataframe[[szparcelproddescription, szparcelpartnerproddescription]].mean(axis=1)})
    #
    #    add them to dataframe
    #
    for szcombinedproddescription, combinedproddataseries in combinedprodsdict.items():
        parceldataframe[szcombinedproddescription] = combinedproddataseries

    #
    #    combine orbit passes (ASC U DES => XXX)
    #
    combinedprodsdict = {}
    for szparcelproddescription in szS1proddescriptions:
        if szparcelproddescription.endswith('_ASC'):
            szparcelpartnerproddescription = szparcelproddescription[:-4] + '_DES'
            if (szparcelproddescription in parceldataframe.columns) and (szparcelpartnerproddescription in parceldataframe.columns):
                szcombinedproddescription = szparcelproddescription[:-4] + '_XXX'
                combinedprodsdict.update({szcombinedproddescription:parceldataframe[[szparcelproddescription, szparcelpartnerproddescription]].mean(axis=1)})
    #
    #    add them to dataframe
    #
    for szcombinedproddescription, combinedproddataseries in combinedprodsdict.items():
        parceldataframe[szcombinedproddescription] = combinedproddataseries
    #
    #    in case csv output directory has been specified - and exists - we'll export the dataframe as csv
    #
    if szparcelcsvdirpath:
        if not os.path.isdir(szparcelcsvdirpath) : raise ValueError(f"invalid szparcelcsvdirpath ({str(szparcelcsvdirpath)})")  # root must exist
        szcsvfile = os.path.join(szparcelcsvdirpath, "S1data.csv")
        parceldataframe.astype(numpy.float16).to_csv(szcsvfile) # save some space with float16
        if verbose: logging.info(f"parcels1dataframe({szparcelproddescription}): csv file: {os.path.basename(szcsvfile)}")
    
    return parceldataframe

#
#
#
def parcels2dataframe(szparceldirpath,
                      szfieldshapefile=None,
                      szparcelcsvdirpath=None,
                      verbose=False):
    """
    read S2 index product files found in szparceldirpath (only S2ndvi and S2fapar)
    read S2 mask product files found in szparceldirpath (only S2sclconvmask and S2sclcombimask)
    apply parcels2productmeandict on these products 
        - fixed iparcelminclearpct and ifieldminclearpct parameters
        - different mask combinations 
    return dataframe (index on dates, column for each product-mask combination)
    """

    #
    #
    #
    if not os.path.isdir(szparceldirpath) : raise ValueError(f"invalid parcel directory szparceldirpath ({str(szparceldirpath)})")      # src dir must exist
    #
    #    all original products
    #
    szS2proddescriptions = ['S2fapar', 'S2ndvi']
    szS2maskdescriptions = ['S2sclconvmask', 'S2sclcombimask']
    iparcelminclearpct   = 10
    ifieldminclearpct    = 20
 
    parceldataframe = pandas.DataFrame()

    for szparcelproddescription in szS2proddescriptions:
        productmeandict = parcels2productmeandict(szparceldirpath, szparcelproddescription,
                                                  szfieldshapefile=szfieldshapefile, verbose=verbose)
        if not productmeandict: continue
        parceldataframe = pandas.merge(parceldataframe, 
                                       pandas.DataFrame.from_dict(productmeandict, orient='index', columns=[szparcelproddescription]),
                                       how='outer', left_index=True, right_index=True) 

        for szparcelmaskdescription in szS2maskdescriptions:
            productmeandict = parcels2productmeandict(szparceldirpath, szparcelproddescription,
                                                      szparcelmaskdescription=szparcelmaskdescription, iparcelminclearpct=iparcelminclearpct,
                                                      szfieldshapefile=szfieldshapefile, ifieldminclearpct=ifieldminclearpct, verbose=verbose)
            if not productmeandict: continue
            parceldataframe = pandas.merge(parceldataframe, 
                                           pandas.DataFrame.from_dict(productmeandict, orient='index', columns=[szparcelproddescription+"_"+szparcelmaskdescription]),
                                           how='outer', left_index=True, right_index=True) 
    #
    #    in case csv output directory has been specified - and exists - we'll export the dataframe as csv
    #
    if szparcelcsvdirpath:
        if not os.path.isdir(szparcelcsvdirpath) : raise ValueError(f"invalid szparcelcsvdirpath ({str(szparcelcsvdirpath)})")  # root must exist
        szcsvfile = os.path.join(szparcelcsvdirpath, "S2data.csv")
        parceldataframe.astype(numpy.float16).to_csv(szcsvfile) # save some space with float16
        if verbose: logging.info(f"parcels2dataframe({szparcelproddescription}): csv file: {os.path.basename(szcsvfile)}")
    
    return parceldataframe

#
#
#
def main():
    if True:
        szsrcrootdirpath = r"C:\tmp\CropSARParcels\tif"
        szdstrootdirpath = r"C:\tmp\CropSARParcels\csv"
    else:
        szsrcrootdirpath = r"/vitodata/CropSAR/tmp/dominique/gee/CropSARParcels/tif"
        szdstrootdirpath = r"/vitodata/CropSAR/tmp/dominique/gee/CropSARParcels/csv"
    
    for icroptype, szcroptypedirpath in CropSARParcels.findcroptypedirectoriesdict(szsrcrootdirpath).items():
        for szfieldID, szparceldirpath in CropSARParcels.findfieldIDdirectoriesdict(szcroptypedirpath).items():
            szfieldshapefile   = os.path.join(szparceldirpath, szfieldID + ".shp")
            szparcelcsvdirpath = CropSARParcels.getparceldirectory(szdstrootdirpath, icroptype, szfieldID)
            parcels2dataframe(szparceldirpath, szfieldshapefile=szfieldshapefile, szparcelcsvdirpath=szparcelcsvdirpath, verbose=True)    
            parcels1dataframe(szparceldirpath, szfieldshapefile=szfieldshapefile, szparcelcsvdirpath=szparcelcsvdirpath, verbose=True)    
 

"""
"""    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname).3s {%(module)s:%(funcName)s:%(lineno)d} - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    print('starting main')
    main()
    print('exit main')

