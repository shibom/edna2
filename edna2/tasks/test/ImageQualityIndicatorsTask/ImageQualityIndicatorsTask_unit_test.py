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

import logging
import pathlib
import unittest

from edna2.utils import UtilsLogging

from edna2.tasks.ImageQualityIndicatorsTask import ImageQualityIndicatorsTask

logger = UtilsLogging.getLogger()


class ImageQualityIndicatorsUnitTest(unittest.TestCase):

    def testGetH5FilePath(self):
        filePath1 = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20160204/RAW_DATA/" +
            "meshtest/XrayCentering_01/mesh-meshtest_1_0001.cbf")
        h5MasterFilePath1, h5DataFilePath1, h5FileNumber = \
            ImageQualityIndicatorsTask.getH5FilePath(filePath1, 9)
        h5MasterFilePath1Reference = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20160204/RAW_DATA/" +
            "meshtest/XrayCentering_01/mesh-meshtest_1_1_master.h5")
        h5DataFilePath1Reference = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20160204/RAW_DATA/" +
            "meshtest/XrayCentering_01/mesh-meshtest_1_1_data_000001.h5")
        self.assertEqual(h5MasterFilePath1,
                         h5MasterFilePath1Reference,
                         "masterPath1")
        self.assertEqual(h5DataFilePath1,
                         h5DataFilePath1Reference,
                         "dataPath1")
        #
        # fast mesh
        #
        filePath2 = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20171017/RAW_DATA/" +
            "mesh2/MeshScan_02/mesh-opid30a3_2_0021.cbf")
        h5MasterFilePath2, h5DataFilePath2, h5FileNumber2 = \
            ImageQualityIndicatorsTask.getH5FilePath(
                filePath2, batchSize=20, isFastMesh=True)
        h5MasterFilePath2Reference = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20171017/RAW_DATA/" +
            "mesh2/MeshScan_02/mesh-opid30a3_2_1_master.h5")
        self.assertEqual(h5MasterFilePath2,
                         h5MasterFilePath2Reference,
                         "master path2")
        h5DataFilePath2Reference = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20171017/RAW_DATA/" +
            "mesh2/MeshScan_02/mesh-opid30a3_2_1_data_000001.h5")
        self.assertEqual(h5DataFilePath2,
                         h5DataFilePath2Reference,
                         "data path2")
        #
        # fast mesh 2
        #
        filePath2 = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20171017/RAW_DATA/mesh2" +
            "/MeshScan_02/mesh-opid30a3_2_0321.cbf")
        h5MasterFilePath2, h5DataFilePath2, h5FileNumber2 = \
            ImageQualityIndicatorsTask.getH5FilePath(
                filePath2, batchSize=20, isFastMesh=True)
        h5MasterFilePath2Reference = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20171017/RAW_DATA/mesh2/" +
            "MeshScan_02/mesh-opid30a3_2_1_master.h5")
        self.assertEqual(h5MasterFilePath2,
                         h5MasterFilePath2Reference,
                         "master path2")
        h5DataFilePath2Reference = pathlib.Path(
            "/data/id30a3/inhouse/opid30a3/20171017/RAW_DATA/mesh2/" +
            "MeshScan_02/mesh-opid30a3_2_1_data_000004.h5")
        self.assertEqual(h5DataFilePath2,
                         h5DataFilePath2Reference,
                         "data path2")
