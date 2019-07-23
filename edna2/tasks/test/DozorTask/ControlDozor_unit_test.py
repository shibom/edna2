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


__author__ = "Olof Svensson"
__contact__ = "svensson@esrf.fr"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os
import json

import unittest

# from controltasks import ControlDozor
from edna2.tasks.DozorTasks import ControlDozor


class ControlDozorUnitTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = os.path.join(os.path.dirname(__file__),
                                     "data")
        referenceDataPath = os.path.join(self.dataPath,
                                         "ControlDozor.json")
        with open(referenceDataPath) as f:
            self.inData = json.loads(f.read())
        self.controlDozor = ControlDozor(inData=self.inData)

    def testCreateDict(self):
        dictImage = self.controlDozor.createImageDict(self.inData)
        self.assertEqual(True, isinstance(dictImage, dict))

    def testCreateListOfBatches(self):
        self.assertEqual(
            [[1], [2], [3], [4], [5]],
            ControlDozor.createListOfBatches(range(1, 6), 1)
        )

        self.assertEqual(
            [[1, 2], [3, 4], [5]],
            ControlDozor.createListOfBatches(range(1, 6), 2)
        )

        self.assertEqual(
            [[1, 2, 3], [4, 5]],
            ControlDozor.createListOfBatches(range(1, 6), 3)
        )

        self.assertEqual(
            [[1, 2, 3, 4], [5]],
            ControlDozor.createListOfBatches(range(1, 6), 4)
        )

        self.assertEqual(
            [[1, 2, 3, 4, 5]],
            ControlDozor.createListOfBatches(range(1, 6), 5)
        )

        self.assertEqual(
            [[1], [2], [4], [5], [6]],
            ControlDozor.createListOfBatches(
                list(range(4, 7)) + list(range(1, 3)),
                1
            )
        )

        self.assertEqual(
            [[1, 2], [4, 5], [6]],
            ControlDozor.createListOfBatches(
                list(range(4, 7)) + list(range(1, 3)),
                2
            )
        )

        self.assertEqual(
            [[1, 2], [4, 5, 6]],
            ControlDozor.createListOfBatches(
                list(range(4, 7)) + list(range(1, 3)),
                3
            )
        )
