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

__authors__ = ['O. Svensson']
__license__ = 'MIT'
__date__ = '21/04/2019'

# Corresponding EDNA code:
# https://github.com/olofsvensson/edna-mx
# mxv1/src/EDHandlerESRFPyarchv1_0.py

import os
import pathlib
import tempfile

from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

logger = UtilsLogging.getLogger()


def getWorkingDirectory(task, inData):
    parentDirectory = inData.get('workingDirectory', None)
    if parentDirectory is None:
        parentDirectory = os.getcwd()
    workingDirectory = tempfile.mkdtemp(
        prefix=task.__class__.__name__ + '_',
        dir=parentDirectory)
    return pathlib.Path(workingDirectory)


def createPyarchFilePath(filePath):
    """
    This method translates from an ESRF "visitor" path to a "pyarch" path:
    /data/visitor/mx415/id14eh1/20100209 -> /data/pyarch/2010/id14eh1/mx415/20100209
    """
    pyarchFilePath = None
    if isinstance(filePath, str):
        filePath = pathlib.Path(filePath)
    listOfDirectories = filePath.parts
    if UtilsConfig.isEMBL():
        if 'p13' in listOfDirectories[0:3] or 'P13' in listOfDirectories[0:3]:
            pyarchFilePath = os.path.join('/data/ispyb/p13',
                                          *listOfDirectories[4:])
        else:
            pyarchFilePath = os.path.join('/data/ispyb/p14',
                                          *listOfDirectories[4:])
        return pyarchFilePath
    listBeamlines = ['bm30a', 'id14eh1', 'id14eh2', 'id14eh3', 'id14eh4',
                     'id23eh1', 'id23eh2', 'id29', 'id30a1',
                     'id30a2', 'id30a3', 'id30b']
    # Check that we have at least four levels of directories:
    if len(listOfDirectories) > 5:
        dataDirectory = listOfDirectories[1]
        secondDirectory = listOfDirectories[2]
        thirdDirectory = listOfDirectories[3]
        fourthDirectory = listOfDirectories[4]
        fifthDirectory = listOfDirectories[5]
        year = fifthDirectory[0:4]
        proposal = None
        beamline = None
        if dataDirectory == 'data' and secondDirectory == 'gz':
            if thirdDirectory == 'visitor':
                proposal = fourthDirectory
                beamline = fifthDirectory
            elif fourthDirectory == 'inhouse':
                proposal = fifthDirectory
                beamline = thirdDirectory
            else:
                raise RuntimeError(
                    'Illegal path for UtilsPath.createPyarchFilePath: ' +
                    '{0}'.format(filePath))
            listOfRemainingDirectories = listOfDirectories[6:]
        elif dataDirectory == 'data' and secondDirectory == 'visitor':
            proposal = listOfDirectories[3]
            beamline = listOfDirectories[4]
            listOfRemainingDirectories = listOfDirectories[5:]
        elif dataDirectory == 'data' and secondDirectory in listBeamlines:
            beamline = secondDirectory
            proposal = listOfDirectories[4]
            listOfRemainingDirectories = listOfDirectories[5:]
        if proposal is not None and beamline is not None:
            pyarchFilePath = pathlib.Path('/data/pyarch') / year / beamline
            pyarchFilePath = pyarchFilePath / proposal
            for directory in listOfRemainingDirectories:
                pyarchFilePath = pyarchFilePath / directory
    if pyarchFilePath is None:
        logger.warning(
            'UtilsPath.createPyarchFilePath: path not converted for' +
            ' pyarch: %s ' % filePath)
    else:
        pyarchFilePath = pyarchFilePath.as_posix()
    return pyarchFilePath
