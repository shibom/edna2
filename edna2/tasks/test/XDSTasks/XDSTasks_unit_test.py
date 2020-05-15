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
__date__ = "20/04/2020"

import unittest
import tempfile

from edna2.utils import UtilsTest
from edna2.utils import UtilsLogging

from edna2.tasks.XDSTasks import XDSTask
from edna2.tasks.XDSTasks import XDSIndexingTask

logger = UtilsLogging.getLogger()


class XDSTasksUnitTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = UtilsTest.prepareTestDataPath(__file__)

    def tes_writeSPOT_XDS(self):
        spotFile = self.dataPath / '00001.spot'
        spotXdsReferenceFile = self.dataPath / 'SPOT.XDS'
        with open(str(spotXdsReferenceFile)) as f:
            spotXdsReference = f.read()
        spotXds = XDSTask.createSPOT_XDS([spotFile], oscRange=1)
        with open('/tmp/SPOT.XDS', 'w') as f:
            f.write(spotXds)
        with open('/tmp/SPOT.XDS_REF', 'w') as f:
            f.write(spotXdsReference)
        self.assertEqual(spotXdsReference.split('\n')[0], spotXds.split('\n')[0])
        self.assertEqual(spotXdsReference, spotXds)

    def test_readIdxrefLp(self):
        idxRefLpPath = self.dataPath / 'IDXREF.LP'
        resultXDSIndexing = XDSIndexingTask.readIdxrefLp(idxRefLpPath)

    def test_parseXparm(self):
        xparmPath = self.dataPath / 'XPARM.XDS'
        xparmDict = XDSIndexingTask.parseXparm(xparmPath)
        pass
