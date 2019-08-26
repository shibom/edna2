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
import shutil
import pathlib
import tempfile
import unittest

from edna2.utils import UtilsTest
from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

from edna2.tasks.ImageQualityIndicatorsTask import ImageQualityIndicatorsTask

logger = UtilsLogging.getLogger()


class ImageQualityIndicatorsEiger4MExecTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)
        # self.dataPath = pathlib.Path(os.getcwd()) / 'data'

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    @unittest.skipIf(not os.path.exists(
        '/scisoft/pxsoft/data/WORKFLOW_TEST_DATA/id30a3/inhouse/opid30a3' +
        '/20181126/RAW_DATA/tryp3/MXPressA_01/mesh-opid30a3_1_0001.cbf'),
        'Cannot find CBF file mesh-opid30a3_1_0001.cbf')
    def test_execute_eiger4m_cbf_10images(self):
        referenceDataPath = self.dataPath / 'eiger4m_cbf_10images.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)
        self.assertEqual(10, len(outData['imageQualityIndicators']))

    @unittest.skipIf(UtilsConfig.getSite() == 'Default',
                     'Cannot run ImageQualityIndicatorsExecTest ' +
                     'test with default config')
    @unittest.skipIf(not os.path.exists(
        '/scisoft/pxsoft/data/WORKFLOW_TEST_DATA/id30a3/inhouse/opid30a3' +
        '/20181126/RAW_DATA/tryp3/MXPressA_01/mesh-opid30a3_1_1_master.h5'),
        'Cannot find h5 master file mesh-opid30a3_1_1_master.h5')
    def test_execute_eiger4m_h5_10images(self):
        referenceDataPath = self.dataPath / 'eiger4m_h5_10images.json'
        inData = UtilsTest.loadAndSubstitueTestData(referenceDataPath)
        directory = pathlib.Path(inData['directory'])
        # tmpDirectory = tempfile.mkdtemp(prefix='eiger4m_h5_100images_')
        # shutil.copy(str(directory / 'mesh-opid30a3_1_1_master.h5'),
        #            tmpDirectory)
        # shutil.copy(str(directory / 'mesh-opid30a3_1_1_data_000001.h5'),
        #            tmpDirectory)
        # inData['directory'] = tmpDirectory
        task = ImageQualityIndicatorsTask(inData=inData)
        task.execute()
        self.assertFalse(task.isFailure())
        outData = task.outData
        self.assertTrue('imageQualityIndicators' in outData)
        self.assertEqual(len(outData['imageQualityIndicators']), 10)
        # shutil.rmtree(tmpDirectory)


if __name__ == '__main__':
    unittest.main()