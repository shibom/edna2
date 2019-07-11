from __future__ import division, print_function
import os
import sys
from datetime import datetime
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
        outData = {}

        dd = sd.Dozor(inData)
        dd.extract_olof_json(inData)
        headerfile = pathlib.Path(dd.workingDir) / 'header.json'
        if dd.success and not headerfile.exists():
            with open(headerfile, 'w') as jhead:
                json.dump(dd.cbfheader, jhead, sort_keys=True, indent=2)
        elif dd.success and headerfile.exists():
            if dd.stacklength <= 100:
                dd.create_stack()
            else:
                dd.mp_stack()
            try:
                cxipath = pathlib.Path(dd.workingDir)
                cxi_all = cxipath.glob('dozor*cxi')
                current = len(cxi_all) - 1
                prefix = 'dozor_%d' % current
                args = dict()
                args['peak_search'] = 'cxi'
                args['peak_info'] = '/data/peakinfo'
                args['highres'] = '4.0'
                cwd = dd.workingDir
                cryst = Utils(cwd, prefix, 'cxi', **args)
                cryst.find_files()
                cryst.crystfel_dir = cwd

                geomfile = cxipath.glob('*.geom')
                if len(geomfile) > 0:
                    cryst.geometry_file = geomfile[0]
                else:
                    kk = {'cxi': """dim0 = %\ndim1 = ss\ndim2 = fs\ndata = /data/data\n"""}
                    cryst.make_geomfile(**kk)

                if len(cryst.filelist) < 100 and os.path.isfile(cryst.geometry_file):
                    cryst.infile = os.path.join(os.getcwd(), 'input.lst')
                    outname = datetime.now().strftime('%H-%M-%S.stream')
                    cryst.outstream = str(cxipath / outname)
                    # shellfile = 'input.sh'

                    ofh = open(cryst.infile, 'w')
                    for fname in cryst.filelist:
                        ofh.write(fname)
                        ofh.write('\n')
                    ofh.close()

                    # Utils.run_script(cryst.indexamajig_cmd(), shellfile)
                    # Run as AbstractTask method
                    cmd = cryst.indexamajig_cmd()
                    self.setLogFileName('autocryst.log')
                    self.runCommandLine(cmd)
                if cryst.status and os.path.exists(cryst.outstream):
                    cryst.report_stats(cryst.outstream)
                    logger.info("MeshScan-results:{}".format(cryst.results))
                    outData = cryst.results

                else:
                    logger.info("Error:{}".format("crystfel pipeline has errors"))
                    cryst.status = False
                    self.setFailure()
            except Exception as err:
                logger.info("Error-crystfel:{}".format(err))
                dd.success = False
                self.setFailure()

        else:
            logger.info("something not correct with ImageQualityIndicator parsing")
            dd.success = False
        return outData
