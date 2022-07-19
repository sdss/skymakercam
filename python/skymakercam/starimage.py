#Library imports
import numpy as np
import matplotlib.pyplot as plt
import time
#from astropy.io import fits
#from astropy.table import Table,vstack
from astropy.coordinates import SkyCoord  # High-level coordinates
#from astropy.coordinates import ICRS, Galactic, FK4, FK5  # Low-level frames
#from astropy.coordinates import Angle, Latitude, Longitude  # Angles
#import astropy.units as u
#from astroquery.gaia import Gaia
#from scipy.ndimage import gaussian_filter, gaussian_gradient_magnitude
#from scipy import optimize
#import healpy as hp
#from astropy.table import Table, hstack, vstack
from skymakercam.coords import *



class Guidestars:
    def __init__(self, ras, decs, dd_x_mm, dd_y_mm, chip_xxs, chip_yys, mags, cats2):
        self.ras = ras
        self.decs = decs
        self.dd_x_mm =dd_x_mm
        self.dd_y_mm =dd_y_mm
        self.chip_xxs = chip_xxs
        self.chip_yys = chip_yys
        self.mags = mags
        self.cats2 = cats2


def find_guide_stars(c, pa, inst, remote_catalog=False, east_is_right=True, cull_cat=True, recycled_cat = None, return_focal_plane_coords=False, remote_maglim=None):
    # function to figure out which (suitable) guide stars are on the guider chip
    # input:
    # c in SkyCoord;          contains ra & dec of IFU field center
    # pa in degrees;          position angle (east of north) for the guider 
    # remote_catalog = True;  queries the GAIA TAP to obtain a catalog on the fly
    # east_is_right = True;   accounts for the handedness fip resulting from the 5 mirror configuration
    #                         should be set to FALSE for the spectrophotometric telescope, which has only 2 mirrors
    #
    # returns: ra,dec, G-band magnitude of all stars on the chip, as well as xy pixel positions (in mm)
                        #note! this does not account for the 6th mirror, which flips the handedness

    inner_search_radius=inst.inner_search_radius
    outer_search_radius=inst.outer_search_radius
    global cat 
    
    #make sure c is in icrs
    c_icrs=c.transform_to('icrs')   
    
    #if not using a local 4GB copy of the catalog, download the appropriate sub-set of gaia data
    if recycled_cat is not None:
        cat = recycled_cat
    else:
        if remote_catalog:
            if remote_maglim is None:
                remote_maglim = inst.mag_lim_lower
            radius = u.Quantity(outer_search_radius, u.deg)
            #j = Gaia.cone_search_async(coordinate=c_icrs, radius)
            gaia_query = "SELECT source_id, ra,dec,phot_g_mean_mag FROM gaiaedr3.gaia_source WHERE phot_g_mean_mag <= "+str(remote_maglim)+" AND 1=CONTAINS(POINT('ICRS',ra,dec), CIRCLE('ICRS',"+str(c_icrs.ra.deg)+","+str(c_icrs.dec.deg)+", "+str(radius.value)+"))"
            print("Gaia query: ",gaia_query)
            j = Gaia.launch_job_async(gaia_query)
            cat = j.get_results()
            #print("Gaia query: ",gaia_query)
            print(f'{len(cat)} stars found within {radius}')

        elif cull_cat:
            t0 = time.time()
            #print("Culling the catalog: ")
            cat_ra = cat_full[(c_icrs.ra.deg - 2/np.cos(c_icrs.dec.rad) < cat_full['ra'])& (cat_full['ra'] < c_icrs.ra.deg +2/np.cos(c_icrs.dec.rad))]
            #print(len(cat_ra)," of ",len(cat_full),"pass initial RA selection")
            cat = cat_ra[(c_icrs.dec.deg - 2 < cat_ra['dec'])& (cat_ra['dec'] < c_icrs.dec.deg +2)]
            #print(len(cat)," of ",len(cat_ra),"pass initial DEC selection")
            t1 = time.time()
            #print("Culling complete. It took me {:.1f} s".format(t1-t0))
        
    #print("Circular selection")
    t0 = time.time()
    dd=sphdist(c_icrs.ra.deg,c_icrs.dec.deg,cat['ra'],cat['dec'])

    #pick the subset that is within 1.5 degree
    #also check some magnitude range
    
    ii=(dd < outer_search_radius) & (dd > inner_search_radius)  & (cat['phot_g_mean_mag'] < inst.mag_lim_lower) & (cat['phot_g_mean_mag'] > inst.mag_lim_upper)
    cats2=cat[ii]
    t1 = time.time()
    #print("Circular selection complete. It took me {:.1f} s".format(t1-t0))
    #convert ra&dec of guide stars to xy position in relation to field center (in mm)
    
    #print("Scale conversion...")
    t0 = time.time()
    dd_x_mm,dd_y_mm=ad2xy(cats2,c_icrs,inst=inst)
    
    if east_is_right:
        dd_x_mm=-1.*dd_x_mm
        pa=-1.*pa
    t1 = time.time()
    #print("Scale conversion complete. It took me {:.1f} s".format(t1-t0))
    #show some star positions in focal plane units

    if return_focal_plane_coords:
        return dd_x_mm,dd_y_mm,cats2
    #identify which stars fall on the guider chip
    selection_on_chip,chip_xxs,chip_yys=in_box(dd_x_mm,dd_y_mm,pa,inst=inst)
    
    iii=np.equal(selection_on_chip,1)
    
    #overplot the identified guide stars positions

    selection_not_crowded = (selection_on_chip==True)
    if inst.min_neighbour_distance>0:
        ctr=0
        for cindex,cc in enumerate(cats2):
            if selection_on_chip[cindex]:
                #dd=cc.separation(cats2[iii])
                dd=sphdist(cc['ra'],cc['dec'],cats2['ra'],cats2['dec'])*3600. #in arcsec
                if np.any((dd > 0) & (dd < inst.min_neighbour_distance)):
                    selection_not_crowded[cindex]=False
                    ctr+=1
                    #print(cindex,"Sum of not crowded:",np.sum(selection_not_crowded))
        #print("Flags: ",np.sum(selection_not_crowded))
        #print(selection_on_chip.dtype,selection_not_crowded.dtype)
        iii=selection_on_chip & selection_not_crowded
        print("Removed {} stars due to crowding.".format(ctr))
    
    #print("After crowding check: ",np.sum(iii),len(iii))
    #overplot the final cleaned guide star positions
    #sub select the guide stars that fall on the guide chip, return their properties
    ras=cats2['ra'][iii]
    decs=cats2['dec'][iii]    
    mags=cats2['phot_g_mean_mag'][iii]
    #print("iii Selection: {} of {}".format(np.sum(iii),len(iii)))
    chip_xxs = chip_xxs[iii]
    chip_yys = chip_yys[iii]
    
    dd_x_mm = dd_x_mm[iii]
    dd_y_mm = dd_y_mm[iii]
        
    return Guidestars(ras, decs, dd_x_mm, dd_y_mm, chip_xxs, chip_yys, mags, cats2)
    

def find_guide_stars_auto(input_touple, inst, folder = "/guide_star_search_results_no_faint_limit", verbose=False, save_bin = True):
    #print(inst.mag_lim_lower)
    t0 = time.time()
    index = input_touple[0]
    c = input_touple[1]
    if verbose: 
        print("Analyzing pointing {} (ra: {} dec: {})\n".format(index+1,c.ra.deg,c.dec.deg))

    for pa in [0, 60, 120, 180, 240, 300]:
        if pa==0:
           culled_cat = get_cat_using_healpix2(c, inst=inst)
        ras,decs,dd_x_mm,dd_y_mm,chip_xxs,chip_yys,mags,culled_cat = \
           find_guide_stars(c, pa=pa, recycled_cat=culled_cat, inst=inst)    

        output = np.stack((ras, decs, dd_x_mm, dd_y_mm, chip_xxs, chip_yys, mags), axis=1)
        
        if save_bin:
            filename = inst.catalog_path + folder + "/guide_stars_{:06d}_pa_{:03d}.npy".format(index,pa)
            np.save(filename,output)
        else:
            filename = inst.catalog_path + folder + "/guide_stars_{:06d}_pa_{:03d}".format(index,pa)
            np.savetxt(filename,output,fmt="%10.6f")
        
    return index,len(ras), time.time() - t0


def make_synthetic_image(chip_x, chip_y, gmag, inst, exp_time=5, seeing_arcsec=3.5, sky_flux=10, defocus=0.0):
    
    seeing_pixel = seeing_arcsec * inst.image_scale / (inst.chip_size_mm[0] / inst.chip_size_pix[0] * 1000) / 2.36
    
    x_position = chip_x / inst.chip_size_mm[0] * inst.chip_size_pix[0]
    y_position = chip_y / inst.chip_size_mm[1] * inst.chip_size_pix[1]
    
    selection_on_chip = (0 < x_position) & (x_position < inst.chip_size_pix[0]) & (0 < y_position) & (y_position < inst.chip_size_pix[1])
    
    x_position = x_position[selection_on_chip]
    y_position = y_position[selection_on_chip]
    gmag = gmag[selection_on_chip]
    
    #print("{} of {} stars are on the chip.".format(np.sum(selection_on_chip),len(selection_on_chip)))
    
    #gaia_legend_mag = np.arange(17,4,mag_lim_index)
    #gaia_legend_flux= 10**(-(np.array(gaia_legend_mag)+zp)/2.5)
    
    gaia_flux = 10 ** (-(gmag + inst.zp) / 2.5)

    background = (sky_flux + inst.dark_current) * exp_time
    n_pix = 7*7


    signal = gaia_flux * exp_time
    noise = np.sqrt(inst.readout_noise ** 2 + signal + n_pix * background)

    star_image = np.zeros((inst.chip_size_pix[1],inst.chip_size_pix[0]))

    for index, current_flux in enumerate(gaia_flux):
        current_x = x_position[index]
        current_y = y_position[index]

        i = int(current_x)
        j = int(current_y)

        xx = current_x-i
        yy = current_y-j

        star_image[j,i] = (1 - xx) * (1 - yy) * current_flux * exp_time


        if i < inst.chip_size_pix[0] - 1:
            star_image[j,i+1] = (xx) * (1-yy) * current_flux * exp_time
        if j < inst.chip_size_pix[1] - 1:
            star_image[j+1,i] = (1 - xx) * (yy) * current_flux * exp_time
        if (i < inst.chip_size_pix[0] - 1) & (j < inst.chip_size_pix[1] - 1):
            star_image[j+1,i+1] = (xx) * (yy) * current_flux * exp_time

        #star_image[int(current_y),int(current_x)] = current_flux*exp_time

    star_image_c = gaussian_filter(star_image, sigma=seeing_pixel, mode="constant")
    if defocus != 0.0:
        star_image_c = gaussian_filter(star_image_c, sigma=defocus, mode='constant')
        #star_image_c = gaussian_gradient_magnitude(star_image, sigma=1+defocus/10000, mode='constant')

    star_image_c_noise = np.random.poisson(lam=star_image_c,size = star_image_c.shape)
    
    background_array = np.random.poisson(background,size=star_image.shape)

    readout_noise_array = np.random.normal(loc=0,scale = inst.readout_noise,size=star_image.shape)

    combined = star_image_c_noise + background_array + readout_noise_array + inst.bias

    return combined


