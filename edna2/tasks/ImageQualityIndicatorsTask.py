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

# Corresponding EDNA code:
# https://github.com/olofsvensson/edna-mx
# mxv1/plugins/EDPluginControlImageQualityIndicators-v1.4/plugins/
#      EDPluginControlImageQualityIndicatorsv1_4.py

import os
import time
import numpy
import base64
import pathlib


from edna2.tasks.AbstractTask import AbstractTask
from edna2.tasks.WaitFileTask import WaitFileTask
from edna2.tasks.DozorTasks import ControlDozor
from edna2.tasks.H5ToCBFTask import H5ToCBFTask
try:
    from edna2.tasks.CrystfelTasks import ExeCrystFEL
    crystFelImportFailed = False
except ImportError:
    crystFelImportFailed = True

from edna2.utils import UtilsImage
from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

logger = UtilsLogging.getLogger()

DEFAULT_MIN_IMAGE_SIZE = 1000000
DEFAULT_WAIT_FILE_TIMEOUT = 120


class ImageQualityIndicatorsTask(AbstractTask):
    """
    This task controls the plugins that generate image quality indicators.
    """

    def getInDataSchema(self):
        return {
            "type": "object",
            "properties": {
                "doDistlSignalStrength": {"type": "boolean"},
                "doIndexing": {"type": "boolean"},
                "doCrystfel": {"type": "boolean"},
                "doUploadToIspyb": {"type": "boolean"},
                "processDirectory": {"type": "string"},
                "image": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "batchSize": {"type": "integer"},
                "fastMesh": {"type": "boolean"},
                "wedgeNumber": {"type": "integer"},
                "directory": {"type": "string"},
                "template": {"type": "string"},
                "startNo": {"type": "integer"},
                "endNo": {"type": "integer"},
            }
        }

    def getOutDataSchema(self):
        return {
            "type": "object",
            "required": ["imageQualityIndicators"],
            "properties": {
                "imageQualityIndicators": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["number", "angle", "spotsNumOf",
                                     "spotsIntAver", "spotsResolution",
                                     "mainScore", "spotScore",
                                     "visibleResolution"],
                        "properties": {
                            "dozor_score": {"type": "number"},
                            "dozorSpotFile": {"type": "string"},
                            "dozorSpotList": {"type": "string"},
                            "dozorSpotListShape": {
                                "type": "array",
                                "items": {
                                    "type": "integer",
                                }
                            },
                            "dozorSpotsIntAver": {"type": "number"},
                            "dozorSpotsResolution": {"type": "number"},
                            "dozorVisibleResolution": {"type": "number"},
                            "binPopCutOffMethod2Res": {"type": "number"},
                            "goodBraggCandidates": {"type": "integer"},
                            "iceRings": {"type": "integer"},
                            "image": {"type": "string"},
                            "inResTotal": {"type": "integer"},
                            "inResolutionOvrlSpots": {"type": "integer"},
                            "maxUnitCell": {"type": "number"},
                            "method1Res": {"type": "number"},
                            "method2Res": {"type": "number"},
                            "pctSaturationTop50Peaks": {"type": "number"},
                            "saturationRangeAverage": {"type": "number"},
                            "saturationRangeMax": {"type": "number"},
                            "saturationRangeMin": {"type": "number"},
                            "selectedIndexingSolution": {"type": "number"},
                            "signalRangeAverage": {"type": "number"},
                            "signalRangeMax": {"type": "number"},
                            "signalRangeMin": {"type": "number"},
                            "spotTotal": {"type": "integer"},
                            "totalIntegratedSignal": {"type": "number"},
                        },
                    },
                },
                "inputDozor": {"type": "number"},
            },
        }

    def run(self, inData):
        batchSize = inData.get('batchSize', 1)
        doDistlSignalStrength = inData.get('doDistlSignalStrength', False)
        doIndexing = inData.get('doIndexing', False)
        if crystFelImportFailed:
            doCrystfel = False
        else:
            doCrystfel = inData.get('doCrystfel', False)
        isFastMesh = inData.get('fastMesh', False)
        # Loop through all the incoming reference images
        listImage = inData.get('image', [])
        if len(listImage) == 0:
            directory = pathlib.Path(inData['directory'])
            template = inData['template']
            startNo = inData['startNo']
            endNo = inData['endNo']
            listImage = []
            for index in range(startNo, endNo + 1):
                imageName = template.replace("####", "{0:04d}".format(index))
                imagePath = directory / imageName
                listImage.append(str(imagePath))
        outData = dict()
        listImageQualityIndicators = []
        listcrystfel_output = []
        inDataWaitFile = {}
        listDistlTask = []
        listDozorTask = []
        listOfImagesInBatch = []
        listOfAllBatches = []
        indexBatch = 0
        listH5FilePath = []
        # Configurations
        minImageSize = UtilsConfig.get(
            self, 'minImageSize', defaultValue=DEFAULT_MIN_IMAGE_SIZE)
        waitFileTimeOut = UtilsConfig.get(
            self, 'waitFileTimeOut', defaultValue=DEFAULT_WAIT_FILE_TIMEOUT)
        # Process data in batches
        for image in listImage:
            listOfImagesInBatch.append(pathlib.Path(image))
            if len(listOfImagesInBatch) == batchSize:
                listOfAllBatches.append(listOfImagesInBatch)
                listOfImagesInBatch = []
        if len(listOfImagesInBatch) > 0:
            listOfAllBatches.append(listOfImagesInBatch)
            listOfImagesInBatch = []
        # Loop over batches
        for listOfImagesInBatch in listOfAllBatches:
            # First wait for images
            for imagePath in listOfImagesInBatch:
                # If Eiger, just wait for the h5 file
                if imagePath.suffix == '.h5':
                    h5MasterFilePath, h5DataFilePath, hdf5ImageNumber = \
                        self.getH5FilePath(imagePath,
                                           batchSize=batchSize,
                                           isFastMesh=isFastMesh)
                    if not h5DataFilePath in listH5FilePath:
                        logger.info("Eiger data, waiting for master" +
                                    " and data files...")
                        listH5FilePath.append(h5DataFilePath)
                        inDataWaitFileTask = {
                            'file': str(h5DataFilePath),
                            'size': minImageSize,
                            'timeOut': waitFileTimeOut
                        }
                        waitFileTask = WaitFileTask(inData=inDataWaitFileTask)
                        logger.info("Waiting for file {0}".format(h5DataFilePath))
                        logger.debug("Wait file timeOut set to %f" % waitFileTimeOut)
                        waitFileTask.execute()
                    #     #                    hdf5FilePath = strPathToImage.replace(".cbf", ".h5")
                        time.sleep(1)
                    if not os.path.exists(h5DataFilePath):
                        strError = "Time-out while waiting for image %s" % h5DataFilePath
                        self.error(strError)
                        self.addErrorMessage(strError)
                        self.setFailure()
                else:
                    if not imagePath.exists():
                        logger.info("Waiting for file {0}".format(imagePath))
                        inDataWaitFileTask = {
                            'file': str(imagePath),
                            'size': minImageSize,
                            'timeOut': waitFileTimeOut
                        }
                        waitFileTask = WaitFileTask(inData=inDataWaitFileTask)
                        logger.debug("Wait file timeOut set to %.0f s" % waitFileTimeOut)
                        waitFileTask.execute()
                    if not imagePath.exists():
                        errormessage = "Time-out while waiting for image "+ \
                                       str(imagePath)
                        logger.error(errormessage)
                        self.setFailure()
            if not self.isFailure():
                pathToFirstImage = listOfImagesInBatch[0]
                directory = pathToFirstImage.parent
                firstImage = UtilsImage.getImageNumber(listOfImagesInBatch[0])
                lastImage = UtilsImage.getImageNumber(listOfImagesInBatch[-1])
                inDataH5ToCBF = {
                    'hdf5File': listOfImagesInBatch[0],
                    'hdf5ImageNumber': 1,
                    'startImageNumber': firstImage,
                    'endImageNumber': lastImage,
                    'forcedOutputDirectory': directory
                }
                h5ToCBFTask = H5ToCBFTask(inData=inDataH5ToCBF)
                h5ToCBFTask.execute()
                if h5ToCBFTask.isSuccess():
                    outputCBFFileTemplate = h5ToCBFTask.outData['outputCBFFileTemplate']
                    if outputCBFFileTemplate is not None:
                        lastCbfFile = outputCBFFileTemplate.replace("######", "{0:06d}".format(
                            UtilsImage.getImageNumber(listOfImagesInBatch[-1])))
                        strPathToImage = os.path.join(directory, lastCbfFile)
    #                     #                        print(cbfFile.path.value)
                        if os.path.exists(strPathToImage):
                            # Rename all images
                            oldListOfImagesInBatch = listOfImagesInBatch
                            listOfImagesInBatch = []
                            for imagePathH5 in oldListOfImagesInBatch:
                                imagePathCbf = pathlib.Path(str(imagePathH5).replace('.h5', '.cbf'))
                                listOfImagesInBatch.append(imagePathCbf)
                                imageNumber = UtilsImage.getImageNumber(imagePathCbf)
                                oldPath = directory / outputCBFFileTemplate.replace('######',
                                                                                    '{0:06d}'.format(imageNumber))
                                newPath = directory / outputCBFFileTemplate.replace('######',
                                                                                    '{0:04d}'.format(imageNumber))
                                os.rename(oldPath, newPath)
                            lastCbfFile = outputCBFFileTemplate.replace(
                                '######',
                                '{0:04d}'.format(UtilsImage.getImageNumber(listOfImagesInBatch[-1])))
                            pathToLastImage = directory / lastCbfFile
                            logger.info("Image has been converted to CBF file: {0}".format(pathToLastImage))


                for image in listOfImagesInBatch:
                    distlTask = None
                    # Check if we should run distl.signalStrength
                    if doDistlSignalStrength:
                        raise RuntimeError("not yet implemented...")
                        # if self.bUseThinClient:
                        #     strPluginName = self.strPluginNameThinClient
                        # else:
                        #     strPluginName = self.strPluginName
                        # edPluginPluginExecImageQualityIndicator = self.loadPlugin(strPluginName)
                        # self.listPluginExecImageQualityIndicator.append(edPluginPluginExecImageQualityIndicator)
                        # xsDataInputDistlSignalStrength = XSDataInputDistlSignalStrength()
                        # xsDataInputDistlSignalStrength.setReferenceImage(xsDataImageNew)
                        # edPluginPluginExecImageQualityIndicator.setDataInput(xsDataInputDistlSignalStrength)
                        # edPluginPluginExecImageQualityIndicator.execute()
                    listDistlTask.append((image, distlTask))
                inDataControlDozor = {
                    'image': listOfImagesInBatch,
                    'batchSize': len(listOfImagesInBatch)
                }
                controlDozor = ControlDozor(inDataControlDozor)
                controlDozor.start()
                listDozorTask.append((controlDozor, inDataControlDozor, list(listOfImagesInBatch)))

        if not self.isFailure():
            listIndexing = []
            # Synchronize all image quality indicator plugins and upload to ISPyB
        #     xsDataInputStoreListOfImageQualityIndicators = XSDataInputStoreListOfImageQualityIndicators()
        #
        #     for (xsDataImage, edPluginPluginExecImageQualityIndicator) in listPluginDistl:
        #         xsDataImageQualityIndicators = XSDataImageQualityIndicators()
        #         xsDataImageQualityIndicators.image = xsDataImage.copy()
        #         if edPluginPluginExecImageQualityIndicator is not None:
        #             edPluginPluginExecImageQualityIndicator.synchronize()
        #             if edPluginPluginExecImageQualityIndicator.dataOutput is not None:
        #                 if edPluginPluginExecImageQualityIndicator.dataOutput.imageQualityIndicators is not None:
        #                     xsDataImageQualityIndicators = XSDataImageQualityIndicators.parseString( \
        #                         edPluginPluginExecImageQualityIndicator.dataOutput.imageQualityIndicators.marshal())
        #         self.xsDataResultControlImageQualityIndicators.addImageQualityIndicators(xsDataImageQualityIndicators)
        #
            for (controlDozor, inDataControlDozor, listBatch) in listDozorTask:
                controlDozor.join()
                # Check that we got at least one result
                if len(controlDozor.outData['imageDozor']) == 0:
                    # Run the dozor plugin again, this time synchronously
                    firstImage = listBatch[0].name
                    lastImage = listBatch[-1].name
                    logger.warning("No dozor results! Re-executing Dozor for" +
                                   " images {0} to {1}".format(firstImage, lastImage))
                    time.sleep(5)
                    controlDozor = ControlDozor(inDataControlDozor)
                    controlDozor.execute()
                listImageDozor = list(controlDozor.outData['imageDozor'])
                for imageDozor in listImageDozor:
                    for imagePath, distlTask in listDistlTask:
                        if imageDozor['image'] == str(imagePath):
        #                     xsDataImageQualityIndicators.dozor_score = imageDozor.mainScore
        #                     xsDataImageQualityIndicators.dozorSpotFile = imageDozor.spotFile
                            if 'spotFile' in imageDozor and imageDozor['spotFile'] is not None:
                                if os.path.exists(imageDozor['spotFile']):
                                    numpyArray = numpy.loadtxt(imageDozor['spotFile'], skiprows=3)
                                    imageDozor['dozorSpotList'] = base64.b64encode(numpyArray.tostring()).decode('utf-8')
                                    imageDozor['dozorSpotListShape'] = list(numpyArray.shape)

                listImageQualityIndicators += listImageDozor

                if doCrystfel:
                    # a work around as autocryst module works with only json file/string
                    inDataCrystFEL = {'imageQualityIndicators': listImageDozor}
                    crystfel = ExeCrystFEL(inData=inDataCrystFEL)
                    cryst_result_out = crystfel.run(inDataCrystFEL)
                    if not crystfel.isFailure():
                        listcrystfel_output.append(cryst_result_out)
                        # listImageQualityIndicators += listcrystfel_output


        #                     xsDataImageQualityIndicators.dozorSpotsIntAver = imageDozor.spotsIntAver
        #                     xsDataImageQualityIndicators.dozorSpotsResolution = imageDozor.spotsResolution
        #                     xsDataImageQualityIndicators.dozorVisibleResolution = imageDozor.visibleResolution
        #                     if self.xsDataResultControlImageQualityIndicators.inputDozor is None:
        #                         if edPluginControlDozor.dataOutput.inputDozor is not None:
        #                             self.xsDataResultControlImageQualityIndicators.inputDozor = XSDataDozorInput().parseString(
        #                                 edPluginControlDozor.dataOutput.inputDozor.marshal())
        #         if self.dataInput.doUploadToIspyb is not None and self.dataInput.doUploadToIspyb.value:
        #             xsDataISPyBImageQualityIndicators = \
        #                 XSDataISPyBImageQualityIndicators.parseString(xsDataImageQualityIndicators.marshal())
        #             xsDataInputStoreListOfImageQualityIndicators.addImageQualityIndicators(
        #                 xsDataISPyBImageQualityIndicators)
        #     #        print xsDataInputStoreListOfImageQualityIndicators.marshal()
        #     if self.dataInput.doUploadToIspyb is not None and self.dataInput.doUploadToIspyb.value:
        #         self.edPluginISPyB = self.loadPlugin(self.strISPyBPluginName)
        #         self.edPluginISPyB.dataInput = xsDataInputStoreListOfImageQualityIndicators
        #         self.edPluginISPyB.execute()
        #     #
        #     if bDoIndexing:
        #         # Find the 5 most intensive images (TIS):
        #         listImage = []
        #         # Check that we have dozor_score from all images:
        #         has_dozor_score = True
        #         for imageQualityIndicators in self.xsDataResultControlImageQualityIndicators.imageQualityIndicators:
        #             if imageQualityIndicators.dozor_score is None:
        #                 has_dozor_score = False
        #         if has_dozor_score:
        #             listSorted = sorted(self.xsDataResultControlImageQualityIndicators.imageQualityIndicators,
        #                                 key=lambda imageQualityIndicators: imageQualityIndicators.dozor_score.value)
        #         else:
        #             listSorted = sorted(self.xsDataResultControlImageQualityIndicators.imageQualityIndicators,
        #                                 key=lambda
        #                                     imageQualityIndicators: imageQualityIndicators.totalIntegratedSignal.value)
        #         for xsDataResultControlImageQualityIndicator in listSorted[-5:]:
        #             if xsDataResultControlImageQualityIndicator.dozor_score.value > 1:
        #                 xsDataInputReadImageHeader = XSDataInputReadImageHeader()
        #                 xsDataInputReadImageHeader.image = XSDataFile(
        #                     xsDataResultControlImageQualityIndicator.image.path)
        #                 self.edPluginReadImageHeader = self.loadPlugin(self.strPluginReadImageHeaderName)
        #                 self.edPluginReadImageHeader.dataInput = xsDataInputReadImageHeader
        #                 self.edPluginReadImageHeader.executeSynchronous()
        #                 xsDataResultReadImageHeader = self.edPluginReadImageHeader.dataOutput
        #                 if xsDataResultReadImageHeader is not None:
        #                     xsDataSubWedge = xsDataResultReadImageHeader.subWedge
        #                     self.xsDataCollection = XSDataCollection()
        #                     self.xsDataCollection.addSubWedge(xsDataSubWedge)
        #                     xsDataIndexingInput = XSDataIndexingInput()
        #                     xsDataIndexingInput.setDataCollection(self.xsDataCollection)
        #                     xsDataMOSFLMIndexingInput = EDHandlerXSDataMOSFLMv10.generateXSDataMOSFLMInputIndexing(
        #                         xsDataIndexingInput)
        #                     edPluginMOSFLMIndexing = self.loadPlugin(self.strIndexingMOSFLMPluginName)
        #                     self.listPluginMOSFLM.append(
        #                         [edPluginMOSFLMIndexing, xsDataResultControlImageQualityIndicator])
        #                     edPluginMOSFLMIndexing.setDataInput(xsDataMOSFLMIndexingInput)
        #                     edPluginMOSFLMIndexing.execute()
        #         for tupleMOSFLM in self.listPluginMOSFLM:
        #             edPluginMOSFLMIndexing = tupleMOSFLM[0]
        #             xsDataResultControlImageQualityIndicator = tupleMOSFLM[1]
        #             edPluginMOSFLMIndexing.synchronize()
        #             if not edPluginMOSFLMIndexing.isFailure():
        #                 xsDataMOSFLMOutput = edPluginMOSFLMIndexing.dataOutput
        #                 xsDataIndexingResult = EDHandlerXSDataMOSFLMv10.generateXSDataIndexingResult(xsDataMOSFLMOutput)
        #                 selectedSolution = xsDataIndexingResult.selectedSolution
        #                 if selectedSolution is not None:
        #                     xsDataResultControlImageQualityIndicator.selectedIndexingSolution = selectedSolution

        outData['imageQualityIndicators'] = listImageQualityIndicators
        outData['crystfel_per_batch'] = listcrystfel_output
        return outData

    @classmethod
    def getH5FilePath(cls, filePath, batchSize=1, isFastMesh=False):
        imageNumber = UtilsImage.getImageNumber(filePath)
        prefix = UtilsImage.getPrefix(filePath)
        if isFastMesh:
            h5ImageNumber = int((imageNumber - 1) / 100) + 1
            h5FileNumber = 1
        else:
            h5ImageNumber = 1
            h5FileNumber = int((imageNumber - 1) / batchSize) * batchSize + 1
        h5MasterFileName = "{prefix}_{h5FileNumber}_master.h5".format(
            prefix=prefix, h5FileNumber=h5FileNumber)
        h5MasterFilePath = filePath.parent / h5MasterFileName
        h5DataFileName = \
            "{prefix}_{h5FileNumber}_data_{h5ImageNumber:06d}.h5".format(
                prefix=prefix, h5FileNumber=h5FileNumber, h5ImageNumber=h5ImageNumber)
        h5DataFilePath = filePath.parent / h5DataFileName
        return h5MasterFilePath, h5DataFilePath, h5FileNumber
