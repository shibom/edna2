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

from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

logger = UtilsLogging.getLogger()


class UtilsConfigUnitTest(unittest.TestCase):

    def setUp(self):
        self.oldISPyBUser = None
        if "ISPyB_user" in os.environ:
            self.oldISPyBUser = os.environ["ISPyB_user"]
        os.environ["ISPyB_user"] = "ispybuser"

    def tearDown(self):
        if self.oldISPyBUser is None:
            del os.environ['ISPyB_user']
        else:
            os.environ["ISPyB_user"] = self.oldISPyBUser

    def test_getConfigDir(self):
        configDir = UtilsConfig.getConfigDir()
        self.assertTrue(configDir.exists())

    def test_getConfig(self):
        config = UtilsConfig.getConfig(site='esrf_id30a2')
        sections = config.sections()
        self.assertTrue("ExecDozor" in sections)

    def test_getTaskConfig(self):
        taskName = "ExecDozor"
        dictConfig = UtilsConfig.getTaskConfig(taskName, site='esrf_id30a2')
        self.assertTrue("ix_min" in dictConfig)
        taskName = "ISPyB"
        dictConfig = UtilsConfig.getTaskConfig(taskName, site='esrf_id30a2')
        self.assertTrue("username" in dictConfig)
        self.assertEqual(dictConfig["username"], os.environ["ISPyB_user"])



