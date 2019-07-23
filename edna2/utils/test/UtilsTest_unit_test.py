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


class UtilsTestUnitTest(unittest.TestCase):

    def setUp(self):
        self.inData1 = {
            "image": "$EDNA2_TESTDATA_IMAGES/ref-2m_RNASE_1_0001.cbf"
        }
        self.inData2 = {
            "images": [
                "$EDNA2_TESTDATA_IMAGES/ref-2m_RNASE_1_0001.cbf",
                "$EDNA2_TESTDATA_IMAGES/ref-2m_RNASE_1_0002.cbf"
                ]
        }

    def test_getTestdataPath(self):
        testdataDir = UtilsTest.getTestdataPath()
        print(testdataDir)

    def test_substitute(self):
        # One unix path
        newInData1 = UtilsTest.substitute(self.inData1, "$EDNA2_TESTDATA_IMAGES", "/data")
        self.assertEqual(newInData1["image"], "/data/ref-2m_RNASE_1_0001.cbf")
        # Two unix paths
        newInData2 = UtilsTest.substitute(self.inData2, "$EDNA2_TESTDATA_IMAGES", "/data")
        self.assertEqual(newInData2["images"][0], "/data/ref-2m_RNASE_1_0001.cbf")
        self.assertEqual(newInData2["images"][1], "/data/ref-2m_RNASE_1_0002.cbf")

    def test_getSearchStringFileNames(self):
        listFileNames1 = UtilsTest.getSearchStringFileNames("$EDNA2_TESTDATA_IMAGES", self.inData1)
        self.assertEqual(listFileNames1, ["ref-2m_RNASE_1_0001.cbf"])
        listFileNames2 = UtilsTest.getSearchStringFileNames("$EDNA2_TESTDATA_IMAGES", self.inData2)
        self.assertEqual(listFileNames2, ["ref-2m_RNASE_1_0001.cbf", "ref-2m_RNASE_1_0002.cbf"])
 