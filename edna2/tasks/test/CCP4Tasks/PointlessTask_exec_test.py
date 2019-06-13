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

from tasks import PointlessTask

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('edna2')
logger.setLevel(logging.DEBUG)


class PointlessTasksExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    @unittest.skipIf(os.name == 'nt', "Don't run on Windows")
    def test_execute_PointlessTask(self):
        referenceDataPath = self.dataPath / 'inDataPointlessTask.json'
        tmpDir = UtilsTest.createTestTmpDirectory('PointlessTask')
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath,
                                                    tmpDir=tmpDir)
        task = PointlessTask(inData=inData)
        task.execute()
        assert not task.isFailure()
        outData = task.outData
        assert outData['isSuccess']
