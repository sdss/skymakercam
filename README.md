# skymakercam

![Versions](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/sdss-skymakercam/badge/?version=latest)](https://sdss-skymakercam.readthedocs.io/en/latest/?badge=latest)
[![Travis (.org)](https://img.shields.io/travis/wasndas/skymakercam)](https://travis-ci.org/wasndas/skymakercam)
[![codecov](https://codecov.io/gh/wasndas/skymakercam/branch/main/graph/badge.svg)](https://codecov.io/gh/wasndas/skymakercam)

Skymaker camera based on sdss-basecam

## from [lvmtan](https://github.com/sdss/lvmtan) run:

    poetry run container_start --name lvm.all

## from [lvmpwi](https://github.com/sdss/lvmpwi) run:

    poetry run container_start --name=lvm.sci.pwi --simulator

## from skymakercam run:

    poetry run python utils/plot_skymakercam.py -v -c python/skymakercam/etc/cameras.yaml lvm.sci.agw.cam


## use your own python code:
With this [config example python/skymakercam/etc/cameras.yaml](https://github.com/wasndas/skymakercam/blob/master/python/skymakercam/etc/cameras.yaml) and the actors running from before it can be used like this:

    from logging import DEBUG, INFO
    from skymakercam.camera import SkymakerCameraSystem, SkymakerCamera

    async def example_skymakercam(camname, verb, config):
   
       cs = SkymakerCameraSystem(SkymakerCamera, camera_config=config, verbose=verb)
       cam = await cs.add_camera(name=camname, uid=cs._config[camname]["uid"])

       # eg: expose or do whatever u do with a sdss-basecam.
       exp = await cam.expose(exptime, camname)
       
   
    verb = DEBUG
    camname = "lvm.sci.agw.cam"
    config = "python/skymakercam/etc/cameras.yaml"

    asyncio.run(example_skymakercam(camname, verb, config))
    
