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
__date__ = "28/04/2020"

import unittest

from edna2.utils import UtilsSymmetry


class EDTestCaseUtilsSymmetry(unittest.TestCase):

    def test_getMinimumSymmetrySpaceGroupFromBravaisLattice(self):
        """
        Testing retrieving the lowest symmetry space group from all Bravais Lattices
        """
        listBravaisLattice = [
            "aP", "mP", "mC", "mI", "oP", "oA", "oB", "oC", "oS", "oF", "oI", "tP", "tC", "tI", "tF",
            "hP", "hR", "cP", "cF", "cI"
        ]
        listSpaceGroup = [
            "P1", "P2", "C2", "C2", "P222", "C222", "C222", "C222", "C222", "F222", "I222",
            "P4", "P4", "I4", "I4", "P3", "H3", "P23", "F23", "I23"
        ]
        for index in range(len(listBravaisLattice)):
            self.assertEqual(
                listSpaceGroup[index],
                UtilsSymmetry.getMinimumSymmetrySpaceGroupFromBravaisLattice(listBravaisLattice[index])
            )

    def test_getITNumberFromSpaceGroupName(self):
        self.assertEqual(1, UtilsSymmetry.getITNumberFromSpaceGroupName("P1"), "ITNumber from space group P1")
        self.assertEqual(3, UtilsSymmetry.getITNumberFromSpaceGroupName("P2"), "ITNumber from space group P2")
        self.assertEqual(5, UtilsSymmetry.getITNumberFromSpaceGroupName("C2"), "ITNumber from space group C2")
        self.assertEqual(16, UtilsSymmetry.getITNumberFromSpaceGroupName("P222"), "ITNumber from space group P222")
        self.assertEqual(21, UtilsSymmetry.getITNumberFromSpaceGroupName("C222"), "ITNumber from space group C222")
        self.assertEqual(22, UtilsSymmetry.getITNumberFromSpaceGroupName("F222"), "ITNumber from space group F222")
        self.assertEqual(75, UtilsSymmetry.getITNumberFromSpaceGroupName("P4"), "ITNumber from space group P4")
        self.assertEqual(79, UtilsSymmetry.getITNumberFromSpaceGroupName("I4"), "ITNumber from space group I4")
        self.assertEqual(143, UtilsSymmetry.getITNumberFromSpaceGroupName("P3"), "ITNumber from space group P3")
        self.assertEqual(146, UtilsSymmetry.getITNumberFromSpaceGroupName("H3"), "ITNumber from space group H3")
        self.assertEqual(195, UtilsSymmetry.getITNumberFromSpaceGroupName("P23"), "ITNumber from space group P23")
        self.assertEqual(196, UtilsSymmetry.getITNumberFromSpaceGroupName("F23"), "ITNumber from space group F23")

    def testGetSpaceGroupNameFromITNumber(self):
        self.assertEqual("P1", UtilsSymmetry.getSpaceGroupNameFromITNumber(1), "Space group from from it number 1")
        self.assertEqual("P2", UtilsSymmetry.getSpaceGroupNameFromITNumber(3), "Space group from from it number 3")
        self.assertEqual("C2", UtilsSymmetry.getSpaceGroupNameFromITNumber(5), "Space group from from it number 5")
        self.assertEqual("P222", UtilsSymmetry.getSpaceGroupNameFromITNumber(16), "Space group from from it number 16")
        self.assertEqual("C222", UtilsSymmetry.getSpaceGroupNameFromITNumber(21), "Space group from from it number 21")
        self.assertEqual("F222", UtilsSymmetry.getSpaceGroupNameFromITNumber(22), "Space group from from it number 22")
        self.assertEqual("P4", UtilsSymmetry.getSpaceGroupNameFromITNumber(75), "Space group from from it number 75")
        self.assertEqual("I4", UtilsSymmetry.getSpaceGroupNameFromITNumber(79), "Space group from from it number 79")
        self.assertEqual("P3", UtilsSymmetry.getSpaceGroupNameFromITNumber(143), "Space group from from it number 143")
        self.assertEqual("H3", UtilsSymmetry.getSpaceGroupNameFromITNumber(146), "Space group from from it number 146")
        self.assertEqual("P23", UtilsSymmetry.getSpaceGroupNameFromITNumber(195), "Space group from from it number 195")
        self.assertEqual("F23", UtilsSymmetry.getSpaceGroupNameFromITNumber(196), "Space group from from it number 196")


