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

import os
import json
import numpy
import shlex
import shutil
import base64
import pathlib
import tempfile

import matplotlib
import matplotlib.pyplot as plt

from edna2.tasks.AbstractTask import AbstractTask
from edna2.tasks.H5ToCBFTask import H5ToCBFTask
from edna2.tasks.ReadImageHeader import ReadImageHeader
from edna2.tasks.ISPyBTasks import ISPyBRetrieveDataCollection

from edna2.utils import UtilsPath
from edna2.utils import UtilsImage
from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging

# Corresponding EDNA code:
# https://github.com/olofsvensson/edna-mx
# mxPluginExec/plugins/EDPluginDozor-v1.0/plugins/EDPluginDozorv1_0.py
# mxv1/plugins/EDPluginControlDozor-v1.0/plugins/EDPluginControlDozorv1_0.py

matplotlib.use('Agg')

logger = UtilsLogging.getLogger()

# Default values for ESRF Pilatus2M : ID30a1: 1,776; 826,894
IX_MIN_PILATUS_2M = 1
IX_MAX_PILATUS_2M = 776
IY_MIN_PILATUS_2M = 826
IY_MAX_PILATUS_2M = 894

# Default values for ESRF Pilatus6M : id23eh1: 1,1230; 1228, 1298
IX_MIN_PILATUS_6M = 1
IX_MAX_PILATUS_6M = 1230
IY_MIN_PILATUS_6M = 1228
IY_MAX_PILATUS_6M = 1298

# Default values for ESRF Eiger4M : ID30a3: 1,1120; 1025,1140
IX_MIN_EIGER_4M = 1
IX_MAX_EIGER_4M = 1120
IY_MIN_EIGER_4M = 1025
IY_MAX_EIGER_4M = 1140

# Default parameters

DEFAULT_FRACTION_POLARIZATION = 0.99
DEFAULT_IMAGE_STEP = 1
MAX_BATCH_SIZE = 5000


class ExecDozor(AbstractTask):  # pylint: disable=too-many-instance-attributes
    """
    The ExecDozor is responsible for executing the 'dozor' program.
    """

    def getInDataSchema(self):
        return {
            "type": "object",
            "required": ["detectorType", "exposureTime", "spotSize",
                         "detectorDistance", "wavelength",
                         "orgx", "orgy", "oscillationRange",
                         "firstImageNumber", "numberImages",
                         "nameTemplateImage"],
            "properties": {
                "detectorType": {"type": "string"},
                "exposureTime": {"type": "number"},
                "spotSize": {"type": "integer"},
                "detectorDistance": {"type": "number"},
                "wavelength": {"type": "number"},
                "fractionPolarization": {"type": "number"},
                "orgx": {"type": "number"},
                "orgy": {"type": "number"},
                "oscillationRange": {"type": "number"},
                "imageStep": {"type": "number"},
                "startingAngle": {"type": "number"},
                "firstImageNumber": {"type": "integer"},
                "numberImages": {"type": "integer"},
                "nameTemplateImage": {"type": "string"},
                "wedgeNumber": {"type": "integer"},
                "radiationDamage": {"type": "boolean"},
                "overlap": {"type": "number"}
            }
        }

    def getOutDataSchema(self):
        return {
            "type": "object",
            "required": ["imageDozor"],
            "properties": {
                "imageDozor": {
                    "type": "array",
                    "items": {
                        "$ref": self.getSchemaUrl("imageDozor.json")
                    }
                },
                "halfDoseTime": {"type": "number"},
                "dozorPlot":  {"type": "string"},
                "plotmtvFile":  {"type": "string"},
                "pngPlots":  {
                    "type": "array",
                    "items": {"type": "string"}
                },
            },
        }

    def run(self, inData):
        commands = self.generateCommands(inData)
        with open(str(self.getWorkingDirectory() / 'dozor.dat'), 'w') as f:
            f.write(commands)
        # Create dozor command line
        commandLine = 'dozor -pall'
        if 'radiationDamage' in inData:
            commandLine += ' -rd dozor.dat'
        else:
            commandLine += ' -p dozor.dat'
        self.setLogFileName('dozor.log')
        self.runCommandLine(commandLine)
        log = self.getLog()
        outData = self.parseOutput(inData, log,
                                   workingDir=self.getWorkingDirectory())
        return outData

    def generateCommands(self, inData):
        """
        This method creates the input file for dozor
        """
        ixMin = None
        ixMax = None
        iyMin = None
        iyMax = None
        nx = None
        ny = None
        pixel = None
        if inData['detectorType'] == 'pilatus2m':
            nx = 1475
            ny = 1679
            pixel = 0.172
            ixMin = IX_MIN_PILATUS_2M
            ixMax = IX_MAX_PILATUS_2M
            iyMin = IY_MIN_PILATUS_2M
            iyMax = IY_MAX_PILATUS_2M
        elif inData['detectorType'] == 'pilatus6m':
            nx = 2463
            ny = 2527
            pixel = 0.172
            ixMin = IX_MIN_PILATUS_6M
            ixMax = IX_MAX_PILATUS_6M
            iyMin = IY_MIN_PILATUS_6M
            iyMax = IY_MAX_PILATUS_6M
        elif inData['detectorType'] == 'eiger4m':
            nx = 2070
            ny = 2167
            pixel = 0.075
            ixMin = IX_MIN_EIGER_4M
            ixMax = IX_MAX_EIGER_4M
            iyMin = IY_MIN_EIGER_4M
            iyMax = IY_MAX_EIGER_4M
        processInfo = 'name template: {0}'.format(
            os.path.basename(inData['nameTemplateImage']))
        processInfo += ', first image no: {0}'.format(
            inData['firstImageNumber'])
        processInfo += ', no images: {0}'.format(
            inData['numberImages'])
        command = '!\n'
        command += 'detector %s\n' % inData['detectorType']
        command += 'nx %d\n' % nx
        command += 'ny %d\n' % ny
        command += 'pixel %f\n' % pixel
        command += 'exposure %.3f\n' % inData['exposureTime']
        command += 'spot_size %d\n' % inData['spotSize']
        command += 'detector_distance %.3f\n' % \
            inData['detectorDistance']
        command += 'X-ray_wavelength %.3f\n' % inData['wavelength']
        fractionPolarization = inData.get(
            'fractionPolarization',
            DEFAULT_FRACTION_POLARIZATION
        )
        command += 'fraction_polarization %.3f\n' % fractionPolarization
        command += 'pixel_min 0\n'
        command += 'pixel_max 64000\n'
        if ixMin is not None:
            command += 'ix_min %d\n' % ixMin
            command += 'ix_max %d\n' % ixMax
            command += 'iy_min %d\n' % iyMin
            command += 'iy_max %d\n' % iyMax
        badZona = UtilsConfig.get(self, 'bad_zona', None)
        if badZona is not None:
            command += 'bad_zona %s\n' % badZona
        command += 'orgx %.1f\n' % inData['orgx']
        command += 'orgy %.1f\n' % inData['orgy']
        command += 'oscillation_range %.3f\n' % \
            inData['oscillationRange']
        imageStep = inData.get('imageStep', DEFAULT_IMAGE_STEP)
        command += 'image_step %.3f\n' % imageStep
        command += 'starting_angle %.3f\n' % inData['startingAngle']
        command += 'first_image_number %d\n' % inData['firstImageNumber']
        command += 'number_images %d\n' % inData['numberImages']
        if 'wedgeNumber' in inData:
            command += 'wedge_number %d\n' % inData['wedgeNumber']
        command += 'name_template_image %s\n' % \
            inData['nameTemplateImage']
        command += 'end\n'
        # logger.debug('command: {0}'.format(command))
        return command

    def parseOutput(self, inData, output, workingDir=None):
        """
        This method parses the output of dozor
        """
        resultDozor = {
            'imageDozor': []  # list of dict. each dict contains spotFile and Image_path
        }
        # Create template for image name
        template = inData['nameTemplateImage']
        noWildCards = template.count('?')
        template = template.replace('?'*noWildCards,
                                    '{0:0'+str(noWildCards) + '}')
        # Skip the four first lines
        listOutput = output.split('\n')[6:]

        for line in listOutput:
            # Remove '|'
            listLine = shlex.split(line.replace('|', ' '))
            if len(listLine) > 0 and listLine[0].isdigit():
                imageDozor = {}
                imageNumber = int(listLine[0])
                overlap = inData.get('overlap', 0.0)
                angle = inData['startingAngle'] + \
                    (imageNumber - inData['firstImageNumber']) * \
                    (inData['oscillationRange'] - overlap) + \
                    inData['oscillationRange'] / 2.0
                imageDozor['number'] = imageNumber
                imageDozor['image'] = template.format(imageNumber)
                imageDozor['angle'] = angle
                imageDozor['spotsNumOf'] = None
                imageDozor['spotsIntAver'] = None
                imageDozor['spotsResolution'] = None
                imageDozor['mainScore'] = None
                imageDozor['spotScore'] = None
                imageDozor['visibleResolution'] = 40
                try:
                    if listLine[5].startswith('-') or len(listLine) < 11:
                        imageDozor['spotsNumOf'] = \
                            int(listLine[1])
                        imageDozor['spotsIntAver'] = \
                            self.parseDouble(listLine[2])
                        imageDozor['spotsRFactor'] = \
                            self.parseDouble(listLine[3])
                        imageDozor['spotsResolution'] = \
                            self.parseDouble(listLine[4])
                        imageDozor['mainScore'] = \
                            self.parseDouble(listLine[8])
                        imageDozor['spotScore'] = \
                            self.parseDouble(listLine[9])
                        imageDozor['visibleResolution'] = \
                            self.parseDouble(listLine[10])
                    else:
                        imageDozor['spotsNumOf'] = \
                            int(listLine[1])
                        imageDozor['spotsIntAver'] = \
                            self.parseDouble(listLine[2])
                        imageDozor['spotsRfactor'] = \
                            self.parseDouble(listLine[3])
                        imageDozor['spotsResolution'] = \
                            self.parseDouble(listLine[4])
                        imageDozor['powderWilsonScale'] = \
                            self.parseDouble(listLine[5])
                        imageDozor['powderWilsonBfactor'] = \
                            self.parseDouble(listLine[6])
                        imageDozor['powderWilsonResolution'] = \
                            self.parseDouble(listLine[7])
                        imageDozor['powderWilsonCorrelation'] = \
                            self.parseDouble(listLine[8])
                        imageDozor['powderWilsonRfactor'] = \
                            self.parseDouble(listLine[9])
                        imageDozor['mainScore'] = \
                            self.parseDouble(listLine[10])
                        imageDozor['spotScore'] = \
                            self.parseDouble(listLine[11])
                        imageDozor['visibleResolution'] = \
                            self.parseDouble(listLine[12])
                except Exception as e:
                    logger.warning('Exception caught when parsing Dozor log!')
                    logger.warning(e)
                # ExecDozor spot file
                if workingDir is not None:
                    spotFile = os.path.join(str(workingDir),
                                            '%05d.spot' % imageDozor['number'])
                    if os.path.exists(spotFile):
                        imageDozor['spotFile'] = spotFile
#                #print imageDozor['marshal()
                resultDozor['imageDozor'].append(imageDozor)
            elif line.startswith('h'):
                resultDozor['halfDoseTime'] = line.split('=')[1].split()[0]
        # Check if mtv plot file exists
        if workingDir is not None:
            mtvFileName = 'dozor_rd.mtv'
            mtvFilePath = os.path.join(str(workingDir), mtvFileName)
            if os.path.exists(mtvFilePath):
                resultDozor['plotmtvFile'] = mtvFilePath
                resultDozor['pngPlots'] = self.generatePngPlots(mtvFilePath,
                                                                workingDir)
        return resultDozor

    @classmethod
    def parseDouble(cls, value):
        returnValue = None
        try:
            returnValue = float(value)
        except Exception as ex:
            errorMessage = 'Error when trying to parse '' + value + '': %r' % ex
            logger.error(errorMessage)
        return returnValue

    @classmethod
    def generatePngPlots(cls, plotmtvFile, workingDir):
        listXSFile = []
        # Create plot dictionary
        with open(str(plotmtvFile)) as f:
            listLines = f.readlines()
        listPlots = []
        dictPlotList = []
        dictSubPlot = {}
        index = 0
        while index < len(listLines):
            # print('0' + listLines[index])
            if listLines[index].startswith('$'):
                dictPlot = {}
                dictPlotList = []
                listPlots.append(dictPlot)
                dictPlot['plotList'] = dictPlotList
                index += 1
                dictPlot['name'] = listLines[index].split('\'')[1]
                index += 1
                while listLines[index].startswith('%'):
                    listLine = listLines[index].split('=')
                    label = listLine[0][1:].strip()
                    if '\'' in listLine[1]:
                        value = listLine[1].split('\'')[1]
                    else:
                        value = listLine[1]
                    value = value.replace('\n', '').strip()
                    dictPlot[label] = value
                    index += 1
            elif listLines[index].startswith('#'):
                dictSubPlot = {}
                dictPlotList.append(dictSubPlot)
                plotName = listLines[index].split('#')[1]
                dictSubPlot['name'] = plotName.replace('\n', '').strip()
                index += 1
                while listLines[index].startswith('%'):
                    listLine = listLines[index].split('=')
                    label = listLine[0][1:].strip()
                    if '\'' in listLine[1]:
                        value = listLine[1].split('\'')[1]
                    else:
                        value = listLine[1]
                    value = value.replace('\n', '').strip()
                    dictSubPlot[label] = value
                    index += 1
                dictSubPlot['xValues'] = []
                dictSubPlot['yValues'] = []
            else:
                listData = listLines[index].replace('\n', '').split()
                dictSubPlot['xValues'].append(float(listData[0]))
                dictSubPlot['yValues'].append(float(listData[1]))
                index += 1
        # Generate the plots
        for mtvplot in listPlots:
            listLegend = []
            xmin = None
            xmax = None
            ymin = None
            ymax = None
            for subPlot in mtvplot['plotList']:
                xmin1 = min(subPlot['xValues'])
                if xmin is None or xmin > xmin1:
                    xmin = xmin1
                xmax1 = max(subPlot['xValues'])
                if xmax is None or xmax < xmax1:
                    xmax = xmax1
                ymin1 = min(subPlot['yValues'])
                if ymin is None or ymin > ymin1:
                    ymin = ymin1
                ymax1 = max(subPlot['yValues'])
                if ymax is None or ymax < ymax1:
                    ymax = ymax1
            if 'xmin' in mtvplot:
                xmin = float(mtvplot['xmin'])
            if 'ymin' in mtvplot:
                ymin = float(mtvplot['ymin'])
            plt.xlim(xmin, xmax)
            plt.ylim(ymin, ymax)
            plt.xlabel(mtvplot['xlabel'])
            plt.ylabel(mtvplot['ylabel'])
            plt.title(mtvplot['name'])
            for subPlot in mtvplot['plotList']:
                if 'markercolor' in subPlot:
                    style = 'bs-.'
                else:
                    style = 'r'
                plt.plot(
                    subPlot['xValues'],
                    subPlot['yValues'],
                    style,
                    linewidth=2
                )
                listLegend.append(subPlot['linelabel'])
            plt.legend(listLegend, loc='lower right')
            mtvPlotName = mtvplot['name'].replace(' ', '').replace('.', '_')
            plotPath = os.path.join(str(workingDir), mtvPlotName + '.png')
            plt.savefig(plotPath, bbox_inches='tight', dpi=75)
            plt.close()
            listXSFile.append(plotPath)
        return listXSFile


class ControlDozor(AbstractTask):

    def __init__(self, inData):
        AbstractTask.__init__(self, inData)
        self.hasOverlap = False
        self.overlap = 0.0

    def getInDataSchema(self):
        return {
            "type": "object",
            "properties": {
                "dataCollectionId": {"type": "integer"},
                "processDirectory": {"type": "string"},
                "image": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "directory": {"type": "string"},
                "template": {"type": "string"},
                "startNo": {"type": "integer"},
                "endNo": {"type": "integer"},
                "batchSize": {"type": "integer"},
                "hdf5BatchSize": {"type": "integer"},
                "wedgeNumber": {"type": "integer"},
                "radiationDamage": {"type": "string"},
                "keepCbfTmpDirectory": {"type": "boolean"}
            }
        }

    def getOutDataSchema(self):
        return {
            "type": "object",
            "required": ["imageQualityIndicators", "detectorType"],
            "properties": {
                "imageQualityIndicators": {
                    "type": "array",
                    "items": {
                        "$ref": self.getSchemaUrl("imageQualityIndicators.json")
                    }
                },
                "detectorType": {"type": "string"},
                "halfDoseTime": {"type": "number"},
                "dozorPlot":  {"type": "string"},
                "pathToCbfDirectory":  {"type": "string"},
                "pngPlots":  {"type": "string"},
            },
        }

    def run(self, inData):
        outData = {}
        hasHdf5Prefix = False
        detectorType = None
        # Check overlap
        overlap = inData.get('overlap', self.overlap)
        # Check if connection to ISPyB needed
        batchSize, dictImage = self.determineBatchsize(inData)
        logger.debug("ExecDozor batch size: {0}".format(batchSize))
        if 'hdf5BatchSize' in inData:
           hdf5BatchSize = inData['hdf5BatchSize']
        listAllBatches = self.createListOfBatches(dictImage.keys(), batchSize)
        if dictImage[listAllBatches[0][0]].endswith('h5'):
            hasHdf5Prefix = True
            # Convert HDF5 images to CBF
            logger.debug("HDF5 converter batch size: {0}".format(batchSize))
            doRadiationDamage = inData.get('doRadiationDamage', False)
            if doRadiationDamage:
               cbfTempDir = None
            else:
               cbfTempDir = tempfile.mkdtemp(prefix='CbfTemp_')
            listHdf5Batches = self.createListOfBatches(
                dictImage.keys(),
                batchSize
            )
            dictImage, hasHdf5Prefix = self.convertToCBF(
                dictImage,
                listHdf5Batches,
                doRadiationDamage=doRadiationDamage,
                cbfTempDir=cbfTempDir
            )
        outData['imageQualityIndicators'] = []
        for listBatch in listAllBatches:
            outDataDozor, detectorType = self.runDozorTask(
                inData=inData,
                dictImage=dictImage,
                listBatch=listBatch,
                overlap=overlap,
                workingDirectory=str(self.getWorkingDirectory()),
                hasHdf5Prefix=hasHdf5Prefix,
                hasOverlap=self.hasOverlap
            )
            if outDataDozor is not None:
                for imageDozor in outDataDozor['imageDozor']:
                    imageQualityIndicators = {
                        'angle': imageDozor['angle'],
                        'number': imageDozor['number'],
                        'image': imageDozor['image'],
                        'dozorScore': imageDozor['mainScore'],
                        'dozorSpotScore': imageDozor['spotScore'],
                        'dozorSpotsNumOf': imageDozor['spotsNumOf'],
                        'dozorSpotsIntAver': imageDozor['spotsIntAver'],
                        'dozorSpotsResolution': imageDozor['spotsResolution'],
                        'dozorVisibleResolution': imageDozor['visibleResolution'],
                    }
                    if 'spotFile' in imageDozor:
                        if os.path.exists(imageDozor['spotFile']):
                            spotFile = imageDozor['spotFile']
                            imageQualityIndicators['dozorSpotFile'] = spotFile
                            numpyArray = numpy.loadtxt(spotFile, skiprows=3)
                            imageQualityIndicators['dozorSpotList'] = \
                                base64.b64encode(numpyArray.tostring()).decode('utf-8')
                            imageQualityIndicators['dozorSpotListShape'] = \
                                list(numpyArray.shape)
                    outData['imageQualityIndicators'].append(imageQualityIndicators)
            # Make plot if we have a data collection id
        if 'dataCollectionId' in inData:
            self.makePlot(inData['dataCollectionId'], outData, self.getWorkingDirectory())
        #            xsDataResultControlDozor.halfDoseTime = edPluginDozor.dataOutput.halfDoseTime
        #            xsDataResultControlDozor.pngPlots = edPluginDozor.dataOutput.pngPlots
        #
        #            self.sendResultToMXCuBE(imageDozorBatchList)
        #            self.sendMessageToMXCuBE("Batch processed")
        #        if self.cbfTempDir is not None:
        #            if self.dataInput.keepCbfTmpDirectory is not None and self.dataInput.keepCbfTmpDirectory.value:
        #                self.dataOutput.pathToCbfDirectory = XSDataFile(XSDataString(self.cbfTempDir))
        #            else:
        #                shutil.rmtree(self.cbfTempDir)

        # Read the header from the first image in the batch
        outData['detectorType'] = detectorType
        return outData

    def determineBatchsize(self, inData):
        if 'dataCollectionId' in inData:
            ispybInData = {
                'dataCollectionId': inData['dataCollectionId']
            }
            ispybTask = ISPyBRetrieveDataCollection(inData=ispybInData)
            ispybTask.execute()
            dataCollection = ispybTask.outData
            batchSize = UtilsConfig.get('ControlDozor', 'batchSize')
            if batchSize is None:
                batchSize = dataCollection['numberOfImages']
            if batchSize > MAX_BATCH_SIZE:
                batchSize = MAX_BATCH_SIZE
            if 'overlap' in dataCollection and \
                    abs(dataCollection['overlap']) > 1:
                self.hasOverlap = True
                self.overlap = dataCollection['overlap']
            else:
                self.overlap = 0.0
            dictImage = self.createImageDictFromISPyB(dataCollection)
        else:
            # No connection to ISPyB, take parameters from input
            if 'batchSize' in inData:
                batchSize = inData['batchSize']
            else:
                batchSize = MAX_BATCH_SIZE
            dictImage = self.createImageDict(inData)
        return batchSize, dictImage

    @classmethod
    def runDozorTask(cls, inData, dictImage, listBatch,
                     overlap, workingDirectory,
                     hasHdf5Prefix, hasOverlap):
        outDataDozor = None
        image = dictImage[listBatch[0]]
        inDataReadHeader = {
            'image': image
        }
        controlHeader = ReadImageHeader(inData=inDataReadHeader)
        controlHeader.execute()
        outDataHeader = controlHeader.outData
        subWedge = outDataHeader['subWedge'][0]
        experimentalCondition = subWedge['experimentalCondition']
        beam = experimentalCondition['beam']
        detector = experimentalCondition['detector']
        detectorType = detector['type']
        goniostat = experimentalCondition['goniostat']
        inDataDozor = {'detectorType': detector['type'],
                       'exposureTime': beam['exposureTime'],
                       'detectorDistance': detector['distance'],
                       'spotSize': 3, 'wavelength': beam['wavelength'],
                       'orgx': detector['beamPositionX'] / detector['pixelSizeX'],
                       'orgy': detector['beamPositionY'] / detector['pixelSizeY'],
                       'oscillationRange': goniostat['oscillationWidth'],
                       'startingAngle': goniostat['rotationAxisStart'],
                       'firstImageNumber': subWedge['image'][0]['number'],
                       'numberImages': len(listBatch),
                       'workingDirectory': workingDirectory,
                       'overlap': overlap}
        fileName = os.path.basename(subWedge['image'][0]['path'])
        prefix = UtilsImage.getPrefix(fileName)
        suffix = UtilsImage.getSuffix(fileName)
        if UtilsConfig.isEMBL():
            template = '{0}_?????.{1}'.format(prefix, suffix)
        elif hasHdf5Prefix and not hasOverlap:
            template = '{0}_??????.{1}'.format(prefix, suffix)
        else:
            template = '{0}_????.{1}'.format(prefix, suffix)
        inDataDozor['nameTemplateImage'] = os.path.join(
            os.path.dirname(subWedge['image'][0]['path']),
            template
        )
        if 'wedgeNumber' in inData:
            inDataDozor['wedgeNumber'] = inData['wedgeNumber']
        if 'radiationDamage' in inData:
            inDataDozor['radiationDamage'] = inData['radiationDamage']
        dozor = ExecDozor(inData=inDataDozor)
        dozor.execute()
        if not dozor.isFailure():
            outDataDozor = dozor.outData
        return outDataDozor, detectorType

    def makePlot(self, dataCollectionId, outDataImageDozor, workingDirectory):
        minImageNumber = None
        maxImageNumber = None
        minAngle = None
        maxAngle = None
        minDozorValue = None
        maxDozorValue = None
        minResolution = None
        maxResolution = None
        plotFileName = 'dozor_{0}.png'.format(dataCollectionId)
        csvFileName = 'dozor_{0}.csv'.format(dataCollectionId)
        with open(str(workingDirectory / csvFileName), 'w') as gnuplotFile:
            gnuplotFile.write(
                '# Data directory: {0}\n'.format(self.directory)
            )
            gnuplotFile.write(
                '# File template: {0}\n'.format(
                    self.template.replace('%04d', '####')
                )
            )
            gnuplotFile.write(
                '# {0:>9s}{1:>16s}{2:>16s}{3:>16s}{4:>16s}{5:>16s}\n'.format(
                    "'Image no'",
                    "'Angle'",
                    "'No of spots'",
                    "'Main score (*10)'",
                    "'Spot score'",
                    "'Visible res.'",
                )
            )
            for imageQualityIndicators in outDataImageDozor['imageQualityIndicators']:
               gnuplotFile.write(
                   '{0:10d},{1:15.3f},{2:15d},{3:15.3f},{4:15.3f},{5:15.3f}\n'.format(
                        imageQualityIndicators['number'],
                        imageQualityIndicators['angle'],
                        imageQualityIndicators['dozorSpotsNumOf'],
                        10 * imageQualityIndicators['dozorScore'],
                        imageQualityIndicators['dozorSpotScore'],
                        imageQualityIndicators['dozorVisibleResolution'],
                    )
               )
               if minImageNumber is None or minImageNumber > imageQualityIndicators['number']:
                   minImageNumber = imageQualityIndicators['number']
                   minAngle = imageQualityIndicators['angle']
               if maxImageNumber is None or maxImageNumber < imageQualityIndicators['number']:
                   maxImageNumber = imageQualityIndicators['number']
                   maxAngle = imageQualityIndicators['angle']
               if minDozorValue is None or minDozorValue > imageQualityIndicators['dozorScore']:
                   minDozorValue = imageQualityIndicators['dozorScore']
               if maxDozorValue is None or maxDozorValue < imageQualityIndicators['dozorScore']:
                   maxDozorValue = imageQualityIndicators['dozorScore']

               # Min resolution: the higher the value the lower the resolution
               if minResolution is None or minResolution < imageQualityIndicators['dozorVisibleResolution']:
                   # Disregard resolution worse than 10.0
                   if imageQualityIndicators['dozorVisibleResolution'] < 10.0:
                       minResolution = imageQualityIndicators['dozorVisibleResolution']

               # Max resolution: the lower the number the better the resolution
               if maxResolution is None or maxResolution > imageQualityIndicators['dozorVisibleResolution']:
                   maxResolution = imageQualityIndicators['dozorVisibleResolution']


        xtics = ''
        if minImageNumber is not None and minImageNumber == maxImageNumber:
           minAngle -= 1.0
           maxAngle += 1.0
        noImages = maxImageNumber - minImageNumber + 1
        if noImages <= 4:
           minImageNumber -= 0.1
           maxImageNumber += 0.1
           deltaAngle = maxAngle - minAngle
           minAngle -= deltaAngle * 0.1 / noImages
           maxAngle += deltaAngle * 0.1 / noImages
           xtics = '1'

        if maxResolution is None or maxResolution > 0.8:
           maxResolution = 0.8
        else:
           maxResolution = int(maxResolution * 10.0) / 10.0

        if minResolution is None or minResolution < 4.5:
           minResolution = 4.5
        else:
           minResolution = int(minResolution * 10.0) / 10.0 + 1

        if maxDozorValue < 0.001 and minDozorValue < 0.001:
           yscale = 'set yrange [-0.5:0.5]\n    set ytics 1'
        else:
           yscale = 'set autoscale  y'

        gnuplotScript = \
"""#
set terminal png
set output '{dozorPlotFileName}'
set title '{title}'
set grid x2 y2
set xlabel 'Image number'
set x2label 'Angle (degrees)'
set y2label 'Resolution (A)'
set ylabel 'Number of spots / ExecDozor score (*10)'
set xtics {xtics} nomirror
set x2tics
set ytics nomirror
set y2tics
set xrange [{minImageNumber}:{maxImageNumber}]
set x2range [{minAngle}:{maxAngle}]
{yscale}
set y2range [{minResolution}:{maxResolution}]
set key below
plot '{dozorCsvFileName}' using 1:3 title 'Number of spots' axes x1y1 with points linetype rgb 'goldenrod' pointtype 7 pointsize 1.5, \
    '{dozorCsvFileName}' using 1:4 title 'ExecDozor score' axes x1y1 with points linetype 3 pointtype 7 pointsize 1.5, \
    '{dozorCsvFileName}' using 1:6 title 'Visible resolution' axes x1y2 with points linetype 1 pointtype 7 pointsize 1.5
""".format(title=self.template.replace('%04d', '####'),
          dozorPlotFileName=plotFileName,
          dozorCsvFileName=csvFileName,
          minImageNumber=minImageNumber,
          maxImageNumber=maxImageNumber,
          minAngle=minAngle,
          maxAngle=maxAngle,
          minResolution=minResolution,
          maxResolution=maxResolution,
          xtics=xtics,
          yscale=yscale,
          )
        pathGnuplotScript = str(workingDirectory / 'gnuplot.sh')
        with open(pathGnuplotScript, 'w') as f:
            f.write(gnuplotScript)
        oldCwd = os.getcwd()
        os.chdir(str(workingDirectory))
        gnuplot = UtilsConfig.get(self, 'gnuplot', 'gnuplot')
        os.system('{0} {1}'.format(gnuplot, pathGnuplotScript))
        os.chdir(oldCwd)
        dozorPlotPath = workingDirectory / plotFileName
        dozorCsvPath = workingDirectory / csvFileName
        return dozorPlotPath, dozorCsvPath

    @classmethod
    def storeDataOnPyarch(cls, dozorPlotPath, dozorCsvPath,
                          directory, processDirectory=None):
        if processDirectory is None:
            processDirectory = pathlib.Path(
                str(directory).replace('RAW_DATA', 'PROCESSED_DATA'))
        resultsDirectory = processDirectory / 'results'
        try:
            if not resultsDirectory.exists():
                resultsDirectory.mkdir(parents=True, mode=0o755)
            dozorPlotResultPath = resultsDirectory / dozorPlotPath.name
            dozorCsvResultPath = resultsDirectory / dozorCsvPath.name
            shutil.copy(dozorPlotPath, dozorPlotResultPath)
            shutil.copy(dozorCsvPath, dozorCsvResultPath)
        except Exception as e:
            logger.warning(
                "Couldn't copy files to results directory: {0}".format(
                    resultsDirectory))
            logger.warning(e)
        try:
            # Create paths on pyarch
            dozorPlotPyarchPath = UtilsPath.createPyarchFilePath(dozorPlotResultPath)
            dozorCsvPyarchPath = UtilsPath.createPyarchFilePath(dozorCsvResultPath)
            if not os.path.exists(os.path.dirname(dozorPlotPyarchPath)):
                os.makedirs(os.path.dirname(dozorPlotPyarchPath), 0o755)
            shutil.copy(dozorPlotResultPath, dozorPlotPyarchPath)
            shutil.copy(dozorCsvResultPath, dozorCsvPyarchPath)
    #         # Upload to data collection
    #         xsDataInputISPyBSetImageQualityIndicatorsPlot = XSDataInputISPyBSetImageQualityIndicatorsPlot()
    #         xsDataInputISPyBSetImageQualityIndicatorsPlot.dataCollectionId = XSDataInteger(dataCollectionId)
    #         xsDataInputISPyBSetImageQualityIndicatorsPlot.imageQualityIndicatorsPlotPath = XSDataString(dozorPlotPyarchPath)
    #         xsDataInputISPyBSetImageQualityIndicatorsPlot.imageQualityIndicatorsCSVPath = XSDataString(dozorCsvPyarchPath)
    #         EDPluginISPyBSetImageQualityIndicatorsPlot = self.loadPlugin("EDPluginISPyBSetImageQualityIndicatorsPlotv1_4")
    #         EDPluginISPyBSetImageQualityIndicatorsPlot.dataInput = xsDataInputISPyBSetImageQualityIndicatorsPlot
    #         EDPluginISPyBSetImageQualityIndicatorsPlot.executeSynchronous()
        except Exception as e:
            logger.warning("Couldn't copy files to pyarch: {0}".format(dozorPlotPyarchPath))
            logger.warning(e)
    #
    # self.sendMessageToMXCuBE("Processing finished", "info")
    # self.setStatusToMXCuBE("Success")
    #

    def createImageDict(self, inData):
        # Create dictionary of all images with the image number as key
        dictImage = {}
        if 'image'in inData and len(inData['image']) > 0:
            listImage = inData['image']
            pathToFirstImage = listImage[0]
            self.directory = os.path.dirname(pathToFirstImage)
            self.template = os.path.basename(
                pathToFirstImage).replace('0001', '####')
        else:
            # Create list of images
            listImage = []
            self.directory = inData['directory']
            self.template = inData['template']
            startNo = int(inData['startNo'])
            endNo = int(inData['endNo'])
            for imageIndex in range(startNo, endNo + 1):
                imageName = self.template % imageIndex
                imagePath = os.path.join(self.directory, imageName)
                listImage.append(imagePath)
        for imagePath in listImage:
            imageNo = UtilsImage.getImageNumber(imagePath)
            dictImage[imageNo] = imagePath
        return dictImage

    def createImageDictFromISPyB(self, dataCollection):
        # Create dictionary of all images with the image number as key
        dictImage = {}
        # Create list of images
        listImage = []
        self.directory = dataCollection['imageDirectory']
        self.template = dataCollection['fileTemplate']
        startNo = dataCollection['startImageNumber']
        endNo = dataCollection['startImageNumber'] + \
                dataCollection['numberOfImages'] - 1
        for imageIndex in range(startNo, endNo + 1):
            imageName = self.template % imageIndex
            imagePath = os.path.join(self.directory, imageName)
            listImage.append(imagePath)
        for image in listImage:
            imageNo = UtilsImage.getImageNumber(image)
            dictImage[imageNo] = image
        return dictImage

    @classmethod
    def createListOfBatches(cls, listImage, batchSize):
        # Create the list of batches containing the image no
        listAllBatches = []
        listImagesInBatch = []
        indexBatch = 0
        indexNextImageInBatch = None
        listImageSorted = sorted(listImage)
        for imageNo in listImageSorted:
            if indexNextImageInBatch is None:
                # This image can be appended to this batch
                indexBatch = 1
                indexNextImageInBatch = imageNo + 1
                listImagesInBatch.append(imageNo)
                if batchSize == 1:
                    listAllBatches.append(listImagesInBatch)
                    listImagesInBatch = []
                    indexNextImageInBatch = None
            elif imageNo != indexNextImageInBatch or indexBatch == batchSize:
                # A new batch must be started
                indexBatch = 1
                listAllBatches.append(listImagesInBatch)
                listImagesInBatch = [imageNo]
                indexNextImageInBatch = imageNo + 1
            else:
                # This image can be appended to this batch
                listImagesInBatch.append(imageNo)
                indexNextImageInBatch += 1
                indexBatch += 1
        if listImagesInBatch:
            listAllBatches.append(listImagesInBatch)
        return listAllBatches

    @classmethod
    def convertToCBF(cls, dictImage, listAllBatches,
                     doRadiationDamage=False, hasOverlap=False,
                     cbfTempDir=None):
        # Find start and end image number
        startImage = None
        endImage = None
        for image in dictImage:
            if startImage is None or startImage > image:
                startImage = image
            if endImage is None or endImage < image:
                endImage = image
        # Check if we are dealing with characterisation images
        newDict = {}
        hasHdf5Prefix = True
        if hasOverlap or startImage == endImage:
            hasHdf5Prefix = False
            for imageNumber in dictImage:
                inDataH5ToCBF = {
                    'hdf5File': startImage,
                    'hdf5ImageNumber': imageNumber,
                    'forcedOutputImageNumber': imageNumber,
                }
                if cbfTempDir is not None:
                    inDataH5ToCBF['forcedOutputDirectory'] = cbfTempDir
                h5ToCBF = H5ToCBFTask(inData=inDataH5ToCBF)
                h5ToCBF.execute()
                outDataH5ToCBF = json.loads(h5ToCBF.outData().open().read())
                newDict['image'] = outDataH5ToCBF['outputCBFFile']
        else:
            listH5ToCBF = []
            directory = os.path.dirname(dictImage[listAllBatches[0][0]])
            for batch in listAllBatches:
                if doRadiationDamage:
                    inDataH5ToCBF = {
                        'hdf5File': dictImage[batch[0]],
                        'hdf5ImageNumber': batch[0],
                        'startImageNumber': listAllBatches[0][0],
                        'endImageNumber': listAllBatches[0][-1],
                    }
                else:
                    inDataH5ToCBF = {
                        'hdf5File': dictImage[startImage],
                        'hdf5ImageNumber': 1,
                        'startImageNumber': batch[0],
                        'endImageNumber': batch[-1],
                    }
                if cbfTempDir is not None:
                    inDataH5ToCBF['forcedOutputDirectory'] = cbfTempDir
                h5ToCBF = H5ToCBFTask(inData=inDataH5ToCBF)
                if doRadiationDamage:
                    h5ToCBF.execute()
                    if h5ToCBF.outData is not None and h5ToCBF.outData['outputCBFFileTemplate'] is not None:
                        outputCBFFileTemplate = h5ToCBF.outData['outputCBFFileTemplate']
                        for newImageNumber in batch:
                            oldImageNumber = newImageNumber - batch[0] + 1
                            oldPath = os.path.join(directory, outputCBFFileTemplate.path.value.replace('######', '{0:06d}'.format(oldImageNumber)))
                            newPath = os.path.join(directory, outputCBFFileTemplate.path.value.replace('######', '{0:04d}'.format(newImageNumber)))
                            os.rename(oldPath, newPath)
                            # newDict[newImageNumber] = XSDataFile(XSDataString(newPath))
                    hasHdf5Prefix = False
                else:
                    h5ToCBF.start()
                    listH5ToCBF.append(h5ToCBF)
            for h5ToCBF in listH5ToCBF:
                h5ToCBF.join()
                outDataH5ToCBF = h5ToCBF.outData
                if 'outputCBFFileTemplate' in outDataH5ToCBF:
                    template = outDataH5ToCBF['outputCBFFileTemplate']
                    template = template.replace('######', '{0:06d}')
                    for image in dictImage:
                        newDict[image] = template.format(image)
        return newDict, hasHdf5Prefix
#
#    def sendMessageToMXCuBE(self, _strMessage, level="info"):
#        if self._oServerProxy is not None:
#            self.DEBUG("Sending message to mxCuBE: {0}".format(_strMessage))
#            try:
#                for strMessage in _strMessage.split("\n"):
#                    if strMessage != "":
#                        self._oServerProxy.log_message("EDNA | ExecDozor: " + _strMessage, level)
#            except:
#                self.DEBUG("Sending message to mxCuBE failed!")
#
#    def sendResultToMXCuBE(self, _batchData):
#        if self._oServerProxy is not None:
#            self.DEBUG("Sending ExecDozor results to mxCuBE")
#            try:
#                self._oServerProxy.dozor_batch_processed(_batchData)
#            except:
#                pass
#
#    def setStatusToMXCuBE(self, status):
#        if self._oServerProxy is not None:
#            self.DEBUG("Sending dozor status %s to mxCuBE" % status)
#            try:
#                self._oServerProxy.dozor_status_changed(status)
#            except:
#                pass

# This is the old 'parseOutput' method that I kept in case we have to go back
# to the previous version of Dozor:
#
#     def parseOutput(self, inData, output, workingDir=None):
#         """
#         This method parses the output of dozor
#         """
#         resultDozor = {
#             'imageDozor': []
#         }
#         # Skip the four first lines
#         listOutput = output.split('\n')[6:]
#
#         for line in listOutput:
#             # Remove '|'
#             listLine = shlex.split(line.replace('|', ' '))
#             if len(listLine) > 0 and listLine[0].isdigit():
#                 imageDozor = {}
#                 imageNumber = int(listLine[0])
#                 overlap = inData.get('overlap', 0.0)
#                 angle = inData['startingAngle'] + \
#                         (imageNumber - inData['firstImageNumber']) * \
#                         (inData['oscillationRange'] - overlap) + \
#                         inData['oscillationRange'] / 2.0
#                 imageDozor['number'] = imageNumber
#                 imageDozor['angle'] = angle
#                 imageDozor['spotsNumOf'] = None
#                 imageDozor['spotsIntAver'] = None
#                 imageDozor['spotsResolution'] = None
#                 imageDozor['mainScore'] = None
#                 imageDozor['spotScore'] = None
#                 imageDozor['visibleResolution'] = 40
#                 try:
#                     if listLine[4].startswith('-') or len(listLine) < 11:
#                         imageDozor['spotsNumOf'] = \
#                             int(listLine[1])
#                         imageDozor['spotsIntAver'] = \
#                         imageDozor['spotsResolution'] = \
#                             self.parseDouble(listLine[3])
#                         imageDozor['mainScore'] = \
#                             self.parseDouble(listLine[7])
#                         imageDozor['spotScore'] = \
#                             self.parseDouble(listLine[8])
#                         imageDozor['visibleResolution'] = \
#                             self.parseDouble(listLine[9])
#                     else:
#                         imageDozor['spotsNumOf'] = \
#                             int(listLine[1])
#                         imageDozor['spotsIntAver'] = \
#                             self.parseDouble(listLine[2])
#                         imageDozor['spotsResolution'] = \
#                             self.parseDouble(listLine[3])
#                         imageDozor['powderWilsonScale'] = \
#                             self.parseDouble(listLine[4])
#                         imageDozor['powderWilsonBfactor'] = \
#                             self.parseDouble(listLine[5])
#                         imageDozor['powderWilsonResolution'] = \
#                             self.parseDouble(listLine[6])
#                         imageDozor['powderWilsonCorrelation'] = \
#                             self.parseDouble(listLine[7])
#                         imageDozor['powderWilsonRfactor'] = \
#                             self.parseDouble(listLine[8])
#                         imageDozor['mainScore'] = \
#                             self.parseDouble(listLine[9])
#                         imageDozor['spotScore'] = \
#                             self.parseDouble(listLine[10])
#                         imageDozor['visibleResolution'] = \
#                             self.parseDouble(listLine[11])
#                 except:
#                     pass
#                 # ExecDozor spot file
#                 if workingDir is not None:
#                     spotFile = os.path.join(str(workingDir),
#                                             '%05d.spot' % imageDozor['number'])
#                     if os.path.exists(spotFile):
#                         imageDozor['spotFile'] = spotFile
# #                #print imageDozor['marshal()
#                 resultDozor['imageDozor'].append(imageDozor)
#             elif line.startswith('h'):
#                 resultDozor['halfDoseTime'] = line.split('=')[1].split()[0]
#
#         # Check if mtv plot file exists
#         if workingDir is not None:
#             mtvFileName = 'dozor_rd.mtv'
#             mtvFilePath = os.path.join(str(workingDir), mtvFileName)
#             if os.path.exists(mtvFilePath):
#                 resultDozor['plotmtvFile'] = mtvFilePath
#                 resultDozor['pngPlots'] = self.generatePngPlots(mtvFilePath,
#                                                                 workingDir)
#         return resultDozor
