#
# Copyright (c) European Synchrotron Radiation Facility (ESRF)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the 'Software'), to deal in
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

# Corresponding EDNA code:
# https://github.com/olofsvensson/edna-mx
# mxPluginExec/plugins/EDPluginGroupISPyB-v1.4/plugins/
#     EDPluginISPyBRetrieveDataCollectionv1_4.py


from suds.client import Client
from suds.transport.http import HttpAuthenticated

import os
import pathlib

from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging
from edna2.utils import UtilsIspyb

from edna2.tasks.AbstractTask import AbstractTask

logger = UtilsLogging.getLogger()


class ISPyBRetrieveDataCollection(AbstractTask):

    def run(self, inData):
        dictConfig = UtilsConfig.getTaskConfig('ISPyB')
        username = dictConfig['username']
        password = dictConfig['password']
        httpAuthenticated = HttpAuthenticated(username=username,
                                              password=password)
        wdsl = dictConfig['ispyb_ws_url'] + '/ispybWS/ToolsForCollectionWebService?wsdl'
        client = Client(wdsl, transport=httpAuthenticated, cache=None)
        if 'image' in inData:
            path = pathlib.Path(inData['image'])
            indir = path.parent.as_posix()
            infilename = path.name
            dataCollection = client.service.findDataCollectionFromFileLocationAndFileName(
                indir,
                infilename
            )
        elif 'dataCollectionId' in inData:
            dataCollectionId = inData['dataCollectionId']
            dataCollection = client.service.findDataCollection(dataCollectionId)
        else:
            errorMessage = 'Neither image nor data collection id given as input!'
            logger.error(errorMessage)
            raise BaseException(errorMessage)
        if dataCollection is not None:
            outData = Client.dict(dataCollection)
        else:
            outData = {}
        return outData


class GetListAutoprocIntegration(AbstractTask):

    def getInDataSchema(self):
        return {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "proposal": {"type": "string"},
                "dataCollectionId": {"type": "integer"}
            }
        }

    def getOutDataSchema(self):
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "AutoProcIntegration_autoProcIntegrationId": {"type": "integer"}
                }
            }
        }

    def run(self, inData):
        # urlExtISPyB, token, proposal, dataCollectionId
        token = inData['token']
        proposal = inData['proposal']
        dataCollectionId = inData['dataCollectionId']
        dictConfig = UtilsConfig.getTaskConfig('ISPyB')
        restUrl = dictConfig['ispyb_ws_url'] + '/rest'
        ispybWebServiceURL = os.path.join(
            restUrl, token, 'proposal', str(proposal), 'mx',
            'autoprocintegration', 'datacollection', str(dataCollectionId),
            'view')
        outData = UtilsIspyb.getJsonFromURL(ispybWebServiceURL)
        return outData


class GetListAutoprocAttachment(AbstractTask):

    def getInDataSchema(self):
        return {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "proposal": {"type": "string"},
                "autoProcProgramId": {"type": "integer"}
            }
        }

    def getOutDataSchema(self):
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "AutoProcIntegration_autoProcIntegrationId": {"type": "integer"}
                }
            }
        }

    def run(self, inData):
        # urlExtISPyB, token, proposal, autoProcProgramId
        token = inData['token']
        proposal = inData['proposal']
        autoProcProgramId = inData['autoProcProgramId']
        dictConfig = UtilsConfig.getTaskConfig('ISPyB')
        restUrl = dictConfig['ispyb_ws_url'] + '/rest'
        ispybWebServiceURL = os.path.join(
            restUrl, token, 'proposal', str(proposal), 'mx',
            'autoprocintegration', 'attachment', 'autoprocprogramid',
            str(autoProcProgramId), 'list')
        outData = UtilsIspyb.getJsonFromURL(ispybWebServiceURL)
        return outData
