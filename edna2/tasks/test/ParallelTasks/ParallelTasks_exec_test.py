# Copyright (c) European Synchrotron Radiation Facility (ESRF)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the 'Software'), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import unittest

from edna2.utils import UtilsTest
from edna2.utils import UtilsLogging

from edna2.tasks.test.ParallelTasks.ExampleTask import ExampleTask
from edna2.tasks.test.ParallelTasks.ControlTestTask import ControlTestTask

logger = UtilsLogging.getLogger()


class ParallelTasksExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    def test_runTestTask(self):
        inData = {'taskNumber': 1}
        logger.info('*'*80)
        testTask = ExampleTask(inData=inData)
        testTask.execute()
        if not testTask.isFailure():
            logger.info(1)
            outData = testTask.getOutData()
            logger.info(2)
            self.assertEqual(outData, {'status': 'finished'})
            # outData = testTask.outData
            # self.assertEqual(outData, {'status': 'finished'})

    def test_runControlTestTask(self):
        inData = {'startNumber': 1, 'numberOfTasks': 4}
        controlTestTask = ControlTestTask(inData=inData)
        controlTestTask.execute()
        outData = controlTestTask.outData
        self.assertEqual(outData['status'], 'finished')

    def test_runTwoControlTestTasks(self):
        inData1 = {'startNumber': 1, 'numberOfTasks': 4}
        controlTestTask1 = ControlTestTask(inData=inData1)
        inData2 = {'startNumber': 11, 'numberOfTasks': 4}
        controlTestTask2 = ControlTestTask(inData=inData2)
        controlTestTask1.start()
        controlTestTask2.start()
        controlTestTask1.join()
        controlTestTask2.join()
        outData1 = controlTestTask1.outData
        self.assertEqual(outData1['status'], 'finished')
        outData2 = controlTestTask2.outData
        self.assertEqual(outData2['status'], 'finished')

