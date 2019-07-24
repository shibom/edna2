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

__authors__ = ["O. Svensson"]
__license__ = "MIT"
__date__ = "21/04/2019"

import os, pathlib
import logging
import unittest
import json

from edna2.utils import UtilsTest
from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

from edna2.tasks.ImageQualityIndicatorsTask import ImageQualityIndicatorsTask

logger = UtilsLogging.getLogger()


class ImageQualityIndicatorsExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)
        # self.dataPath = pathlib.Path(os.getcwd()) / 'data'

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    def test_execute_listOfImages(self):
        referenceDataPath = self.dataPath / 'inData_pilatus6m_5images_list.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)
        outjsonpath = self.dataPath / 'outData_1.json'
        with open(str(outjsonpath), 'w') as jh:
            json.dump(outData, jh, sort_keys=True, indent=4)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    def test_execute_startEnd(self):
        referenceDataPath = self.dataPath / 'inData_pilatus6m_5images_start_end.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)
        outjsonpath = self.dataPath / 'outData_2.json'
        with open(str(outjsonpath), 'w') as jh:
            json.dump(outData, jh, sort_keys=True, indent=4)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    def test_execute_opid30a1(self):
        referenceDataPath = self.dataPath / 'inData_pilatus2m_20images.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)
        outjsonpath = self.dataPath / 'outData_2.json'
        with open(str(outjsonpath), 'w') as jh:
            json.dump(outData, jh, sort_keys=True, indent=4)


    '''
    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    @unittest.skipIf(not os.path.exists('/data/visitor/mx415/id30a2/20160315/' +
                                        'RAW_DATA/test3/mx415_1_0001.cbf'),
                     'Image /data/visitor/mx415/id30a2/20160315/RAW_DATA/' +
                     'test3/mx415_1_0001.cbf doesn\'t exist')
    def test_execute_eiger4m_fastMesh(self):
        referenceDataPath = self.dataPath / 'inData_eiger4m_fastMesh.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)
        self.assertEqual(len(outData['imageQualityIndicators']), 400)
    '''


if __name__ == '__main__':
    unittest.main()