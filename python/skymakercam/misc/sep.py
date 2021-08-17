import numpy as np
import sep

from astropy.io import fits


import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Ellipse
from  matplotlib import use as plt_use
from scipy.ndimage.filters import gaussian_filter, gaussian_gradient_magnitude


def rebin(arr, bin):
    new_shape=[int(arr.shape[0]/bin), int(arr.shape[1]/bin)]
    shape = (new_shape[0], arr.shape[0] // new_shape[0],
             new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).sum(-1).sum(1)


cmap='gist_heat'
plot = None

def plot_data(data):
    global plot
    m, s = np.mean(data), np.std(data)
    lp, up = np.percentile(data, 0.5), np.percentile(data,99.8)
    
    if plot:
        plot.set_data(data)
#        plot.set_clim(lp, up)
        plot.set_clim(m-s, m+s)
    else:    
        rcParams['figure.figsize'] = [10., 8.]
        plt_use('Qt5Agg')
        # plt_use('TkAgg')
        plt.ion()
        plt.title('skymaker cam', fontweight ="bold")
        plt.show()
        plot = plt.imshow(data, interpolation='nearest', cmap=cmap, vmin=m-s, vmax=m+s, origin='lower')
        plt.colorbar(orientation='vertical')

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
    


hdu = fits.open("../20191010/sx.hws.pcam.20191010_00001.fits")
data = rebin(hdu[0].data[0], 4)
#data = hdu[0].data[0].byteswap().newbyteorder()
plot_data(data)
plot_stars(data)

#data_blur = gaussian_filter(data_sub, sigma=7)
#data_blur = gaussian_gradient_magnitude(data_sub,sigma=4)
data_blur = gaussian_gradient_magnitude(data_sub,sigma=0.5,mode='constant')
plot_data(data_blur)
plot_stars(data_blur)



data_blur = gaussian_gradient_magnitude(data_sub,sigma=1,mode='constant')
plot_data(data_blur)
plot_stars(data_blur)


data_blur = gaussian_gradient_magnitude(data_sub,sigma=3,mode='constant')
plot_data(data_blur)
plot_stars(data_blur)


#plt.axis([80,120,60,100])
#plt.axis([0,data.shape[0],0,data.shape[1]])

