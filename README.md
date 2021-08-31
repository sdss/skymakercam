# skymakercam

![Versions](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/sdss-skymakercam/badge/?version=latest)](https://sdss-skymakercam.readthedocs.io/en/latest/?badge=latest)
[![Travis (.org)](https://img.shields.io/travis/wasndas/skymakercam)](https://travis-ci.org/wasndas/skymakercam)
[![codecov](https://codecov.io/gh/wasndas/skymakercam/branch/main/graph/badge.svg)](https://codecov.io/gh/wasndas/skymakercam)

Skymaker camera based on sdss-basecam

    # from [lvmtan](https://github.com/sdss/lvmtan) run:
    poetry run container_start --name lvm.all
    # from [lvmpwi](https://github.com/sdss/lvmpwi) run:
    poetry run container_start --name=lvm.sci.pwi --simulator
    # from skymakercam run:
    poetry run python utils/plot_skymakercam.py -v -c python/skymakercam/etc/cameras.yaml lvm.sci.agw.cam


