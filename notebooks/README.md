
***
geepatches notebooks:
***
__general__
***
- ex_0000_0100_0100_exploring_s1: experimenting with S1 collections
<br> e.g. COPERNICUS/S1_GRD_FLOAT vs COPERNICUS/S1_GRD
<br> e.g. weird footprint of 'angle' band
<br> ...


***
__utilities and obtaining reference roi__
- ex_0100_0100_0100_geeutils_squareareaboundsroi: tryout geeutils.squareareaboundsroi method
- ex_0100_0100_0120_geeutils_squarerasterboundsroi: tryout geeutils.squarerasterboundsroi method
- ex_0100_0100_0130_geeutils_centerpixelpoint: tryout geeutils.pixelcenterpoint and geeutils.pixelinterspoint methods
- ex_0300_0100_0100_geeutils_selection_reference_point: shift point to pixel center or raster intersection for odd/even roi's
- ex_0300_0100_0200_geeutils_selection_reference_roi: matching reference roi to other products


***
__GEECol classes__ :
- ex_0500_0100_0100_geeproduct: (native) collections of GEECol daughter classes
- ex_0500_0100_0200_geeproduct_reference_s2_10m: using reference roi
- ex_0500_0100_0210_geeproduct_reference_s2_20m: prefer S2 20m in case S2 20m and 10m are involved


***
__GEEExp class__ :
- ex_0700_0100_0100_geeexport: demo GEEExp.exportimages

***
__classification based masks__ :
- ex_2000_0100_0100_geemask_SimpleMask: mask by specific class values in a classification
- ex_2000_0100_0200_geemask_ClassFractions: obtain frequencies of class values in a collection of classifications
- ex_2000_0100_0400_geemask_ConvMask: mask by convoluting class values in a classification
- ex_2000_0100_0500_geemask_StaticsMask: mask by applying threshold on frequencies of class values in a collection of classifications


