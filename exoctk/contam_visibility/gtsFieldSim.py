# T. Greene 04 April 2017 tom.greene@nasa.gov; copied Simbad.query & Irsa.query from J Fraine

%matplotlib inline
#import matplotlib
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import math as math

from astroquery.irsa import Irsa
from astroquery.simbad import Simbad
import astropy.units as u

from tqdm import tqdm

D2R = math.pi / 180.0

def gtsFieldSim(ra, dec):

    # Input targetNamename and V3PA here
    targetName= "KELT-8"
    # PA     = 7  #position angle of field rel. to V3 for given observation date / visibility


    fontsize = 30

    # PA     = 50+90  #position angle of field re. to V3 for given observation date / visibility
    minPA  = 0
    xmax1PA  = 360
    spacePA= 1
    nPA    = (xmax1PA - minPA) // spacePA + 2

    setPA  = np.arange(minPA-spacePA, xmax1PA + spacePA, spacePA)

    dmag_limit = 7.5 # delta K mag limit for source consideration

    nWaves        = 2048

    y_gs= np.arange(-2048,2048)
    x_gs= np.arange(-2048,2048)

    # Get coordinates from SIMBAD and then find nearby 2MASS point sources

    target_Info  = Simbad.query_object(targetName)
    target_Data  = Irsa.query_region(targetName, catalog="fp_psc", spatial='Box', width=1 * u.arcsec)

    target_RA  = target_Info['RA'][0].split()
    target_DEC = target_Info['DEC'][0].split()

    RAd0  = (float(target_RA[0]) + float(target_RA[1])/60. + float(target_RA[2])/3600.)*15
    Decd0 = math.fabs(float(target_DEC[0])) + math.fabs(float(target_DEC[1])/60.) + math.fabs(float(target_DEC[2])/3600.)

    if (float(target_DEC[0]) < 0 or float(target_DEC[1]) < 0 or float(target_DEC[2]) < 0):
        Decd0 = -1.0 * Decd0

    K0     = np.sort(target_Data['k_m'])[0]#5.6 #K mag of host star

    sources = Irsa.query_region(targetName, catalog="fp_psc", spatial='Box', width=4 * u.arcmin)
    nsources = len(sources)

    # Set up arrays for x offset, yoffset, mag difference, plot size, and spectral collision
    # dx = np.zeros(nsources)
    # dy = np.zeros(nsources)
    # dmag = np.zeros(nsources)
    # msize = np.zeros(nsources)
    # col = np.zeros(nsources)

    print(target_RA , target_DEC, RAd0, Decd0)

    dmag_limit = 7.5 # delta K mag limit for source contamination consideration

def gaussian1D(center, width, height = None, offset = None):
    """
        Written by Nate Lust
        Edited  by Jonathan Fraine

        Returns a 1D gaussian function with the given parameters

        center  = center of gaussian profile

        width   = width  of gaussian profile

        height  = height of gaussian profile
                    -- defaults to `1 / np.sqrt(2.*pi*sigma**2.)`

        offset  = background, lower limit value for gaussian
                    -- defaults to 0.0
    """

    if height == None:
        height  = np.sqrt(2.*np.pi*width**2.)
        height  = 1.0/height

    if offset == None:
        offset = 0.0

    width   = float(width)

    return lambda x: height*np.exp(-(((center - x)/width)**2)/2) + offset

def gaussian2D(center_y, center_x, width_y, width_x = None, height = None, offset = None):
    """
        Written by Nate Lust
        Edited  by Jonathan Fraine

        Returns a 2D gaussian function with the given parameters

        center_y, center_x  = center position of 2D gaussian profile

        width_y , width_x   = widths of 2D gaussian profile (if width_y != width_x, then gaussian crossection = ellipse)

        height  = height of gaussian profile
                    -- defaults to `1 / np.sqrt(2.*pi*sigma**2.)`

        offset  = background, lower limit value for gaussian
                    -- defaults to 0.0
    """

    if width_x == None:
        width_x = width_y

    if height == None:
        height = np.sqrt(2*np.pi*(width_x**2 + width_y**2))
        height = 1./height

    if offset == None:
        offset = 0.0

    width_x = float(width_x)
    width_y = float(width_y)

    return lambda y,x: height*np.exp(-(((center_x-x)/width_x)**2 + ( (center_y-y)/width_y)**2)/2)+offset

def conv1D(arr1, arr2):
    '''
        Convolve 2 arrays together
            -- used by `smooth_gaussconv`
    '''
    fft1    = np.fft.fft(arr1)
    fft2    = np.fft.fft(arr2)

    conv    = np.fft.ifft(fft1*fft2)

    return np.real(np.fft.fftshift(conv))

def conv2D(arr1, arr2):
    '''
        Convolve 2 arrays together
            -- used by `smooth_gaussconv`
    '''
    fft1    = np.fft.fft2(arr1)
    fft2    = np.fft.fft2(arr2)

    conv    = np.fft.ifft2(fft1*fft2)

    return np.real(np.fft.fftshift(conv))

def smooth_gaussconv(arr, sigma):
    '''
        Gaussian smooths `arr` over a width of `sigma`
            -- uses `conv1D` and `conv2D`, which both use np.fft
    '''
    if len(arr.shape) == 1:
        gs1D    = gaussian1D(arr.size/2, sigma)(np.arange(arr.size))
        return conv1D(gs1D, arr) / gs1D.sum()

    if len(arr.shape) == 2:
        gs2D    = gaussian2D(arr.shape[0]/2., arr.shape[1]/2., sigma)(*np.indices(arr.shape))
        return conv2D(gs2D, arr) / gs2D.sum()

dra   = sources['ra'][(sources['k_m'] - K0) < dmag_limit] - RAd0
ddec  = sources['dec'][(sources['k_m'] - K0) < dmag_limit] - Decd0
dmag  = sources['k_m'][(sources['k_m'] - K0) < dmag_limit] - K0
msize = 10**(-0.1*dmag)*15
nlimit= sum((sources['k_m'] - K0) < dmag_limit)
col   = np.zeros(nlimit) # No spectral collision by default

#LWA R Field Point positions
X_F322W2 = 479 # X Field point (undeviated); old val 514
X_F444W = 1161 # X Field point undeviated); old val 1081
X_buff = 10 # Keep other spectra this far away from xmin1 and xxmax1 (dist from edge)
Y_field = 32  # Y Field point for locating object
Y_buff = 1.0 # Keep other spectra this far away from Y_field (dist from center)

# sweet spot ^

xmaxWL_F322W2 = 4.013 # xmax1 wavelength of F322W2 in microns per https://jwst-docs.stsci.edu/display/JTI/NIRCam+Filters
MINWL_F444W = 3.880 #minimum wavelength of F444W in microns per https://jwst-docs.stsci.edu/display/JTI/NIRCam+Filters

wavelen_undev = 3.97
disp = -0.001 #microns / pxl
dx_F444W = 1106 # length of F444W spectrum in pixels
dx_F322W2m1 = 1583 # length of F322W2 m=1 spectrum in pixels
dx_F322W2m2 = math.fabs((xmaxWL_F322W2 - 2.4) * 2.0 / disp) # length of F322W2 m=2 spectrum in pixels

xmin1_F322W2m1 = (xmaxWL_F322W2 - wavelen_undev)/disp + X_F322W2
xmax_F322W2 = xmin1_F322W2m1 + dx_F322W2m1
xmin1_F322W2m2 = (xmaxWL_F322W2*2.0 - wavelen_undev)/disp + X_F322W2
xmax_F322W2m2 = xmin1_F322W2m2 + dx_F322W2m2
# print(xmin1_F322W2m2, xmax_F322W2m2, dx_F322W2m2

xxmax1_F444W = (MINWL_F444W -  wavelen_undev)/disp + X_F444W
xmin1_F444W = xxmax1_F444W - dx_F444W
# print(xmin1_F322W2m1, xmax_F322W2, xmin1_F444W, xxmax1_F444W

# LWA field extremes for pickoff mirror POM
xmin1_xmax1y = -142
xmin1_miny = -132
xxmax1_miny = 2254
xxmax1_xmax1y = 2198

yxmax1_minx = 2822
ymin_minx = -174
ymin_xmax1x = -180
yxmax1_xmax1x = 2800

nyquistWidth = 2. / 2.3548
# contaminationF322W2 = np.zeros((nPA, nWaves))

normalHeight   = 1/np.sqrt(2*np.pi*nyquistWidth*nyquistWidth)
targetGaussian = gaussian1D(center=Y_field, width=nyquistWidth, height=normalHeight, offset=0)(y_gs+Y_field)

xbox = [-0, -0, 4040, 4040, -0]
ybox = [-0, 4040, 4040, -0, -0]
