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
__date__ = "10/05/2019"

import shutil
import pprint

from edna2.tasks.AbstractTask import AbstractTask
from edna2.tasks.ISPyBTasks import GetListAutoprocessingResults


class FindHklAsciiForMerge(AbstractTask):
    """
    This task receives a list of data collection IDs and returns a
    json schema for EXI2
    """

    def getInDataSchema(self):
        return {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "proposal": {"type": "string"},
                "dataCollectionId": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                    }
                }
            }
        }

    # def getOutDataSchema(self):
    #     return {
    #         "type": "object",
    #         "required": ["dataForMerge"],
    #         "properties": {
    #             "dataForMerge": {
    #                 "type": "object",
    #                 "items": {
    #                     "type": "object",
    #                     "properties": {
    #                         "spaceGroup": {"type": "string"}
    #                     }
    #                 }
    #             }
    #         }
    #     }

    def run(self, inData):
        token = inData['token']
        proposal = inData['proposal']
        listDataCollectionId = inData['dataCollectionId']
        inDataGetListAutoprocessingResults = {
            'token': token,
            'proposal': proposal,
            'dataCollectionId': listDataCollectionId
        }
        getListAutoprocessingResults = GetListAutoprocessingResults(
            inData=inDataGetListAutoprocessingResults
        )
        getListAutoprocessingResults.execute()
        outDataGetListAutoprocessingResults = getListAutoprocessingResults.outData
        index = 1
        properties = {}
        listOrder = []
        for dataCollection in outDataGetListAutoprocessingResults['dataCollection']:
            dataCollectionId = dataCollection['dataCollectionId']
            dictEntry = {}
            listEnumNames = []
            listEnumValues = []
            proteinAcronym = None
            blSampleName = None
            for autoProcResult in dataCollection['autoprocIntegration']:
                if proteinAcronym is None:
                    proteinAcronym = autoProcResult['Protein_acronym']
                    blSampleName = autoProcResult['BLSample_name']
                for autoProcAttachment in autoProcResult['autoprocAttachment']:
                    if 'XDS_ASCII' in autoProcAttachment['fileName']:
                        fileName = autoProcAttachment['fileName']
                        program = autoProcResult['v_datacollection_processingPrograms']
                        attachmentId = autoProcAttachment['autoProcProgramAttachmentId']
                        enumName = '{0:30s} {1}'.format(program, fileName)
                        listEnumNames.append(enumName)
                        enumValue = attachmentId
                        listEnumValues.append(enumValue)
            dictEntry['title'] = 'Select HKL for data Collection #{0} {2} {1}-{2}'.format(
                index,
                proteinAcronym,
                blSampleName
            )
            dictEntry['enum'] = listEnumValues
            dictEntry['enumNames'] = listEnumNames
            entryKey = 'hkl_'+str(dataCollectionId)
            properties[entryKey] = dictEntry
            listOrder.append(entryKey)
            # Minimum sigma
            entryKey = 'minimum_I/SIGMA_' + str(dataCollectionId)
            dictEntry = {
                'integer': 'string',
                'type': 'string',
                'title': 'minimum_I/SIGMA for data Collection #{0} {2} {1}-{2}'.format(
                    index,
                    proteinAcronym,
                    blSampleName
                )
            }
            properties[entryKey] = dictEntry
            listOrder.append(entryKey)
            index += 1
        schema = {
            'properties': properties,
            'type': 'object',
            'title': 'User input needed'
        }
        uiSchema = {
            'ui:order': listOrder
        }
        outData = {
            "schema": schema,
            "uiSchema": uiSchema
        }
        return outData


class MergeUtls(AbstractTask):
    """
    This task will run the Merge_utls.py program written by Shibom Basu
    """

    def run(self, inData):
        listHklLp = inData['listHklLp']
        workingDir = self.getWorkingDirectory()
        index = 1
        for hklLp in listHklLp:
            dataDir = workingDir / "data{0}".format(index)
            dataDir.mkdir(exist_ok=True)
            shutil.copy(hklLp['hkl'], str(dataDir / 'XDS_ASCII.HKL'))
            index += 1
        commandLine = 'Merge_utls.py --root {0} --expt serial-xtal'.format(str(workingDir))
        self.runCommandLine(commandLine, logPath=None)
        outData = {}
        return outData


