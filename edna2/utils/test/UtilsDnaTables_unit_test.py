#
# Copyright (c) European Synchrotron Radiation Facility (ESRF)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the 'Software')), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__authors__ = ['O. Svensson']
__license__ = 'MIT'
__date__ = '21/04/2019'

import pathlib
import unittest

from edna2.utils import UtilsDnaTables
from edna2.utils import UtilsLogging

logger = UtilsLogging.getLogger()


class UtilsTestUnitTest(unittest.TestCase):

    def setUp(self):
        self.dataPath = pathlib.Path(__file__).parent / 'data'

    def test_getDict(self):
        dictDnaTables = UtilsDnaTables.getDict(
            self.dataPath / 'indexingTwoImagesDnaTables.xml')
        # logger.info(pprint.pformat(dictDnaTables))
        self.assertTrue(dictDnaTables is not None)

    def test_getTables(self):
        dictDnaTables = UtilsDnaTables.getDict(
            self.dataPath / 'indexingTwoImagesDnaTables.xml')
        listTables = UtilsDnaTables.getTables(
            dictDnaTables, 'autoindex_solutions')
        # logger.info(pprint.pformat(listTables))
        self.assertGreaterEqual(len(list(listTables)), 1)

    def test_getListParam(self):
        dictDnaTables = UtilsDnaTables.getDict(
            self.dataPath / 'indexingTwoImagesDnaTables.xml')
        listTables = UtilsDnaTables.getTables(
            dictDnaTables, 'autoindex_solutions')
        listParameter = UtilsDnaTables.getListParam(listTables[0])
        # logger.info(pprint.pformat(listParameter))
        self.assertGreaterEqual(len(listParameter), 1)

    def test_getItemValue(self):
        dictDnaTables = UtilsDnaTables.getDict(
            self.dataPath / 'indexingTwoImagesDnaTables.xml')
        listTables = UtilsDnaTables.getTables(
            dictDnaTables, 'autoindex_solutions')
        listParameter = UtilsDnaTables.getListParam(listTables[0])
        dictParam = listParameter[0]
        # logger.info(pprint.pformat(dictParam))
        self.assertEqual(UtilsDnaTables.getItemValue(dictParam, 'penalty'), 999)
        self.assertEqual(UtilsDnaTables.getItemValue(dictParam, 'lattice'), 'cI')
        self.assertEqual(UtilsDnaTables.getItemValue(dictParam, 'a'), 121.869148)

    def test_getListValue(self):
        # Mosaicity
        dictDnaTables = UtilsDnaTables.getDict(
            self.dataPath / 'indexingTwoImagesDnaTables.xml')
        listTables = UtilsDnaTables.getTables(
            dictDnaTables, 'mosaicity_estimation')
        listParameter = UtilsDnaTables.getListParam(listTables[0])
        # logger.info(pprint.pformat(listParameter))
        self.assertEqual(UtilsDnaTables.getListValue(
            listParameter, 'mosaicity', 'value'), 0.1)
        # Refinement
        listTablesRefinement = UtilsDnaTables.getTables(
            dictDnaTables, 'refinement')
        tableRefinement = listTablesRefinement[0]
        listParamRefinement = UtilsDnaTables.getListParam(tableRefinement)
        # logger.info(pprint.pformat(listParamRefinement))
        self.assertEqual(UtilsDnaTables.getListValue(
            listParamRefinement, 'parameters', 'used'), 204)
        self.assertEqual(UtilsDnaTables.getListValue(
            listParamRefinement, 'results', 'detector_distance'), 305.222015)
        self.assertEqual(UtilsDnaTables.getListValue(
            listParamRefinement, 'deviations', 'positional'), 1.351692)
