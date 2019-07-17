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

import unittest

from utils import UtilsTest
from utils import UtilsConfig
from utils import UtilsLogging

from tasks.CrystfelTasks import ExeCrystFEL

logger = UtilsLogging.getLogger()


class CrystfelTaskExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    @unittest.skipIf(not os.path.exists('/scisoft/pxsoft/data/' +
                     'WORKFLOW_TEST_DATA/id30a1/20141110/RAW_DATA/' +
                     'opid30a1/1-1-4"'),
                     'Image directory doesn\'t exist')
    def test_execute_listOfImages(self):
        referenceDataPath = self.dataPath / 'inData_listOfImages.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ExeCrystFEL(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertEqual(outData['centering'], 'P')
        self.assertEqual(outData['space_group'], 'P622')

