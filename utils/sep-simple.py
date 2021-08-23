# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: sep-simple.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


from plotit import *


bin = 1
hdu = fits.open("../20191010/sx.hws.pcam.20191010_00001.fits")
data = rebin(hdu[0].data[0], bin)
data[data < 100] = 0
data--=100
pl = PlotIt(data)

for um in [10., 100.,200.,300.,400.,500.]:
#    defocus = math.sqrt(um/10)
    defocus = (um/100)**2
    print(defocus)
    data2=data
    data2 = gaussian_filter(data2, sigma=defocus, mode='constant')
    pl.update(data2)
    time.sleep(1)

