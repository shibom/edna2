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

import pathlib
import unittest

from edna2.tasks.H5ToCBFTask import H5ToCBFTask

from edna2.utils import UtilsTest
from edna2.utils import UtilsImage


class H5ToCBFUnitTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    def test_generateCommands_withImageNumber(self):
        referenceDataPath = self.dataPath / 'H5ToCBF_withImageNumber.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath,
                                                    loadTestImages=False)
        hdf5File = pathlib.Path(inData['hdf5File'])
        directory = hdf5File.parent
        prefix = UtilsImage.getPrefix(hdf5File)
        commandLine, cbfFile = H5ToCBFTask.generateCommandsWithImageNumber(
            inData, directory, prefix, hdf5File)
        self.assertTrue(commandLine is not None)
        self.assertTrue(cbfFile is not None)

    def test_generateCommands_withImageRange(self):
        referenceDataPath = self.dataPath / 'H5ToCBF_withImageRange.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath,
                                                    loadTestImages=False)
        hdf5File = pathlib.Path(inData['hdf5File'])
        directory = hdf5File.parent
        prefix = UtilsImage.getPrefix(hdf5File)
        commandLine, template = H5ToCBFTask.generateCommandsWithImageRange(
            inData, directory, prefix, hdf5File)
        self.assertTrue(commandLine is not None)
        self.assertTrue(template is not None)
