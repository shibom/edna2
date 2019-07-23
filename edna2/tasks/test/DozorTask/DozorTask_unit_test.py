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

__authors__ = ['O. Svensson']
__license__ = 'MIT'
__date__ = '21/04/2019'

import os
import json
import shutil
import unittest
import tempfile

from edna2.tasks.DozorTasks import ExecDozor

from edna2.utils import UtilsTest


class ExecDozorUnitTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)
        referenceDataPath = self.dataPath / 'inDataDozor.json'
        with open(str(referenceDataPath)) as f:
            self.inData = json.load(f)
        self.dozor = ExecDozor(inData=self.inData)

    def test_generateCommands(self):
        dozor = ExecDozor(inData=self.inData)
        strCommandText = dozor.generateCommands(self.inData)
        # print(strCommandText)
        self.assertTrue(strCommandText is not None)

    def test_parseOutput(self):
        self.dozor.startingAngle = 10.0
        self.dozor.firstImageNumber = 1
        self.dozor.oscillationRange = 0.1
        self.dozor.overlap = 0.0
        logFileName = self.dataPath / 'Dozor_v2.0.2.log'
        with open(str(logFileName)) as f:
            output = f.read()
        result = self.dozor.parseOutput(self.inData, output)
        self.assertEqual(10,
                         len(result['imageDozor']),
                         "Result from 10 images")
        # Log file with 'no results'
        logFileName2 = self.dataPath / 'Dozor_v2.0.2_no_results.log'
        with open(str(logFileName2)) as f:
            output2 = f.read()
        result2 = self.dozor.parseOutput(self.inData, output2)
        self.assertEqual(51,
                         len(result2['imageDozor']),
                         "Result from 51 images")

    def test_parseDouble(self):
        self.assertEqual(1.0,
                         ExecDozor.parseDouble('1.0'),
                         "Parsing '1.0'")
        self.assertEqual(None,
                         ExecDozor.parseDouble('****'),
                         "Parsing '****'")

    def test_generatePngPlots(self):
        plotmtvFile = self.dataPath / 'dozor_rd.mtv'
        tmpDir = tempfile.mkdtemp(suffix='EDTestCasePluginUnitDozor_')
        listFile = ExecDozor.generatePngPlots(plotmtvFile, tmpDir)
        for plotFile in listFile:
            self.assertTrue(os.path.exists(plotFile))
        shutil.rmtree(tmpDir)


