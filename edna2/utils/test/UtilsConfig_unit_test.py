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
import unittest

from utils import UtilsConfig
from utils import UtilsLogging

logger = UtilsLogging.getLogger()


class UtilsConfigUnitTest(unittest.TestCase):

    def setUp(self):
        self.site = "esrf_id30a2"
        os.environ["EDNA2_SITE"] = self.site
        os.environ["ISPyB_user"] = "ispybws1"

    def test_getConfigDir(self):
        configDir = UtilsConfig.getConfigDir()
        self.assertTrue(configDir.exists())

    def test_getSite(self):
        site = UtilsConfig.getSite()
        self.assertEqual(site, self.site)

    def test_getConfig(self):
        config = UtilsConfig.getConfig()
        sections = config.sections()
        self.assertTrue("ExecDozor" in sections)

    def test_getTaskConfig(self):
        taskName = "ExecDozor"
        dictConfig = UtilsConfig.getTaskConfig(taskName)
        self.assertTrue("ix_min" in dictConfig)
        taskName = "ISPyB"
        dictConfig = UtilsConfig.getTaskConfig(taskName)
        self.assertTrue("username" in dictConfig)
        self.assertEqual(dictConfig["username"], os.environ["ISPyB_user"])


