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
__date__ = "14/04/2020"


from edna2.tasks.AbstractTask import AbstractTask
from edna2.tasks.ReadImageHeader import ReadImageHeader
from edna2.tasks.DozorTasks import ControlDozor
from edna2.tasks.XDSTasks import XDSIndexingTask


class ControlIndexingTask(AbstractTask):
    """
    This task receives a list of images or data collection ids and
    returns result of indexing
    """

    def getInDataSchema(self):
        return {
            "type": "object",
            "properties": {
                "dataCollectionId": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                    }
                },
                "imagePath": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    }
                }
            }
        }

    def run(self, inData):
        # First get the list of subWedges
        listSubWedge = self.getListSubWedge(inData)
        # Get list of spots from Dozor
        listDozorSpotFile = []
        for subWedge in listSubWedge:
            listSubWedgeImage = subWedge['image']
            for image in listSubWedgeImage:
                # listImage.append(image['path'])
                inDataControlDozor = {
                    'image': [image['path']]
                }
                controlDozor = ControlDozor(inData=inDataControlDozor)
                controlDozor.execute()
                if controlDozor.isSuccess():
                    dozorSpotFile = controlDozor.outData["imageQualityIndicators"][0]["dozorSpotFile"]
                    listDozorSpotFile.append(dozorSpotFile)
        imageDict = listSubWedge[0]
        imageDict["dozorSpotFile"] = listDozorSpotFile
        xdsIndexinInData = {
            "image": [imageDict]
        }
        xdsIndexingTask = XDSIndexingTask(inData=xdsIndexinInData)
        xdsIndexingTask.execute()
        outData = {
            "subWedge": listSubWedge
        }
        return outData

    @staticmethod
    def getListSubWedge(inData):
        listSubWedge = None
        # First check if we have data collection ids or image list
        if "dataCollectionId" in inData:
            # TODO: get list of data collections from ISPyB
            raise RuntimeError("Not implemented!")
        elif "imagePath" in inData:
            listSubWedge = ControlIndexingTask.readImageHeaders(inData["imagePath"])
        else:
            raise RuntimeError("No dataCollectionId or imagePath in inData")
        return listSubWedge

    @staticmethod
    def readImageHeaders(listImagePath):
        # Read the header(s)
        listSubWedge = []
        for imagePath in listImagePath:
            inDataReadImageHeader = {
                "image": imagePath
            }
            readImageHeader = ReadImageHeader(inData=inDataReadImageHeader)
            readImageHeader.execute()
            subWedge = readImageHeader.outData["subWedge"]
            listSubWedge += subWedge
        return listSubWedge
