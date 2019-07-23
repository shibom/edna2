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

from edna2.utils import UtilsTest
from edna2.utils import UtilsLogging

from edna2.tasks.CCP4Tasks import PointlessTask

logger = UtilsLogging.getLogger()


class CCP4Tasks(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    def test_unit_PointlessTask(self):
        pathToLogFile = self.dataPath / 'pointless.log'
        outData = PointlessTask.parsePointlessOutput(pathToLogFile)
        self.assertEqual("C 2 2 2", outData['sgstr'], "Space group name")
        self.assertEqual(21, outData['sgnumber'], "Space group number")
        self.assertEqual(52.55, outData['cell']['length_a'], "Cell length a")
        self.assertEqual(148.80, outData['cell']['length_b'], "Cell length b")
        self.assertEqual(79.68, outData['cell']['length_c'], "Cell length v")
        self.assertEqual(91.00, outData['cell']['angle_alpha'], "Cell angle alpha")
        self.assertEqual(92.00, outData['cell']['angle_beta'], "Cell angle beta")
        self.assertEqual(93.00, outData['cell']['angle_gamma'], "Cell angle gamma")
        pathToLogFile2 = self.dataPath / 'pointless2.log'
        outData = PointlessTask.parsePointlessOutput(pathToLogFile2)
        self.assertEqual("P 3 2 1", outData['sgstr'], "Space group name")
        self.assertEqual(150, outData['sgnumber'], "Space group number")
        self.assertEqual(110.9918, outData['cell']['length_a'], "Cell length a")
        self.assertEqual(110.9918, outData['cell']['length_b'], "Cell length b")
        self.assertEqual(137.0160, outData['cell']['length_c'], "Cell length v")
        self.assertEqual(94.00, outData['cell']['angle_alpha'], "Cell angle alpha")
        self.assertEqual(95.00, outData['cell']['angle_beta'], "Cell angle beta")
        self.assertEqual(120.00, outData['cell']['angle_gamma'], "Cell angle gamma")
