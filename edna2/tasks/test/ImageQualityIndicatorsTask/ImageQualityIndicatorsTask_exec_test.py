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

import os
import logging
import unittest

from utils import UtilsTest
from utils import UtilsConfig

from tasks.ImageQualityIndicatorsTask import ImageQualityIndicatorsTask

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('edna2')
logger.setLevel(logging.DEBUG)


class ImageQualityIndicatorsExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    def tes_execute_listOfImages(self):
        referenceDataPath = self.dataPath / 'inData_listOfImages.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    def test_execute_startEnd(self):
        referenceDataPath = self.dataPath / 'inData_startEnd.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)

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
