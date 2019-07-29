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
import unittest

from edna2.utils import UtilsConfig
from edna2.utils import UtilsTest
from edna2.utils import UtilsLogging

from edna2.tasks.DozorTasks import ControlDozor

logger = UtilsLogging.getLogger()


class ControlDozorExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run control dozor test with default config')
    def test_execute_ControlDozor(self):
        referenceDataPath = self.dataPath / 'ControlDozor.json'
        self.inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        controlDozor = ControlDozor(inData=self.inData)
        controlDozor.execute()
        self.assertTrue(controlDozor.isSuccess())
        outData = controlDozor.outData
        self.assertEqual(len(outData['imageQualityIndicators']), 5)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run control dozor test with default config')
    def test_execute_ControlDozor_batchSize_2(self):
        referenceDataPath = self.dataPath / 'ControlDozor_batchSize_2.json'
        self.inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        controlDozor = ControlDozor(inData=self.inData)
        controlDozor.execute()
        self.assertTrue(controlDozor.isSuccess())
        outData = controlDozor.outData
        self.assertEqual(len(outData['imageQualityIndicators']), 5)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run control dozor test with default config')
    def test_execute_ControlDozor_batchSize_2a(self):
        referenceDataPath = self.dataPath / 'ControlDozor_batchSize_2a.json'
        self.inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        controlDozor = ControlDozor(inData=self.inData)
        controlDozor.execute()
        self.assertTrue(controlDozor.isSuccess())
        outData = controlDozor.outData
        self.assertEqual(len(outData['imageQualityIndicators']), 4)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run control dozor test with default config')
    @unittest.skipIf(not os.path.exists('/data/visitor/mx415/id30a2/20160315/' +
                                        'RAW_DATA/test3/mx415_1_0001.cbf'),
                     'Image /data/visitor/mx415/id30a2/20160315/RAW_DATA/' +
                     'test3/mx415_1_0001.cbf doesn\'t exist')
    def test_execute_ControlDozor_wedgeNumber(self):
        referenceDataPath = self.dataPath / 'ControlDozor_wedgeNumber.json'
        self.inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        controlDozor = ControlDozor(inData=self.inData)
        controlDozor.execute()
        self.assertTrue(controlDozor.isSuccess())
        outData = controlDozor.outData
        self.assertEqual(len(outData['imageQualityIndicators']), 740)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run control dozor test with default config')
    @unittest.skipIf(not os.path.exists('/data/visitor/mx415/id30a2/20180502/' +
                                        'RAW_DATA/t1/t1_1_0001.cbf'),
                     'Image /data/visitor/mx415/id30a2/20180502/RAW_DATA/' +
                     't1/t1_1_0001.cbf doesn\'t exist')
    def test_execute_ControlDozor_ispyb(self):
        currentSite = UtilsConfig.getSite()
        UtilsConfig.setSite('esrf_ispyb_valid')
        referenceDataPath = self.dataPath / 'ControlDozor_ispyb.json'
        self.inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        controlDozor = ControlDozor(inData=self.inData)
        controlDozor.execute()
        self.assertTrue(controlDozor.isSuccess())
        UtilsConfig.setSite(currentSite)
        outData = controlDozor.outData
        self.assertEqual(len(outData['imageQualityIndicators']), 640)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run control dozor test with default config')
    @unittest.skipIf(not os.path.exists('/data/visitor/mx415/id30a3/20171127/' +
                                        'RAW_DATA/mx415/1-2-2/MXPressF_01/' +
                                        'mesh-mx415_1_1_master.h5'),
                     'Image /data/visitor/mx415/id30a3/20171127/RAW_DATA/mx415/' +
                     '1-2-2/MXPressF_01/mesh-mx415_1_1_master.h5 doesn\'t exist')
    def test_execute_ControlDozor_ispyb_h5(self):
        currentSite = UtilsConfig.getSite()
        UtilsConfig.setSite('esrf_ispyb_valid')
        referenceDataPath = self.dataPath / 'ControlDozor_ispyb_hdf5.json'
        self.inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        controlDozor = ControlDozor(inData=self.inData)
        controlDozor.execute()
        UtilsConfig.setSite(currentSite)
        self.assertTrue(controlDozor.isSuccess())
        outData = controlDozor.outData
        self.assertEqual(len(outData['imageQualityIndicators']), 51)
