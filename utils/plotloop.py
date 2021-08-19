# -*- coding: utf-8 -*-
#
# @Author: Florian Briegel (briegel@mpia.de)
# @Date: 2021-08-18
# @Filename: __main__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


import argparse
import os
import sys
import logging
import time

import numpy as np

from astropy.coordinates import SkyCoord
from importlib import reload

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Ellipse
from matplotlib import use as plt_use
from matplotlib import rcParams

import sep

from skymakercam.camera import SkymakerCameraSystem, SkymakerCamera, asyncio
import matplotlib.cbook
import warnings
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)



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
    return objects


def plot_data(data):
    global plot
    global m, s, lp, up
    
    if plot:
        plot.set_data(data)
#        plot.set_clim(lp, up)
        plot.set_clim(m-s, m+s)
        
    else:    
        rcParams['figure.figsize'] = [13., 8.]
        #plt_use('Qt5Agg') # steels the focus
        plt_use('TkAgg')
        plt.ion()
        plt.tight_layout()
        m, s = np.mean(data), np.std(data)
        lp, up = np.percentile(data, 0.5), np.percentile(data,99.8)

        plt.title('skymaker cam', fontweight ="bold")
#        plot = plt.imshow(data, interpolation='nearest', cmap=cmap, vmin=m-s, vmax=m+s, origin='lower')
        plot = plt.imshow(data, interpolation='nearest', cmap=cmap, vmin=lp, vmax=up, origin='lower')
        plt.colorbar(orientation='vertical')
        
        
async def plotloop(exptim, name, verb=False, config="../etc/cameras.yaml"):

    cs = SkymakerCameraSystem(SkymakerCamera, camera_config=config, verbose=verb)
    cam = await cs.add_camera(name=name, uid=cs._config[name]["uid"])

    if verb:
        cs.logger.log(logging.DEBUG, f"config {cs.list_available_cameras()}")

    exp = await cam.expose(exptim, "LAB TEST")
    #cs.logger.log(logging.DEBUG, f"config {str(exp.data)}")
    plot_data(exp.data)
    objects = plot_stars(exp.data)
    cs.logger.log(logging.DEBUG, f"Found Objects: {len(objects)}")
    cs.logger.log(logging.DEBUG, f"Found Objects: {objects[:7]}")
  
    while(True):
       exp = await cam.expose(exptim, "LAB TEST")
       # cs.logger.log(logging.DEBUG, f"config {str(exp.data)}")
       plot_data(exp.data)
       plt.pause(0.5)
#       await asyncio.sleep(0.4) 


def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", '--exptime', type=float, default=5.0,
                        help="Expose for for exptime seconds")

    parser.add_argument("-v", '--verbose', action='store_true',
                        help="print some notes to stdout")

    # Name of an optional YAML file
    parser.add_argument("-c", '--cfg', default="python/skymakercam/etc/cameras.yaml",
                        help="YAML file of lvmt cameras")

    # the last argument is mandatory: must be the name of exactly one camera
    # as used in the configuration file
    parser.add_argument('camname', default="sci.agw")

    args = parser.parse_args()

    asyncio.run(plotloop(args.exptime, args.camname, verb=args.verbose, config=args.cfg))
    
            
if __name__ == '__main__':

    #da = DataAnalysis()
    main()
