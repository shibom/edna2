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
from edna2.tasks.PhenixTasks import DistlSignalStrengthTask
from edna2.tasks.ReadImageHeader import ReadImageHeader
try:
    from edna2.tasks.CrystfelTasks import ExeCrystFEL
    from edna2.lib.autocryst.src.run_crystfel import AutoCrystFEL
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
                        "$ref": self.getSchemaUrl("imageQualityIndicators.json")
                    }
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
            doCrystfel = inData.get('doCrystfel', True)
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
        else:
            firstImage = listImage[0]
            lastImage = listImage[-1]
            directory = pathlib.Path(firstImage).parent
            template = UtilsImage.getTemplate(firstImage)
            startNo = UtilsImage.getImageNumber(firstImage)
            endNo = UtilsImage.getImageNumber(lastImage)
        outData = dict()
        listImageQualityIndicators = []
        listcrystfel_output = []
        inDataWaitFile = {}
        listDistlTask = []
        listDozorTask = []
        listCrystFELTask = []
        listOfImagesInBatch = []
        listOfAllBatches = []
        listOfAllH5Files = []
        indexBatch = 0
        self.listH5FilePath = []
        detectorType = None
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
        if UtilsImage.getSuffix(pathlib.Path(listImage[0])) == 'h5':
            for image in listImage:
                listOfAllH5Files.append(pathlib.Path(image))
        #
        # Loop over batches:
        # - Wait for all files in batch
        # - Run Dozor and Crystfel (if required) in parallel
        #
        # Check if we should run CrystFEL:

        for listOfImagesInBatch in listOfAllBatches:
            listOfH5FilesInBatch = []
            for imagePath in listOfImagesInBatch:
                # First wait for images
                self.waitForImagePath(
                    imagePath=imagePath,
                    batchSize=batchSize,
                    isFastMesh=isFastMesh,
                    minImageSize=minImageSize,
                    waitFileTimeOut=waitFileTimeOut,
                    listofH5FilesInBatch=listOfH5FilesInBatch
                )
            if not self.isFailure():
                # Determine start and end image no
                pathToFirstImage = listOfImagesInBatch[0]
                pathToLastImage = listOfImagesInBatch[-1]
                batchStartNo = UtilsImage.getImageNumber(pathToFirstImage)
                batchEndNo = UtilsImage.getImageNumber(pathToLastImage)
                # Run Control Dozor
                inDataControlDozor = {
                    'template': template,
                    'directory': directory,
                    'startNo': batchStartNo,
                    'endNo': batchEndNo,
                    'batchSize': batchSize,
                }
                controlDozor = ControlDozor(inDataControlDozor)
                controlDozor.start()
                listDozorTask.append((controlDozor, inDataControlDozor,
                                      list(listOfImagesInBatch), listOfH5FilesInBatch))
                # Check if we should run distl.signalStrength
                if doDistlSignalStrength:
                    for image in listOfImagesInBatch:
                        inDataDistl = {
                            'referenceImage': str(image)
                        }
                        distlTask = DistlSignalStrengthTask(inData=inDataDistl)
                        distlTask.start()
                        listDistlTask.append((image, distlTask))
                if doCrystfel:
                    # a work around as autocryst module works with only json file/string
                    inDataCrystFEL = {
                        'doCBFtoH5': False,
                        'doSubmit': True,
                    }
                    if len(listOfH5FilesInBatch) > 0:
                        inDataCrystFEL['listH5FilePath'] = listOfH5FilesInBatch
                    else:
                        inDataCrystFEL['cbfFileInfo'] = {
                            "directory": directory,
                            "startNo": batchStartNo,
                            "endNo": batchEndNo,
                            "template": template,
                            "batchSize": batchSize
                        }
                    crystfel = ExeCrystFEL(inData=inDataCrystFEL)
                    crystfel.start()
                    listCrystFELTask.append(crystfel)

        if not self.isFailure():
            # listIndexing = []
            listDistlResult = []
            # Synchronize all image quality indicator plugins and upload to ISPyB
            for (image, distlTask) in listDistlTask:
                imageQualityIndicators = {}
                if distlTask is not None:
                    distlTask.join()
                    if distlTask.isSuccess():
                        outDataDistl = distlTask.outData
                        if outDataDistl is not None:
                            imageQualityIndicators = outDataDistl['imageQualityIndicators']
                imageQualityIndicators['image'] = str(image)
                listDistlResult.append(imageQualityIndicators)
                # self.xsDataResultControlImageQualityIndicators.addImageQualityIndicators(xsDataImageQualityIndicators)
            for (controlDozor, inDataControlDozor, listBatch, listH5FilePath) in listDozorTask:
                controlDozor.join()
                # Check that we got at least one result
                if len(controlDozor.outData['imageQualityIndicators']) == 0:
                    # Run the dozor plugin again, this time synchronously
                    firstImage = listBatch[0].name
                    lastImage = listBatch[-1].name
                    logger.warning("No dozor results! Re-executing Dozor for" +
                                   " images {0} to {1}".format(firstImage, lastImage))
                    time.sleep(5)
                    controlDozor = ControlDozor(inDataControlDozor)
                    controlDozor.execute()
                listOutDataControlDozor = list(controlDozor.outData['imageQualityIndicators'])
                if detectorType is None:
                    detectorType = controlDozor.outData['detectorType']
                if doDistlSignalStrength:
                    for outDataControlDozor in listOutDataControlDozor:
                        for distlResult in listDistlResult:
                            if outDataControlDozor['image'] == distlResult['image']:
                                imageQualityIndicators = dict(outDataControlDozor)
                                imageQualityIndicators.update(distlResult)
                                listImageQualityIndicators.append(imageQualityIndicators)
                else:
                    listImageQualityIndicators += listOutDataControlDozor

            if len(listCrystFELTask) != 0:
                masterstream = str(self.getWorkingDirectory() / 'alltogether.stream')
                try:
                    for crystfel in listCrystFELTask:
                        crystfel.join()
                        catcommand = "cat %s >> %s" % (crystfel.outData['streamfile'], masterstream)
                        AutoCrystFEL.run_as_command(catcommand)

                    if not self.isFailure() and os.path.exists(masterstream):
                        crystfel_outdata = AutoCrystFEL.report_stats(masterstream)
                        AutoCrystFEL.write_cell_file(crystfel_outdata)
                        listcrystfel_output.append(crystfel_outdata)
                    else:
                        logger.error("CrystFEL did not run properly")
                except Exception as err:
                    self.setFailure()
                    logger.error(err)
        outData['imageQualityIndicators'] = listImageQualityIndicators
        outData['crystfel_all_batches'] = listcrystfel_output
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

    def waitForImagePath(self, imagePath, batchSize, isFastMesh,
                         minImageSize, waitFileTimeOut, listofH5FilesInBatch):
        # If Eiger, just wait for the h5 file
        if imagePath.suffix == '.h5':
            h5MasterFilePath, h5DataFilePath, hdf5ImageNumber = \
                self.getH5FilePath(imagePath,
                                   batchSize=batchSize,
                                   isFastMesh=isFastMesh)
            if h5DataFilePath not in listofH5FilesInBatch:
                listofH5FilesInBatch.append(h5DataFilePath)
                logger.info("Eiger data, waiting for master" +
                            " and data files...")
                inDataWaitFileTask = {
                    'file': str(h5DataFilePath),
                    'size': minImageSize,
                    'timeOut': waitFileTimeOut
                }
                waitFileTask = WaitFileTask(inData=inDataWaitFileTask)
                logger.info("Waiting for file {0}".format(h5DataFilePath))
                logger.debug("Wait file timeOut set to %f" % waitFileTimeOut)
                waitFileTask.execute()
                time.sleep(1)
            if not os.path.exists(h5DataFilePath):
                errorMessage = "Time-out while waiting for image %s" % h5DataFilePath
                logger.error(errorMessage)
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
                errorMessage = "Time-out while waiting for image " + \
                               str(imagePath)
                logger.error(errorMessage)
                self.setFailure()
