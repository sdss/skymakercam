import numpy as np
import sep

from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Ellipse


rcParams['figure.figsize'] = [10., 8.]

hdu = fits.open("20191010/sx.hws.pcam.20191010_00001.fits")

data = hdu[0].data[0]

m, s = np.mean(data), np.std(data)
plt.imshow(data, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
plt.colorbar()
plt.title('matplotlib.pyplot.imshow() function Example', 
                                     fontweight ="bold")
plt.show(block=False)


bkg = sep.Background(data.byteswap().newbyteorder())

data_sub = data - bkg

m, s = np.mean(data_sub), np.std(data_sub)
plt.imshow(data_sub, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
plt.show(block=False)


lp, up = np.percentile(data_sub,5.0), np.percentile(data_sub,99.995)
plt.imshow(data_sub, interpolation='nearest', cmap='gray', vmin=lp, vmax=up, origin='lower')
plt.show(block=False)


# plot background-subtracted image
#fig, ax = plt.subplots()

objects = sep.extract(data_sub, 1.5, err=bkg.globalrms)

ax = plt.gcf().gca()
# plot an ellipse for each object
for i in range(len(objects)):
    e = Ellipse(xy=(objects['x'][i], objects['y'][i]),
                width=6*objects['a'][i],
                height=6*objects['b'][i],
                angle=objects['theta'][i] * 180. / np.pi)
    e.set_facecolor('none')
    e.set_edgecolor('red')
    ax.add_artist(e)

plt.show(block=False)  


from scipy.ndimage.filters import gaussian_filter

data_blur = gaussian_filter(data_sub, sigma=7)

m, s = np.mean(data_blur), np.std(data_blur)
plt.imshow(data_blur, interpolation='nearest', cmap='gray', vmin=m-s, vmax=m+s, origin='lower')
plt.show(block=False)
