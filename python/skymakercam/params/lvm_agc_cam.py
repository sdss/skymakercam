import numpy as np
from skymakercam.params.lvm_common import *
from skymakercam.params.lvm_ifu_positions import *

image_scale = 8.92 * 2    # 1arcsec in microns from SDSS-V_0129_LVMi_PDR.pdf Table 7

chip_size_pix = [3200, 2200]


## the position of the guide chips in each telescope
ifu_pa = 90        #degrees, E of N

