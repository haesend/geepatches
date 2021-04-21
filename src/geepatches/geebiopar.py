"""
--------------------------------------------------------------------------------------------------------
This library aims to provide Sentinel-2 biophysical parameter retrievals through GEE, based on the 
S2ToolBox methodology.
For algorithm details, see the original ATBD: https://step.esa.int/docs/extra/ATBD_S2ToolBox_L2B_V1.1.pdf

Currently, only FAPAR has been ported to GEE. fCOVER and LAI can be done as well.
Input should always be Sentinel-2 L2A products. 

This is a lot of neural network parameters, and there has been --no-- thorough validation of this code.
Please use at your own risk and provide feedback to:

kristofvantricht@gmail.com

--------------------------------------------------------------------------------------------------------
"""
import math
import ee
if not ee.data._credentials: ee.Initialize()

#------------------
# GENERAL FUNCTIONS
#------------------

def descale(scaled, scalefactor):
    return ee.Image(scaled.multiply(scalefactor).copyProperties(scaled))

def normalize(unnormalized, minval, maxval):
    return (ee.Image(2)
            .multiply(unnormalized.subtract(ee.Image(minval)))
            .divide(ee.Image(maxval).subtract(ee.Image(minval)))
            .subtract(ee.Image(1))
          .copyProperties(unnormalized))

def denormalize(normalized, minval, maxval):
    return (ee.Image(0.5)
            .multiply(normalized.add(ee.Image(1)))
            .multiply(ee.Image(maxval).subtract(ee.Image(minval)))
            .add(ee.Image(minval)))

def tansig(inputimg):
    return (ee.Image(2)
            .divide(ee.Image(1).add((ee.Image(-2).multiply(inputimg)).exp()))
            .subtract(ee.Image(1))
            .copyProperties(inputimg))

degToRad = ee.Image(math.pi / 180)

#---------------------
# FAPAR 3 BAND
#---------------------
def get_s2fapar3band(img):
    img = descale(img, 0.0001)
    b03_norm = normalize(img.select('B3'), 0, 0.243425768)
    b04_norm = normalize(img.select('B4'), 0, 0.297684236)
    b08_norm = normalize(img.select('B8'), 0.026530282, 0.78139164)
    
    viewZen_norm = normalize(ee.Image(img.getNumber('MEAN_INCIDENCE_ZENITH_ANGLE_B8')).multiply(degToRad).cos(), 0.918595401, 1)
    sunZen_norm  = normalize(ee.Image(img.getNumber('MEAN_SOLAR_ZENITH_ANGLE')).multiply(degToRad).cos(), 0.342022871, 0.936206429)
    relAzim_norm = (ee.Image(img.getNumber('MEAN_SOLAR_AZIMUTH_ANGLE')).subtract(ee.Image(img.getNumber('MEAN_INCIDENCE_AZIMUTH_ANGLE_B8'))).multiply(degToRad)).cos()

    n1 = neuron1_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm)
    n2 = neuron2_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm)
    n3 = neuron3_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm)
    n4 = neuron4_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm)
    n5 = neuron5_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm)
    
    l2 = layer2_fapar3(n1, n2, n3, n4, n5)
    
    fapar = denormalize(l2, 0.000153013, 0.977135097)
    return fapar


def neuron1_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm):
    sumimg = (
        ee.Image(-0.019802303)
        .add(ee.Image(1.063928519).multiply(b03_norm))
        .add(ee.Image(0.910752392).multiply(b04_norm))
        .subtract(ee.Image(0.973014301).multiply(b08_norm))
        .subtract(ee.Image(1.26727725).multiply(viewZen_norm))
        .add(ee.Image(0.239696855).multiply(sunZen_norm))
        .subtract(ee.Image(0.837005031).multiply(relAzim_norm)))

    return tansig(sumimg);


def neuron2_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm):
    sumimg = (
        ee.Image(2.917991233)
        .subtract(ee.Image(1.087124712).multiply(b03_norm))
        .add(ee.Image(2.869208297).multiply(b04_norm))
        .add(ee.Image(0.961199343).multiply(b08_norm))
        .add(ee.Image(0.055681494).multiply(viewZen_norm))
        .subtract(ee.Image(0.267414425).multiply(sunZen_norm))
        .subtract(ee.Image(0.066394844).multiply(relAzim_norm)))

    return tansig(sumimg)


def neuron3_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm):
    sumimg = (
        ee.Image(- 1.3349831)
        .subtract(ee.Image(0.732287638).multiply(b03_norm))
        .add(ee.Image(0.836483005).multiply(b04_norm))
        .subtract(ee.Image(2.273506421).multiply(b08_norm))
        .add(ee.Image(0.00640356).multiply(viewZen_norm))
        .subtract(ee.Image(0.17567951).multiply(sunZen_norm))
        .subtract(ee.Image(0.022244354).multiply(relAzim_norm)))

    return tansig(sumimg)


def neuron4_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm):
    sumimg = (
        ee.Image(- 1.38915446)
        .subtract(ee.Image(0.627414923).multiply(b03_norm))
        .add(ee.Image(1.227193715).multiply(b04_norm))
        .subtract(ee.Image(2.532473181).multiply(b08_norm))
        .subtract(ee.Image(0.025617074).multiply(viewZen_norm))
        .subtract(ee.Image(0.125296835).multiply(sunZen_norm))
        .subtract(ee.Image(0.010849463).multiply(relAzim_norm)))

    return tansig(sumimg);


def neuron5_fapar3(b03_norm,b04_norm,b08_norm,viewZen_norm,sunZen_norm,relAzim_norm):
    sumimg = (
        ee.Image(0.917074723)
        .add(ee.Image(0.376619209).multiply(b03_norm))
        .add(ee.Image(1.886599724).multiply(b04_norm))
        .subtract(ee.Image(1.841536547).multiply(b08_norm))
        .subtract(ee.Image(0.048726519).multiply(viewZen_norm))
        .add(ee.Image(0.107025026).multiply(sunZen_norm))
        .add(ee.Image(0.005804985).multiply(relAzim_norm)))

    return tansig(sumimg)


def layer2_fapar3(neuron1_fapar3, neuron2_fapar3, neuron3_fapar3, neuron4_fapar3, neuron5_fapar3):
    sumimg = (
        ee.Image(-0.446230574)
        .add(ee.Image(0.039475758).multiply(neuron1_fapar3))
        .add(ee.Image(0.32828457).multiply(neuron2_fapar3))
        .add(ee.Image(1.149270061).multiply(neuron3_fapar3))
        .subtract(ee.Image(1.610722043).multiply(neuron4_fapar3))
        .subtract(ee.Image(0.733977148).multiply(neuron5_fapar3)))

    return sumimg;



