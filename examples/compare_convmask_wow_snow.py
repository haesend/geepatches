import ee
if not ee.data._credentials: ee.Initialize()

import geeproduct
import geeexport
import geeutils

import os
import numpy
import osgeo.gdal
import matplotlib.pyplot

#
#
#
IAMRUNNINGONTHEMEP = False

#
#
#
def docompare(eepoint, eedatefrom, eedatetill, szoutputdir, verbose=False):
    """
    """
    #
    # in case szoutputdir has been specified - it must exist
    #
    if szoutputdir:
        if not os.path.isdir(szoutputdir) : raise ValueError(f"invalid szoutputdir ({str(szoutputdir)})")
    #
    #
    #
    s2sclcppfilter    = geeproduct.S2sclcppfilter()    # using default  'cloudy pixel percentage' filter: maximum 95% pixels have SCL class 8,9 or 10
    refcol            = geeproduct.GEECol_s2scl()      # using sentinel 2 20m as reference  
    refcolpix         = 64                             # using square paches of 64 x 20m = 1280m    
    
    s2ndvi            = geeproduct.GEECol_s2ndvi(s2sclcppfilter) # ndvi as index of interest
    s2rgb             = geeproduct.GEECol_s2rgb(s2sclcppfilter)  # rbb images to be exported as verification
    s2scl             = geeproduct.GEECol_s2scl(s2sclcppfilter)

    #
    # considering a combi-mask which considers 'snow' as 'valid' class
    #
    combi_keep_snow   = geeproduct.GEECol_s2sclcombimask(
        conv_lsts2sclclassesarray       = [[2, 4, 5, 6, 7, 11], [3, 8, 9, 10]],
        conv_lstwindowsizeinmeters       = [20*9, 20*101],
        conv_lstthreshold                = [-0.057, 0.025],
        colfilter                        = s2sclcppfilter,
        stat_s2sclclassesarray           = [3, 8, 9, 10], 
        stat_threshold                   = 2, 
        stat_thresholdunits              = "sigma", 
        stat_statisticsareametersradius  = 25000, 
        stat_idaysbackward               = 365
        )

    #
    # considering a combi-mask which considers 'snow' as 'dirty' class
    #
    combi_mask_snow   = geeproduct.GEECol_s2sclcombimask(
        conv_lsts2sclclassesarray       = [[2, 4, 5, 6, 7], [3, 8, 9, 10, 11]],
        conv_lstwindowsizeinmeters       = [20*9, 20*101],
        conv_lstthreshold                = [-0.057, 0.025],
        colfilter                        = s2sclcppfilter,
        stat_s2sclclassesarray           = [3, 8, 9, 10], 
        stat_threshold                   = 2, 
        stat_thresholdunits              = "sigma", 
        stat_statisticsareametersradius  = 25000, 
        stat_idaysbackward               = 365
        )    

    #
    # getcollection's
    #
    s2ndvicollection   = s2ndvi.getcollection         (eedatefrom, eedatetill, eepoint, refcolpix*2, refcol, refcolpix, verbose=verbose)
    keepsnowcollection = combi_keep_snow.getcollection(eedatefrom, eedatetill, eepoint, refcolpix,   refcol, refcolpix, verbose=verbose)
    masksnowcollection = combi_mask_snow.getcollection(eedatefrom, eedatetill, eepoint, refcolpix,   refcol, refcolpix, verbose=verbose)

    #
    # in case szoutputdir has been specified - and exists - we'll export tiff's
    #
    if szoutputdir:
        
        s2sclcollection =  s2scl.getcollection(eedatefrom, eedatetill, eepoint, refcolpix,                       verbose=verbose)
        s2rgbcollection =  s2rgb.getcollection (eedatefrom, eedatetill, eepoint, refcolpix*2, refcol, refcolpix, verbose=verbose)

        geeexport.GEEExp().exportimages(s2sclcollection,    szoutputdir, szfilenameprefix="",           verbose=verbose)
        geeexport.GEEExp().exportimages(s2rgbcollection,    szoutputdir, szfilenameprefix="",           verbose=verbose)
        geeexport.GEEExp().exportimages(s2ndvicollection,   szoutputdir, szfilenameprefix="",           verbose=verbose)
        geeexport.GEEExp().exportimages(keepsnowcollection, szoutputdir, szfilenameprefix="keep_snow_", verbose=verbose)
        geeexport.GEEExp().exportimages(masksnowcollection, szoutputdir, szfilenameprefix="mask_snow_", verbose=verbose)

    #
    # assign the masks to the product - add the masked product as bands
    #
    s2ndvicollection = ee.ImageCollection(ee.Join.saveFirst('keepsnow').apply(**{
            'primary': s2ndvicollection,
            'secondary': keepsnowcollection,
            'condition': ee.Filter.equals(**{'leftField': 'gee_date', 'rightField': 'gee_date'})}))

    s2ndvicollection = ee.ImageCollection(ee.Join.saveFirst('masksnow').apply(**{
            'primary': s2ndvicollection,
            'secondary': masksnowcollection,
            'condition': ee.Filter.equals(**{'leftField': 'gee_date', 'rightField': 'gee_date'})}))
    
    def addmaskedbands(image):
        keepsnowmask = ee.Image(image.get('keepsnow'))
        masksnowmask = ee.Image(image.get('masksnow'))
        keepsnowmaskedndvi = image.updateMask(keepsnowmask.eq(0))
        masksnowmaskedndvi = image.updateMask(masksnowmask.eq(0))
        return image.addBands(ee.Image([masksnowmaskedndvi, keepsnowmaskedndvi])).rename(['NDVI', 'NDVI_MASKED_MASKSNOW', 'NDVI_MASKED_KEEPSNOW'])
        
    s2ndvicollection = s2ndvicollection.map(addmaskedbands)

    #
    # in case szoutputdir has been specified - and exists - we'll the masked tiff's too
    #        
    if szoutputdir:
        geeexport.GEEExp().exportimages(
            s2ndvicollection.select(['NDVI_MASKED_MASKSNOW', 'NDVI_MASKED_KEEPSNOW']), 
            szoutputdir, szfilenameprefix='', verbose=verbose)
    #
    # calculate (average) time-series for raw and masked products - hope we don't get "EEException: Too many concurrent aggregations."
    #
    def average(img):
        img = ee.Image(img)
        avg = ee.Image(img).reduceRegion(ee.Reducer.mean(), geometry=s2ndvicollection.get('gee_refroi'), maxPixels = 1e13)
        avg = avg.set('gee_date', img.get('gee_date'))
        return avg
    
    averages = s2ndvicollection.toList(s2ndvicollection.size().getInfo()).map(average)

    tsndvi = {}
    tsndvi_masked_masksnow = {}
    tsndvi_masked_keepsnow = {}
    for element in averages.getInfo():
        sziso8601date        = element.get('gee_date')
        ndvi                 = element.get('NDVI')
        ndvi_masked_masksnow = element.get('NDVI_MASKED_MASKSNOW')
        ndvi_masked_keepsnow = element.get('NDVI_MASKED_KEEPSNOW')
        if ndvi:                 tsndvi.update({sziso8601date: float(ndvi)})
        if ndvi_masked_masksnow: tsndvi_masked_masksnow.update({sziso8601date: float(ndvi_masked_masksnow)})
        if ndvi_masked_keepsnow: tsndvi_masked_keepsnow.update({sziso8601date: float(ndvi_masked_keepsnow)})

    #
    #    color:  'green', 'blue', 'red', '#FFA500'
    #    marker: None, 'x', 'o', '+', '.'
    #    markersize: 8, 16, 18
    #    fillstyle: 'none', 'full', 'top', 'bottom', 'left', 'right
    #    linestyle: 'none', 'solid', 'dotted', 
    #
    rows = 1
    cols = 1
    subplots = numpy.empty( (rows,cols), dtype=object )
    
    figure = matplotlib.pyplot.figure(figsize=(16,9))
    for irow in range(rows):
        for icol in range(cols):
            subplots[irow, icol] = figure.add_subplot(rows, cols, 1 + icol + irow * cols)
    
    row = 0; col = 0
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (list(tsndvi_masked_keepsnow.keys())), list(tsndvi_masked_keepsnow.values()),
                                         color='#0000FF',   linestyle='solid',  marker='o', markersize=12, fillstyle='full'); line.set_label('KEEPSNOW')  
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (list(tsndvi_masked_masksnow.keys())), list(tsndvi_masked_masksnow.values()),
                                         color='#FFA500',   linestyle='dotted', marker='o', markersize=18, fillstyle='none'); line.set_label('MASKSNOW')  
    line, = subplots[row, col].plot_date(matplotlib.dates.datestr2num (list(tsndvi.keys())), list(tsndvi.values()),
                                         color='#FF0000',   linestyle='none',   marker='o', markersize=6,  fillstyle='full'); line.set_label('NDVI RAW')  


    szdescription  = s2ndvicollection.get('gee_description').getInfo()
    szyyyymmddfrom = eedatefrom.format('YYYYMMdd').getInfo()
    szyyyymmddtill = eedatetill.format('YYYYMMdd').getInfo()
    szpointlon     = f"{eepoint.coordinates().get(0).getInfo():013.8f}"
    szpointlat     = f"{eepoint.coordinates().get(1).getInfo():013.8f}"
    sztitle        = f"{szdescription}_Lon{szpointlon}_Lat{szpointlat}_From{szyyyymmddfrom}_Till{szyyyymmddtill}"


    subplots[row, col].set_title(sztitle)
    subplots[row, col].legend()
    
    
    for irow in range(rows):
        for icol in range(cols):
            subplots[irow, icol].xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d/%m/%Y'))
            for tick in subplots[irow, icol].get_xticklabels(): tick.set_rotation(45)
    
    #
    # in case szoutputdir has been specified - and exists - we'll save the figure
    #        
    if szoutputdir:
        matplotlib.pyplot.savefig(os.path.join(szoutputdir, f"{sztitle}.png"), dpi=300)

    else:
        matplotlib.pyplot.show()
    #
    #    close('all') should be enough, but once upon a time it still seamed to leak
    #
    figure.clear()
    matplotlib.pyplot.close(figure)
    matplotlib.pyplot.close('all')

"""
"""
def main():

    #
    #    params
    #
    eedatefrom     = ee.Date("2020-01-01")
    eedatetill     = ee.Date("2022-01-01")
    verbose        = False
    #
    #
    #
    lsteepoints = [
        geeutils.bobspoint,
        geeutils.tapspoint,
        geeutils.antwerppoint,
        geeutils.snauangard,
        geeutils.orenburgskaya,
        geeutils.taminspoint,
        ]
    for eepoint in lsteepoints:
        #
        #    blabla
        #
        szpointlon     = f"{eepoint.coordinates().get(0).getInfo():013.8f}"
        szpointlat     = f"{eepoint.coordinates().get(1).getInfo():013.8f}"
        szsubdirname   = f"Lon{szpointlon}_Lat{szpointlat}"
        
        szoutputdir = None
        if False:
            szoutputroot   = r"/vitodata/CropSAR/tmp/dominique/gee/tmp" if IAMRUNNINGONTHEMEP else r"C:\tmp"
            szoutputdir    = os.path.join(szoutputroot, szsubdirname)
            if not os.path.isdir(szoutputdir) : 
                os.mkdir(szoutputdir)
                if not os.path.isdir(szoutputdir) : raise ValueError(f"could not create szoutputdir ({str(szoutputdir)})")
                os.chmod(szoutputdir, 0o777)
        #
        #    get some work done.
        #
        docompare(eepoint, eedatefrom, eedatetill, szoutputdir, verbose=verbose)


"""
"""    
if __name__ == '__main__':
    print('starting main')
    main()
    print('finishing main')
