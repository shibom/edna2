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

import os
import pprint
import logging
import unittest

from utils import UtilsTest

from tasks.MosflmTasks import AbstractMosflmTask
from tasks.MosflmTasks import MosflmIndexingTask

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('edna2')
logger.setLevel(logging.DEBUG)


class MosflmTasksUnitTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)
        self.oldEdna2Config = os.environ.get('EDNA2_CONFIG', None)
        self.oldEdna2Site = os.environ.get('EDNA2_SITE', None)
        os.environ['EDNA2_CONFIG'] = str(self.dataPath)
        os.environ['EDNA2_SITE'] = 'mosflm_testconfig'

    def tearDown(self):
        if self.oldEdna2Config:
            os.environ['EDNA2_CONFIG'] = self.oldEdna2Config
        else:
            del os.environ['EDNA2_CONFIG']
        if self.oldEdna2Site:
            os.environ['EDNA2_SITE'] = self.oldEdna2Site
        else:
            del os.environ['EDNA2_SITE']

    def test_generateMOSFLMCommands(self):
        referenceDataPath = self.dataPath / 'inDataAbstractMosflmTask.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        abstractMosflmTask = AbstractMosflmTask(inData=inData)
        listCommands = abstractMosflmTask.generateMOSFLMCommands(inData)
        # logger.info(pprint.pformat(listCommands))
        for requiredItem in ['BEAM', 'DETECTOR', 'OMEGA', 'REVERSEPHI',
                             'DIRECTORY', 'TEMPLATE', 'LIMITS EXCLUDE',
                             'RASTER', 'POLARIZATION']:
            self.assertTrue(requiredItem in ' '.join(listCommands))

    def test_getNewmat(self):
        inData = {}
        abstractMosflmTask = AbstractMosflmTask(inData=inData)
        newmat = abstractMosflmTask.getNewmat(self.dataPath / 'newmat.txt')
        self.assertTrue('cell' in newmat)
        self.assertTrue('matrixA' in newmat)
        self.assertTrue('matrixU' in newmat)
        self.assertTrue('missettingsAngles' in newmat)

    def test_generateMOSFLMCommands_indexing(self):
        referenceDataPath = self.dataPath / 'inDataAbstractMosflmTask.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        listCommands = MosflmIndexingTask.generateMOSFLMCommands(inData)
        for requiredItem in ['BEAM', 'DETECTOR', 'OMEGA', 'REVERSEPHI',
                             'DIRECTORY', 'TEMPLATE', 'LIMITS EXCLUDE',
                             'RASTER', 'POLARIZATION']:
            self.assertTrue(requiredItem in ' '.join(listCommands))

    def test_parseIndexingMosflmOutput(self):
        newMatFilePath = self.dataPath / 'newmat.txt'
        dnaTablesPath = self.dataPath / 'indexingTwoImagesDnaTables.xml'
        task = MosflmIndexingTask(inData={})
        outData = task.parseIndexingMosflmOutput(newMatFilePath, dnaTablesPath)
        logger.info(pprint.pformat(outData))


