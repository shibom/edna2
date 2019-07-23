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


import unittest

from edna2.utils import UtilsPath


class UtilsTestUnitTest(unittest.TestCase):

    def test_createPyarchFilePath(self):
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/')),
            '/')
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data')),
            '/data')
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data/visitor')),
            '/data/visitor')
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id14eh2')),
            '/data/visitor/mx415/id14eh2')
        self.assertEqual(
            '/data/pyarch/2010/id14eh2/mx415/20100212',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id14eh2/20100212')),
            '/data/visitor/mx415/id14eh2/20100212')
        self.assertEqual(
            '/data/pyarch/2010/id14eh2/mx415/20100212/1',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id14eh2/20100212/1')),
            '/data/visitor/mx415/id14eh2/20100212/1')
        self.assertEqual(
            '/data/pyarch/2010/id14eh2/mx415/20100212/1/2',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id14eh2/20100212/1/2')),
            '/data/visitor/mx415/id14eh2/20100212/1/2')
        # Test with inhouse account...
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/')),
            '/')
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data')),
            '/data')
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data/id23eh2')),
            '/data/id23eh2')
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data/id23eh2/inhouse')),
            '/data/id23eh2/inhouse')
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data/id23eh2/inhouse/opid232')),
            '/data/id23eh2/inhouse/opid232')
        self.assertEqual(
            '/data/pyarch/2010/id23eh2/opid232/20100525',
            str(UtilsPath.createPyarchFilePath('/data/id23eh2/inhouse/opid232/20100525')),
            '/data/id23eh2/inhouse/opid232/20100525')
        self.assertEqual(
            '/data/pyarch/2010/id23eh2/opid232/20100525/1',
            str(UtilsPath.createPyarchFilePath('/data/id23eh2/inhouse/opid232/20100525/1')),
            '/data/id23eh2/inhouse/opid232/20100525/1')
        self.assertEqual(
            '/data/pyarch/2010/id23eh2/opid232/20100525/1/2',
            str(UtilsPath.createPyarchFilePath('/data/id23eh2/inhouse/opid232/20100525/1/2')),
            '/data/id23eh2/inhouse/opid232/20100525/1/2')
        self.assertEqual(
            '/data/pyarch/2014/id30a1/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles',
            str(UtilsPath.createPyarchFilePath('/data/id30a1/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles')),
            '/data/id30a1/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles')
        # Visitor
        self.assertEqual(
            'None',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id30a3')),
            '/data/visitor/mx415/id30a3')
        self.assertEqual(
            '/data/pyarch/2010/id30a3/mx415/20100212',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id30a3/20100212')),
            '/data/visitor/mx415/id30a3/20100212')
        self.assertEqual(
            '/data/pyarch/2010/id30a3/mx415/20100212/1',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id30a3/20100212/1')),
            '/data/visitor/mx415/id30a3/20100212/1')
        self.assertEqual(
            '/data/pyarch/2010/id30a3/mx415/20100212/1/2',
            str(UtilsPath.createPyarchFilePath('/data/visitor/mx415/id30a3/20100212/1/2')),
            '/data/visitor/mx415/id30a3/20100212/1/2')
        self.assertEqual(
            '/data/pyarch/2010/id30a3/opid232/20100525',
            str(UtilsPath.createPyarchFilePath('/data/id30a3/inhouse/opid232/20100525')),
            '/data/id30a3/inhouse/opid232/20100525')
        self.assertEqual(
            '/data/pyarch/2010/id30a3/opid232/20100525/1',
            str(UtilsPath.createPyarchFilePath('/data/id30a3/inhouse/opid232/20100525/1')),
            '/data/id30a3/inhouse/opid232/20100525/1')
        self.assertEqual(
            '/data/pyarch/2010/id30a3/opid232/20100525/1/2',
            str(UtilsPath.createPyarchFilePath('/data/id30a3/inhouse/opid232/20100525/1/2')),
            '/data/id30a3/inhouse/opid232/20100525/1/2')
        self.assertEqual(
            '/data/pyarch/2014/id30a3/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles',
            str(UtilsPath.createPyarchFilePath('/data/id30a3/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles')),
            '/data/id30a3/inhouse/opid30a1/20140717/RAW_DATA/opid30a1_1_dnafiles')
