import skymakercam.misc.lvmguiding as lvmguiding
import numpy as np
import os
import matplotlib.pyplot as plt
import time
from astropy.coordinates import SkyCoord
from importlib import reload
from matplotlib.colors import LogNorm
from matplotlib.patches import Ellipse
from matplotlib import use as plt_use
from matplotlib import rcParams

import sep

standard_instrument = lvmguiding.InstrumentParameters()

def rebin(arr, bin):
    new_shape=[int(arr.shape[0]/bin), int(arr.shape[1]/bin)]
    shape = (new_shape[0], arr.shape[0] // new_shape[0],
             new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).sum(-1).sum(1)

cmap='gist_heat'
plot = None

def plot_stars(data):
    ax = plot.get_figure().gca()
    while len(ax.artists):
        for a in ax.artists:
            a.remove()
    
    bkg = sep.Background(data)
    data_sub = data - bkg
    objects = sep.extract(data_sub, 1.5, err=bkg.globalrms)
    # plot an ellipse for each object
    for i in range(len(objects)):
        e = Ellipse(xy=(objects['x'][i], objects['y'][i]),
                    width=6*objects['a'][i],
                    height=6*objects['b'][i],
                    angle=objects['theta'][i] * 180. / np.pi)
        e.set_facecolor('none')
        e.set_edgecolor('yellow')
        ax.add_artist(e)
    

def plot_data(data):
    global plot
    m, s = np.mean(data), np.std(data)
    lp, up = np.percentile(data, 0.5), np.percentile(data,99.8)
    
    if plot:
        plot.set_data(data)
#        plot.set_clim(lp, up)
        plot.set_clim(m-s, m+s)
    else:    
        rcParams['figure.figsize'] = [13., 8.]
        plt_use('Qt5Agg')
        # plt_use('TkAgg')
        plt.ion()
        plt.tight_layout()
#        plt.title('skymaker cam', fontweight ="bold")
        plt.show()
        plot = plt.imshow(data, interpolation='nearest', cmap=cmap, vmin=m-s, vmax=m+s, origin='lower')
        plt.colorbar(orientation='vertical')

ra0  =  (13+26./60+47.24/3600)*15   #13:26:47.24
dec0 = -(47+28./60+46.45/3600)  #−47:28:46.
pa=0
c = SkyCoord(ra=ra0,dec=dec0,unit="deg")

ras1, decs1, dd_x_mm1, dd_y_mm1, chip_xxs1, chip_yys1,mags1, recycled_cat = \
  lvmguiding.find_guide_stars(c, pa=pa, plotflag=False, remote_catalog=True, inst=standard_instrument,)

data = lvmguiding.make_synthetic_image(chip_x=chip_xxs1,
                                            chip_y=chip_yys1,
                                            gmag=mags1,
                                            inst=standard_instrument,
                                            exp_time=5,
                                            seeing_arcsec=3.5,
                                            sky_flux=15,
                                            defocus=None)


plot_data(data)
plot_stars(data)
