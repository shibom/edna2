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
import json
import pathlib
import traceback
import jsonschema
import subprocess
import multiprocessing

from edna2.utils import UtilsPath
from edna2.utils import UtilsLogging

logger = UtilsLogging.getLogger()


class EDNA2Process(multiprocessing.Process):
    """
    See https://stackoverflow.com/a/33599967.
    """

    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._cconn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._cconn.send((e, tb))
        return

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception


class AbstractTask(object):
    """
    Parent task to all EDNA2 tasks.
    """
    def __init__(self, inData):
        self._dictInOut = multiprocessing.Manager().dict()
        self._dictInOut['inData'] = json.dumps(inData, default=str)
        self._dictInOut['outData'] = json.dumps({})
        self._dictInOut['isFailure'] = False
        self._process = EDNA2Process(target=self.executeRun, args=())
        self._workingDirectory = None
        self._logFileName = None
        self._schemaPath = pathlib.Path(__file__).parents[1] / 'schema'
        self._persistInOutData = True
        self._oldDir = os.getcwd()

    def getSchemaUrl(self, schemaName):
        return 'file://' + str(self._schemaPath / schemaName)

    def executeRun(self):
        inData = self.getInData()
        hasValidInDataSchema = False
        hasValidOutDataSchema = False
        if self.getInDataSchema() is not None:
            instance = inData
            schema = self.getInDataSchema()
            try:
                jsonschema.validate(instance=instance, schema=schema)
                hasValidInDataSchema = True
            except Exception as e:
                logger.exception(e)
        else:
            hasValidInDataSchema = True
        if hasValidInDataSchema:
            self._workingDirectory = UtilsPath.getWorkingDirectory(self, inData)
            self.writeInputData(inData)
            self._oldDir = os.getcwd()
            os.chdir(str(self._workingDirectory))
            outData = self.run(inData)
            os.chdir(self._oldDir)
        else:
            raise RuntimeError("Schema validation error for inData")
        if self.getOutDataSchema() is not None:
            instance = outData
            schema = self.getOutDataSchema()
            try:
                jsonschema.validate(instance=instance, schema=schema)
                hasValidOutDataSchema = True
            except Exception as e:
                logger.exception(e)
        else:
            hasValidOutDataSchema = True
        if hasValidOutDataSchema:
            self.writeOutputData(outData)
        else:
            raise RuntimeError("Schema validation error for outData")
        if not os.listdir(str(self._workingDirectory)):
            os.rmdir(str(self._workingDirectory))

    def getInData(self):
        return json.loads(self._dictInOut['inData'])

    def setInData(self, inData):
        self._dictInOut['inData'] = json.dumps(inData, default=str)
    inData = property(getInData, setInData)

    def getOutData(self):
        return json.loads(self._dictInOut['outData'])

    def setOutData(self, outData):
        self._dictInOut['outData'] = json.dumps(outData, default=str)
    outData = property(getOutData, setOutData)

    def writeInputData(self, inData):
        # Write input data
        if self._persistInOutData and self._workingDirectory is not None:
            jsonName = "inData" + self.__class__.__name__ + ".json"
            with open(str(self._workingDirectory / jsonName), 'w') as f:
                f.write(json.dumps(inData, default=str, indent=4))

    def writeOutputData(self, outData):
        self.setOutData(outData)
        if self._persistInOutData and self._workingDirectory is not None:
            jsonName = "outData" + self.__class__.__name__ + ".json"
            with open(str(self._workingDirectory / jsonName), 'w') as f:
                f.write(json.dumps(outData, default=str, indent=4))

    def getLogPath(self):
        if self._logFileName is None:
            self._logFileName = self.__class__.__name__ + ".log.txt"
        logPath = self._workingDirectory / self._logFileName
        return logPath

    def setLogFileName(self, logFileName):
        self._logFileName = logFileName

    def getLogFileName(self):
        return self._logFileName

    def getLog(self):
        with open(str(self.getLogPath())) as f:
            log = f.read()
        return log

    def runCommandLine(self, commandLine, logPath=None, listCommand=None,
                       ignoreErrors=False):
        if listCommand is not None:
            commandLine += ' << EOF-EDNA2\n'
            for command in listCommand:
                commandLine += command + '\n'
            commandLine += "EOF-EDNA2"
        commandLogFileName = self.__class__.__name__ + ".commandLine.txt"
        commandLinePath = self._workingDirectory / commandLogFileName
        with open(str(commandLinePath), 'w') as f:
            f.write(commandLine)
        pipes = subprocess.Popen(
            commandLine,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            cwd=str(self._workingDirectory)
        )
        stdout, stderr = pipes.communicate()
        if len(stdout) > 0:
            log = str(stdout, 'utf-8')
            if logPath is None:
                logPath = self.getLogPath()
            with open(str(logPath), 'w') as f:
                f.write(log)
        if len(stderr) > 0:
            if not ignoreErrors:
                logger.warning("Error messages from command {0}".format(
                    commandLine.split(' ')[0])
                )
            errorLogFileName = self.__class__.__name__ + ".err.txt"
            errorLogPath = self._workingDirectory / errorLogFileName
            with open(str(errorLogPath), 'w') as f:
                f.write(str(stderr, 'utf-8'))
        if pipes.returncode != 0:
            # Error!
            errorMessage = "{0}, code {1}".format(stderr, pipes.returncode)
            raise RuntimeError(errorMessage)

    def onError(self):
        pass

    def start(self):
        self._process.start()

    def join(self):
        self._process.join()
        if self._process.exception:
            error, trace = self._process.exception
            logger.error(error)
            logger.error(trace)
            self._dictInOut['isFailure'] = True
            self.onError()

    def execute(self):
        self.start()
        self.join()

    def setFailure(self):
        self._dictInOut['isFailure'] = True

    def isFailure(self):
        return self._dictInOut['isFailure']

    def isSuccess(self):
        return not self.isFailure()

    def getWorkingDirectory(self):
        return self._workingDirectory

    def setWorkingDirectory(self, inData):
        self._workingDirectory = UtilsPath.getWorkingDirectory(self, inData)

    def getInDataSchema(self):
        return None

    def getOutDataSchema(self):
        return None

    def setPersistInOutData(self, value):
        self._persistInOutData = value
