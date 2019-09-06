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

import pprint

from edna2.tasks.AbstractTask import AbstractTask
from edna2.tasks.ISPyBTasks import GetListAutoprocIntegration
from edna2.tasks.ISPyBTasks import GetListAutoprocAttachment

class FindDataForMerge(AbstractTask):
    """
    This task receives a list of data collection IDs and returns a list
    of dictionaries with all the XDS.ASCII results
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
        dataForMerge = {}
        for dataCollectionId in listDataCollectionId:
            inDataGetListIntegration = {
                'token': token,
                'proposal': proposal,
                'dataCollectionId': dataCollectionId
            }
            getListAutoprocIntegration = GetListAutoprocIntegration(
                inData=inDataGetListIntegration
            )
            getListAutoprocIntegration.setPersistInOutData(False)
            getListAutoprocIntegration.execute()
            listAutoprocIntegration = getListAutoprocIntegration.outData
            # Get v_datacollection_summary_phasing_autoProcProgramId
            for autoprocIntegration in listAutoprocIntegration:
                if 'v_datacollection_summary_phasing_autoProcProgramId' in autoprocIntegration:
                    autoProcProgramId = autoprocIntegration[
                        'v_datacollection_summary_phasing_autoProcProgramId'
                    ]
                    inDataGetListAttachment = {
                        'token': token,
                        'proposal': proposal,
                        'autoProcProgramId': autoProcProgramId
                    }
                    getListAutoprocAttachment = GetListAutoprocAttachment(
                        inData=inDataGetListAttachment
                    )
                    getListAutoprocAttachment.setPersistInOutData(False)
                    getListAutoprocAttachment.execute()
                    listAutoprocAttachment = getListAutoprocAttachment.outData
                    for attachment in listAutoprocAttachment:
                        fileName = attachment['fileName']
                        if 'XDS_ASCII.HKL' in fileName:
                            program = autoprocIntegration[
                                'v_datacollection_processingPrograms'
                            ]
                            if program not in dataForMerge:
                                dataForMerge[program] = []
                            dataForMerge[program].append({
                                'autoprocIntegration': autoprocIntegration,
                                'attachment': attachment
                            })
        outData = {'dataForMerge': dataForMerge}
        return outData
