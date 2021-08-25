# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: __main__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)



import numpy as np

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Ellipse, Rectangle
from matplotlib import use as plt_use

from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.ndimage.filters import gaussian_filter, gaussian_gradient_magnitude
import scipy.ndimage
import sep


from sdsstools.logger import get_logger

class PlotIt:
    def __init__(self, data, rectw=60, logger=get_logger("plotit")):
        self.data = data
        self.rectw = rectw
        self.log = logger
        
        plt_use('TkAgg')
        
        self.fig = plt.figure(figsize=(16, 9))
        self.fig.tight_layout()
        
        self.ax_img = plt.subplot2grid((3,4), (0 ,1), rowspan=3, colspan=3)
        divider = make_axes_locatable(self.ax_img)
        cax_r = divider.append_axes('right', size='5%', pad=0.05)
        
        self.mean, self.sigma = np.mean(data), np.std(data)
        self.lperc, self.uperc = np.percentile(data, 0.5), np.percentile(data, 99.8)
        
        self.pl_img = self.ax_img.imshow(data, interpolation='nearest', vmin=self.mean-self.sigma, vmax=self.mean+self.sigma, origin='lower')
        self.ax_img.set_title('skymaker cam', fontweight ="bold")
        self.fig.colorbar(self.pl_img, cax=cax_r, orientation='vertical')
        
        self.pl_ax = [plt.subplot2grid((3,4), (0,0)),
                      plt.subplot2grid((3,4), (1,0)),
                      plt.subplot2grid((3,4), (2,0))]

        self.pl_xs, self.pl_ys = [None] * len(self.pl_ax), [None] * len(self.pl_ax)

        self.sep_objects()
        self.plot_objects()
        self.plot_star_cuts(update=False)
        
        plt.pause(.5)

    def sep_objects(self):
        bkg = sep.Background(self.data)
        data_sub = self.data - bkg
        self.objects = sep.extract(data_sub, 1.5, err=bkg.globalrms)
        self.object_index_sorted_by_peak=list({k: v for k, v in sorted({idx: self.objects['peak'][idx] for idx in range(len(self.objects))}.items(), key=lambda item: item[1], reverse=True)}.keys())

    def plot_objects(self):
        while len(self.ax_img.artists):
            for a in self.ax_img.artists:
                a.remove()

        for i in range(len(self.objects)):
            e = Ellipse(xy=(self.objects['x'][i], self.objects['y'][i]),
                        width=6*self.objects['a'][i],
                        height=6*self.objects['b'][i],
                        angle=self.objects['theta'][i] * 180. / np.pi)
            e.set_facecolor('none')
            e.set_edgecolor('red')
            self.ax_img.add_artist(e)

    def plot_star_cuts(self, update=True):
        self.pl_objects = [self.object_index_sorted_by_peak[0], 
                           self.object_index_sorted_by_peak[round(len(self.object_index_sorted_by_peak)/2)], 
                           self.object_index_sorted_by_peak[-1]]
        
        
        i = 0
        for idx in self.pl_objects:
            xc, yc, p = round(self.objects['x'][idx]), round(self.objects['y'][idx]), self.objects['peak'][idx]
            
            x0, y0 = xc - self.rectw/2, yc - self.rectw/2
            x1, y1 = xc + self.rectw/2, yc + self.rectw/2
            t = np.arange(-self.rectw/2, +self.rectw/2)

            xx, yx = np.linspace(x0, x1, self.rectw), np.linspace(yc, yc, self.rectw)
            xy, yy = np.linspace(xc, xc, self.rectw), np.linspace(y0, y1, self.rectw)
            
            if not update:
                #print(f"object {idx}: xy = [{xc}, {yc}]: {p}")
                r = Rectangle(xy=(xc-self.rectw/2, yc-self.rectw/2), width=self.rectw, height=self.rectw)
                r.set_facecolor('none')
                r.set_edgecolor('blue')
                self.ax_img.add_artist(r)
                
                self.pl_xs[i] = scipy.ndimage.map_coordinates(self.data, np.vstack((yx,xx)))
                self.pl_ys[i] = scipy.ndimage.map_coordinates(self.data, np.vstack((yy,xy)))
                self.pl_ax[i].plot(t, self.pl_xs[i], t, self.pl_ys[i])
            else:
                self.pl_ax[i].clear()
                xi = scipy.ndimage.map_coordinates(self.data, np.vstack((yx,xx)))
                yi = scipy.ndimage.map_coordinates(self.data, np.vstack((yy,xy)))
                self.pl_ax[i].plot(t, self.pl_xs[i], t, self.pl_ys[i], dashes=[4, 2])
                self.pl_ax[i].plot(t, xi, t, yi, linewidth=2)

            self.pl_ax[i].grid(True)
            i+=1
        


    def update(self, data, new_objects=False):
        self.data = data
        
        self.pl_img.set_data(data)
        if(new_objects):
            self.sep_objects()
            self.plot_objects()
            self.plot_star_cuts(False)
        else:
            self.plot_star_cuts()
            
        plt.pause(.5)

