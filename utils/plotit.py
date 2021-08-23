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

def rebin(arr, bin):
    new_shape=[int(arr.shape[0]/bin), int(arr.shape[1]/bin)]
    shape = (new_shape[0], arr.shape[0] // new_shape[0],
             new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).sum(-1).sum(1)


class PlotIt:
    def __init__(self, data, rectw=60, logger=get_logger("plotit")):
        self.log = logger
        
        self.rectw = rectw
        
        plt_use('TkAgg')
        
        self.fig = plt.figure(figsize=(16, 9))
        self.fig.tight_layout()
        
        self.ax_img = plt.subplot2grid((3,4), (0 ,1), rowspan=3, colspan=3)
        divider = make_axes_locatable(self.ax_img)
        cax_r = divider.append_axes('right', size='5%', pad=0.05)
        
        self.mean, self.sigma = np.mean(data), np.std(data)
        self.lperc, self.uperc = np.percentile(data, 0.5), np.percentile(data, 99.8)
        
#        self.pl_img = self.ax_img.imshow(data, interpolation='nearest', cmap='gray', vmin=self.mean-self.sigma, vmax=self.mean+self.sigma, origin='lower')
        self.pl_img = self.ax_img.imshow(data, interpolation='nearest', vmin=self.mean-self.sigma, vmax=self.mean+self.sigma, origin='lower')
        self.ax_img.set_title('skymaker cam', fontweight ="bold")
        self.fig.colorbar(self.pl_img, cax=cax_r, orientation='vertical')
        
        self.pl_ax = [plt.subplot2grid((3,4), (0,0)),
                      plt.subplot2grid((3,4), (1,0)),
                      plt.subplot2grid((3,4), (2,0))]
        
        bkg = sep.Background(data)
        data_sub = data - bkg
        self.objects = sep.extract(data_sub, 1.5, err=bkg.globalrms)
        self.object_index_sorted_by_peak=list({k: v for k, v in sorted({idx: self.objects['peak'][idx] for idx in range(len(self.objects))}.items(), key=lambda item: item[1], reverse=True)}.keys())
        
        for i in range(len(self.objects)):
            e = Ellipse(xy=(self.objects['x'][i], self.objects['y'][i]),
                        width=6*self.objects['a'][i],
                        height=6*self.objects['b'][i],
                        angle=self.objects['theta'][i] * 180. / np.pi)
            e.set_facecolor('none')
            e.set_edgecolor('red')
            self.ax_img.add_artist(e)
        
        self.pl_objects = [self.object_index_sorted_by_peak[0], 
                           self.object_index_sorted_by_peak[round(len(self.object_index_sorted_by_peak)/2)], 
                           self.object_index_sorted_by_peak[-1]]
        
        self.pl_xs, self.pl_ys = [None] * len(self.pl_objects), [None] * len(self.pl_objects)
        
        i = 0
        for idx in self.pl_objects:
            xc, yc, p = round(self.objects['x'][idx]), round(self.objects['y'][idx]), self.objects['peak'][idx]
            print(f"object {idx}: xy = [{xc}, {yc}]: {p}")
            
            r = Rectangle(xy=(xc-self.rectw/2, yc-self.rectw/2), width=self.rectw, height=self.rectw)
            r.set_facecolor('none')
            r.set_edgecolor('blue')
            self.ax_img.add_artist(r)
            x0, y0 = xc - self.rectw/2, yc - self.rectw/2
            x1, y1 = xc + self.rectw/2, yc + self.rectw/2
            
            x, y = np.linspace(x0, x1, self.rectw), np.linspace(yc, yc, self.rectw)
            self.pl_xs[i] = scipy.ndimage.map_coordinates(data, np.vstack((y,x)))
            
            x, y = np.linspace(xc, xc, self.rectw), np.linspace(y0, y1, self.rectw)
            self.pl_ys[i] = scipy.ndimage.map_coordinates(data, np.vstack((y,x)))
            
            t = np.arange(-self.rectw/2,+self.rectw/2)
            self.pl_ax[i].plot(t, self.pl_xs[i], t, self.pl_ys[i])
            i+=1
        
        plt.pause(.5)
    
    def update(self, data):
            self.pl_img.set_data(data)
            
            i = 0
            for idx in self.pl_objects:
                xc, yc, p = round(self.objects['x'][idx]), round(self.objects['y'][idx]), self.objects['peak'][idx]
                print(f"object {idx}: xy = [{xc}, {yc}]: {p}")
                
                x0, y0 = xc - self.rectw/2, yc - self.rectw/2
                x1, y1 = xc + self.rectw/2, yc + self.rectw/2
                
                x, y = np.linspace(x0, x1, self.rectw), np.linspace(yc, yc, self.rectw)
                xi = scipy.ndimage.map_coordinates(data, np.vstack((y,x)))
                
                x, y = np.linspace(xc, xc, self.rectw), np.linspace(y0, y1, self.rectw)
                yi = scipy.ndimage.map_coordinates(data, np.vstack((y,x)))
                
                self.pl_ax[i].clear()
                
                t = np.arange(-self.rectw/2,+self.rectw/2)
                self.pl_ax[i].grid(True)
                self.pl_ax[i].plot(t, self.pl_xs[i], t, self.pl_ys[i], dashes=[4, 2])
                self.pl_ax[i].plot(t, xi, t, yi, linewidth=2)
                i+=1
            
            plt.pause(.5)

