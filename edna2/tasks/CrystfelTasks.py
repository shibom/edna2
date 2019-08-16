#
# Copyright (c) European Synchrotron Radiation Facility (ESRF)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from __future__ import division, print_function
import os
import sys
import json
import logging
import pathlib


import edna2.lib.autocryst.src.saveDozor as sd
from edna2.lib.autocryst.src import run_crystfel

from edna2.tasks.AbstractTask import AbstractTask
from edna2.utils import UtilsLogging
from edna2.utils import UtilsImage


__author__ = ['S. Basu']
__license__ = 'MIT'
__date__ = '05/07/2019'

logger = UtilsLogging.getLogger()


class ExeCrystFEL(AbstractTask):

    def getInDataSchema(self):
        return {
            "type": "object",
            "required": ["imageQualityIndicators", "detectorType"],
            "properties": {
                "detectorType": {"type": "string"},
                "listH5FilePath": {
                    "type": "array",
                    "items": {"type": "string"}
                    },
                "imageQualityIndicators": {
                    "type": "array",
                    "items": {
                        "$ref": self.getSchemaUrl("imageQualityIndicators.json")
                    }
                }
            }
        }

    def getOutDataSchema(self):
        return {
            "type": "object",
            "properties": {
                "centering": {"type": "string"},
                "num_indexed_frames": {"type": "integer"},
                "lattice": {"type": "string"},
                "unique_axis": {"type": "string"},
                "unit_cell": {
                    "type": "array",
                    "items": {"type": "number"},
                },
                "point_group": {"type": "string"},
                "space_group": {"type": "string"},
                "resolution_limit": {"type": "number"},
                "average_num_spots": {"type": "number"}
            }
        }

    def run(self, inData):
        outData = {}
        if inData['detectorType'] == 'eiger4m':
            os.chdir(self.getWorkingDirectory())
            outData = self.exeIndexing(inData)

        else:
            dd = sd.Dozor(inData)
            dd.extract_olof_json(inData)

            headerfile = self.getWorkingDirectory() / 'headers.json'
            if dd.is_success():
                os.chdir(str(self.getWorkingDirectory()))
                if not headerfile.exists():
                    with open(str(headerfile), 'w') as jhead:
                        json.dump(dd.cbfheader, jhead, sort_keys=True, indent=2)
                else:
                    pass

                if dd.stacklength <= 100:
                    dd.create_stack()
                else:
                    dd.mp_stack()

                outData = self.exeIndexing(inData)
            else:
                self.setFailure()
                logger.error('CrystFEL Task failed due to failure of dozor packing into cxi')
        return outData

    def exeIndexing(self, inData):
        in_for_crystfel = dict()
        in_for_crystfel['detectorType'] = inData['detectorType']
        in_for_crystfel['maxchunksize'] = 10
        if inData['detectorType'] == 'eiger4m':
            tmp = UtilsImage.getPrefix(inData['listH5FilePath'][0])
            in_for_crystfel['prefix'] = tmp.strip('data')
            in_for_crystfel['suffix'] = UtilsImage.getSuffix(inData['listH5FilePath'][0])
            in_for_crystfel['image_directory'] = str(pathlib.Path(inData['listH5FilePath'][0]).parent)

        else:
            cxi_all = list(self.getWorkingDirectory().glob('dozor*cxi'))
            current = len(cxi_all) - 1
            in_for_crystfel['image_directory'] = self.getWorkingDirectory()
            in_for_crystfel['prefix'] = 'dozor_%d.' % current
            in_for_crystfel['suffix'] = 'cxi'
            in_for_crystfel['peak_search'] = 'cxi'
            in_for_crystfel['peak_info'] = '/data/peakinfo'

        results = run_crystfel.__run__(in_for_crystfel)
        return results


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s%(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='autocryst.log',
                        filemode='a+')
    fh = open(sys.argv[1], 'r')
    inData = json.load(fh)
    fh.close()
    crystfel = ExeCrystFEL(inData)

    crystfel.executeRun()
    print(crystfel.outData)
