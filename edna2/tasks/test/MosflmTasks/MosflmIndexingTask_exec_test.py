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
__date__ = "14/05/2019"

import unittest

from edna2.utils import UtilsTest
from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

from edna2.tasks.MosflmTasks import MosflmIndexingTask

logger = UtilsLogging.getLogger()


class MosflmTasksExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    # @unittest.skipIf(UtilsConfig.getSite() == 'Default',
    #                  'Cannot run mosflm test with default config')
    # def test_execute_MosflmIndexingTask_2m_RNASE_1(self):
    #     UtilsTest.loadTestImage('ref-2m_RNASE_1_0001.cbf')
    #     UtilsTest.loadTestImage('ref-2m_RNASE_1_0002.cbf')
    #     referenceDataPath = self.dataPath / 'mosflm_indexing_2m_RNASE_1.json'
    #     inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
    #     mosflmIndexingTask = MosflmIndexingTask(inData=inData)
    #     mosflmIndexingTask.execute()
    #     self.assertTrue(mosflmIndexingTask.isSuccess())

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run mosflm test with default config')
    def tes_execute_MosflmIndexingTask_TRYP_X1_4(self):
        UtilsTest.loadTestImage('ref-TRYP-X1_4_0001.cbf')
        UtilsTest.loadTestImage('ref-TRYP-X1_4_0002.cbf')
        UtilsTest.loadTestImage('ref-TRYP-X1_4_0003.cbf')
        UtilsTest.loadTestImage('ref-TRYP-X1_4_0004.cbf')
        referenceDataPath = self.dataPath / 'mosflm_indexing_TRYP-X1_4.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        mosflmIndexingTask = MosflmIndexingTask(inData=inData)
        mosflmIndexingTask.execute()
        self.assertTrue(mosflmIndexingTask.isSuccess())

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run mosflm test with default config')
    def test_execute_MosflmIndexingTask_TRYP_X1_4(self):
        referenceDataPath = self.dataPath / 'TRYP-X1_4.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        mosflmIndexingTask = MosflmIndexingTask(inData=inData)
        mosflmIndexingTask.execute()
        self.assertTrue(mosflmIndexingTask.isSuccess())