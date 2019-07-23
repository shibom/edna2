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

# Corresponding EDNA code:
# https://github.com/olofsvensson/edna-mx
# mxPluginExec/plugins/EDPluginMXWaitFile-v1.1/plugins/EDPluginMXWaitFilev1_1.py

import os
import time
import pathlib

from edna2.tasks.AbstractTask import AbstractTask

from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

logger = UtilsLogging.getLogger()

DEFAULT_TIMEOUT = 120 # s


class WaitFileTask(AbstractTask):
    """
    This plugin waits for a file to appear on disk
    """

    def run(self, inData):
        # Wait for file if it's not already on disk'
        if not "file" in inData:
            raise BaseException("No expected file path in input!")
        filePath = pathlib.Path(self.inData["file"])
        logger.debug("Waiting for file {0}".format(filePath))
        finalSize = None
        hasTimedOut = False
        shouldContinue = True
        fileDir = filePath.parent
        expectedSize = inData.get('expectedSize', None)
        configTimeOut = UtilsConfig.get(self, 'timeOut', DEFAULT_TIMEOUT)
        timeOut = inData.get('timeOut', configTimeOut)
        if os.name != 'nt' and fileDir.exists():
            # Patch provided by Sebastien 2018/02/09 for forcing NFS cache:
            logger.debug("NFS cache clear, doing os.fstat on directory {0}".format(fileDir))
            d = os.open(fileDir.as_posix(), os.O_DIRECTORY)
            statResult = os.fstat(d)
            logger.debug("Results of os.fstat: {0}".format(statResult))
        # Check if file is there
        if filePath.exists():
            fileSize = filePath.stat().st_size
            if expectedSize is not None:
                # Check size
                if fileSize > expectedSize:
                    shouldContinue = False
            finalSize = fileSize
        if shouldContinue:
            logger.info("Waiting for file %s" % filePath)
            #
            timeStart = time.time()
            while shouldContinue and not hasTimedOut:
                # Sleep 1 s
                time.sleep(1)
                if os.name != 'nt' and fileDir.exists():
                    # Patch provided by Sebastien 2018/02/09 for forcing NFS cache:
                    logger.debug("NFS cache clear, doing os.fstat on directory {0}".format(fileDir))
                    d = os.open(fileDir.as_posix(), os.O_DIRECTORY)
                    statResult = os.fstat(d)
                    logger.debug("Results of os.fstat: {0}".format(statResult))
                timeElapsed = time.time() - timeStart
                # Check if time out
                if timeElapsed > timeOut:
                    hasTimedOut = True
                    strWarning = "Timeout while waiting for file %s" % filePath
                    logger.warning(strWarning)
                else:
                    # Check if file is there
                    if filePath.exists():
                        fileSize = filePath.stat().st_size
                        if expectedSize is not None:
                            # Check that it has right size
                            if fileSize > expectedSize:
                                shouldContinue = False
                        else:
                            shouldContinue = False
                        finalSize = fileSize
        outData = {
            "timedOut": hasTimedOut
        }
        if finalSize is not None:
            outData["finalSize"] = finalSize
        return outData

