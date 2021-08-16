import numpy as np
import sep

from astropy.io import fits


import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Ellipse
from  matplotlib import use as plt_use

def rebin(arr, bin):
    new_shape=[int(arr.shape[0]/bin), int(arr.shape[1]/bin)]
    shape = (new_shape[0], arr.shape[0] // new_shape[0],
             new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).sum(-1).sum(1)

#plt_use('TkAgg')
plt_use('Qt5Agg')
plt.ion()
plt.show()
    
rcParams['figure.figsize'] = [10., 8.]
cmap='gist_heat'

hdu = fits.open("../20191010/sx.hws.pcam.20191010_00001.fits")

data = rebin(hdu[0].data[0], 4)

m, s = np.mean(data), np.std(data)
plot_data = plt.imshow(data, interpolation='nearest', cmap=cmap, vmin=m-s, vmax=m+s, origin='lower')
plot_cb = plt.colorbar(cmap=cmap, orientation='vertical')
plt.title('skymaker cam', fontweight ="bold")


bkg = sep.Background(data.byteswap().newbyteorder())

data_sub = data - bkg

m, s = np.mean(data_sub), np.std(data_sub)
lp, up = np.percentile(data_sub,0.5), np.percentile(data_sub,99.8)

plot_data.set_data(data_sub)
plot_data.set_clim(lp, up)

#ax = plt.gcf().gca()
ax = plot_data.get_figure().gca()

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

while len(ax.artists):
   for a in ax.artists:
       a.remove()
    
from scipy.ndimage.filters import gaussian_filter

data_blur = gaussian_filter(data_sub, sigma=70)

m, s = np.mean(data_blur), np.std(data_blur)
plot_data.set_clim(m-s, m+s)
plot_data.set_data(data_blur)


