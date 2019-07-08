from __future__ import division, print_function
import os
import sys
import json
import logging
import pathlib


import lib.autocryst.src.saveDozor as sd
from lib.autocryst.src.crystfel_utils import Utils

from tasks.AbstractTask import AbstractTask
'''
from tasks.H5ToCBFTask import H5ToCBFTask
from tasks.ReadImageHeader import ReadImageHeader
from tasks.ISPyBTasks import ISPyBRetrieveDataCollection

from utils import UtilsPath
from utils import UtilsImage
from utils import UtilsConfig
'''

__author__ = ['S. Basu']
__license__ = 'MIT'
__date__ = '05/07/2019'

logger = logging.getLogger('autoCryst')


class ExeCrystFEL(AbstractTask):

    def run(self, inData):
        dd = sd.Dozor(inData)
        spot_path = pathlib.Path(dd.jshandle['spotFile'])
        if spot_path.exists():
            parents = spot_path.parents
            dd.jshandle['dozorfolder'] = parents[0]
        else:
            pass
        if dd.jshandle['dozorfolder'].is_dir():
            dd.prep_spot()
        if dd.success:
            with open('header.json', 'w') as jhead:
                json.dump(dd.cbfheader, jhead, sort_keys=True, indent=2)
            if dd.stacklength <= 100:
                dd.create_stack()
            else:
                dd.mp_stack()
            try:
                args = dict()
                args['peak_search'] = 'cxi'
                args['peak_info'] = '/data/peakinfo'
                args['highres'] = '4.0'
                cwd = os.getcwd()
                cryst = Utils(cwd, 'dozor_*', 'cxi', **args)
                cryst.run_indexing()
                cryst.check_oarstat()
                cryst.report_stats()
                # status, results = crystfel_utils.__run__(cwd, 'dozor_2', 'cxi', **args)
                if cryst.status:
                    logger.info("MeshScan-results:{}".format(cryst.results))
                else:
                    logger.info("Error:{}".format("crystfel pipeline has errors"))
                    cryst.status = False
            except Exception as err:
                logger.info("Error-crystfel:{}".format(err))
                dd.success = False

        else:
            logger.info("Dozor did not run properly")
            dd.success = False
        return
