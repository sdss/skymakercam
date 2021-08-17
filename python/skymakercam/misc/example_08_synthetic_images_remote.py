import skymakercam.misc.lvmguiding as lvmguiding
import numpy as np
import os
import matplotlib.pyplot as plt
import time
from astropy.coordinates import SkyCoord
from importlib import reload
from matplotlib.colors import LogNorm

standard_instrument = lvmguiding.InstrumentParameters()

ra0  =  (13+26./60+47.24/3600)*15   #13:26:47.24
dec0 = -(47+28./60+46.45/3600)  #−47:28:46.
pa=0
c = SkyCoord(ra=ra0,dec=dec0,unit="deg")

ras1, decs1, dd_x_mm1, dd_y_mm1, chip_xxs1, chip_yys1,mags1, recycled_cat = \
  lvmguiding.find_guide_stars(c, pa=pa, plotflag=False, remote_catalog=True, inst=standard_instrument,)

my_image1 = lvmguiding.make_synthetic_image(chip_x=chip_xxs1,
                                            chip_y=chip_yys1,
                                            gmag=mags1,
                                            inst=standard_instrument,
                                            exp_time=5,
                                            seeing_arcsec=3.5,
                                            sky_flux=15)

fig,ax4 = plt.subplots(figsize=(13,8))

vmin4 = np.percentile(my_image1,25)
vmax4 = np.percentile(my_image1,99.5)


my_plot4 = ax4.imshow(my_image1,origin="lower",norm=LogNorm(vmin=np.max([vmin4,1]), vmax=vmax4))

plt.colorbar(my_plot4,ax=ax4,fraction=0.046, pad=0.04)
fig.tight_layout()
fig.show()

#fig.savefig("example_images/synthetic_image_{:03d}.png".format(counter),dpi=200,facecolor="w",edgecolor="w",bbox_inches="tight")
