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
__date__ = "20/04/2020"

# Corresponding EDNA code:
# https://github.com/olofsvensson/edna-mx

# mxPluginExec/plugins/EDPluginGroupXDS-v1.0/plugins/EDPluginXDSv1_0.py
# mxPluginExec/plugins/EDPluginGroupXDS-v1.0/plugins/EDPluginXDSIndexingv1_0.py

import math
import numpy as np

from edna2.tasks.AbstractTask import AbstractTask

from edna2.utils import UtilsConfig
from edna2.utils import UtilsLogging
from edna2.utils import UtilsDetector
from edna2.utils import UtilsSymmetry


logger = UtilsLogging.getLogger()


class XDSTask(AbstractTask):
    """
    Common base class for all XDS tasks
    """

    def run(self, inData):
        commandLine = 'xds_par'
        listXDS_INP = self.generateXDS_INP(inData)
        self.writeXDS_INP(listXDS_INP, self.getWorkingDirectory())
        self.setLogFileName('xds.log')
        self.runCommandLine(commandLine, listCommand=[])
        # Work in progress!
        outData = self.parseXDSOutput(self.getWorkingDirectory())
        return outData

    def generateXDS_INP(self, inData):
        """
        This method creates a list of XDS commands,e.g.:

        OVERLOAD=10048500 ! number not relevant, but needed
        DIRECTION_OF_DETECTOR_X-AXIS= 1.0 0.0 0.0
        DIRECTION_OF_DETECTOR_Y-AXIS= 0.0 1.0 0.0
        ROTATION_AXIS= 0.0 -1.0 0.0
        INCIDENT_BEAM_DIRECTION=0.0 0.0 1.0
        NX=4150 NY=4371 QX=0.075 QY=0.075
        ORGX=2091.8997 ORGY=2182.7866
        DETECTOR_DISTANCE= 321.616
        X-RAY_WAVELENGTH= 0.9763
        OSCILLATION_RANGE= 0.2000
        STARTING_ANGLE= 51.2500
        DATA_RANGE= 1 920

        """
        # Take the first sub webge in input as reference
        listImage = inData['image']
        image = listImage[0]
        listDozorSpotFile = image['dozorSpotFile']
        experimentalCondition = image['experimentalCondition']
        detector = experimentalCondition['detector']
        beam = experimentalCondition['beam']
        goniostat = experimentalCondition['goniostat']
        detecorType = detector['type']
        nx = UtilsDetector.getNx(detecorType)
        ny = UtilsDetector.getNy(detecorType)
        pixel = UtilsDetector.getPixelsize(detecorType)
        orgY = round(detector['beamPositionX'] / pixel, 3)
        orgX = round(detector['beamPositionY'] / pixel, 3)
        distance = round(detector['distance'], 3)
        wavelength = round(beam['wavelength'], 3)
        oscRange = round(goniostat['oscillationWidth'])
        startAngle = goniostat['rotationAxisStart'] - int(goniostat['rotationAxisStart'])
        dataRange = '1 360'
        self.writeSPOT_XDS(listDozorSpotFile, oscRange)
        listXDS_INP = [
            'OVERLOAD=10048500',
            'DIRECTION_OF_DETECTOR_X-AXIS={0}'.format(UtilsConfig.get('XDSTask', 'DIRECTION_OF_DETECTOR_X-AXIS')),
            'DIRECTION_OF_DETECTOR_Y-AXIS={0}'.format(UtilsConfig.get('XDSTask', 'DIRECTION_OF_DETECTOR_Y-AXIS')),
            'ROTATION_AXIS={0}'.format(UtilsConfig.get('XDSTask', 'ROTATION_AXIS')),
            'INCIDENT_BEAM_DIRECTION={0}'.format(UtilsConfig.get('XDSTask', 'INCIDENT_BEAM_DIRECTION')),
            'NX={0} NY={1} QX={2} QY={2}'.format(nx, ny, pixel),
            'ORGX={0} ORGY={1}'.format(orgX, orgY),
            'DETECTOR_DISTANCE={0}'.format(distance),
            'X-RAY_WAVELENGTH={0}'.format(wavelength),
            'OSCILLATION_RANGE={0}'.format(oscRange),
            'STARTING_ANGLE={0}'.format(startAngle),
            'DATA_RANGE={0}'.format(dataRange)
        ]
        return listXDS_INP

    @staticmethod
    def createSPOT_XDS(listDozorSpotFile, oscRange):
        """
              implicit none
              integer nmax
              parameter(nmax=10000000)
              real*4 x(3),j
              integer n,i,k
              real*4 xa(nmax,3),ja(nmax)
              logical new
        c
              n=0
              do while(.true.)
                 read(*,*,err=1,end=1)x,j
                 new = .true.
                 do i = n,1,-1
                    if (abs(xa(i,3)-x(3)) .gt. 20.0 ) goto 3
                    do k = 1,2
                       if (abs(x(k)-xa(i,k)) .gt. 6.0) goto 2
                    enddo
                    new = .false.
                    xa(i,:)=(xa(i,:)*ja(i)+x*j)/(ja(i)+j)
                    ja(i)=ja(i)+j
          2         continue
                 enddo
          3       if (new) then
                    n=n+1
                    xa(n,:)=x
                    ja(n)=j
                 endif
              enddo
          1   continue
              do i=1,n
                 write(*,*)xa(i,:), ja(i)
              enddo
              end
        """
        listSpotXds = []
        n = 0
        firstFrame = True
        for dozorSpotFile in listDozorSpotFile:
            # Read the file
            with open(str(dozorSpotFile)) as f:
                dozorLines = f.readlines()
            omega = float(dozorLines[2].split()[1])
            frame = int((omega - oscRange/2)/oscRange) + 1
            frame = frame % 360
            for dozorLine in dozorLines[3:]:
                new = True
                listValues = dozorLine.split()
                n, xPos, yPos, intensity, sigma = list(map(float, listValues))
                # Subtracting 1 from X and Y: this is because for dozor the upper left pixel in the image is (1,1),
                # whereas for the rest of the world it is (0,0)
                xPos = xPos - 1
                yPos = yPos - 1
                index = 0
                for spotXds in listSpotXds:
                    frameOld = spotXds[2]
                    if abs(frameOld - frame) > 20:
                        break
                    xPosOld = spotXds[0]
                    yPosOld = spotXds[1]
                    intensityOld = spotXds[3]
                    if abs(xPosOld - xPos) <= 6 and abs(yPosOld - yPos) <= 6:
                        new = False
                        intensityNew = intensity + intensityOld
                        xPosNew = (xPosOld*intensityOld + xPos*intensity) / intensityNew
                        yPosNew = (yPosOld*intensityOld + yPos*intensity) / intensityNew
                        listSpotXds[index] = [xPosNew, yPosNew, frameOld, intensityNew]
                    index += 1

                if new:
                    spotXds = [xPos, yPos, frame, intensity]
                    listSpotXds.append(spotXds)


        strSpotXds = ''
        for spotXds in listSpotXds:
            strSpotXds += '{0:13.6f}{1:17.6f}{2:17.8f}{3:17.6f}    \n'.format(*spotXds)
        return strSpotXds

    def writeSPOT_XDS(self, listDozorSpotFile, oscRange):
        spotXds = self.createSPOT_XDS(listDozorSpotFile, oscRange)
        filePath = self.getWorkingDirectory() / 'SPOT.XDS'
        with open(str(filePath), 'w') as f:
            f.write(spotXds)

    def writeXDS_INP(self, listXDS_INP, workingDirectory):
        fileName = 'XDS.INP'
        filePath = workingDirectory / fileName
        with open(str(filePath), 'w') as f:
            for line in listXDS_INP:
                f.write(line + '\n')


class XDSIndexingTask(XDSTask):

    def generateXDS_INP(self, inData):
        listXDS_INP = XDSTask.generateXDS_INP(self, inData)
        listXDS_INP.insert(0, 'JOB= IDXREF')
        return listXDS_INP

    @staticmethod
    def parseXDSOutput(workingDirectory):
        idxrefPath = workingDirectory / 'IDXREF.LP'
        xparmPath = workingDirectory / 'XPARM.XDS'
        outData = {
            "idxref":  XDSIndexingTask.readIdxrefLp(idxrefPath),
            "xparm":   XDSIndexingTask.parseXparm(xparmPath)
        }
        return outData


    @staticmethod
    def readIdxrefLp(pathToIdxrefLp, resultXDSIndexing=None):
        if resultXDSIndexing is None:
            resultXDSIndexing = {}
        if pathToIdxrefLp.exists():
            with open(str(pathToIdxrefLp)) as f:
                listLines = f.readlines()
            indexLine = 0
            doParseParameters = False
            doParseLattice = False
            while indexLine < len(listLines):
                if "DIFFRACTION PARAMETERS USED AT START OF INTEGRATION" in listLines[indexLine]:
                    doParseParameters = True
                    doParseLattice = False
                elif "DETERMINATION OF LATTICE CHARACTER AND BRAVAIS LATTICE" in listLines[indexLine]:
                    doParseParameters = False
                    doParseLattice = True
                if doParseParameters:
                    if "MOSAICITY" in listLines[indexLine]:
                        resultXDSIndexing['mosaicity'] = float(listLines[indexLine].split()[-1])
                    elif "DETECTOR COORDINATES (PIXELS) OF DIRECT BEAM" in listLines[indexLine]:
                        resultXDSIndexing['xBeam'] = float(listLines[indexLine].split()[-1])
                        resultXDSIndexing['yBeam'] = float(listLines[indexLine].split()[-2])
                    elif "CRYSTAL TO DETECTOR DISTANCE" in listLines[indexLine]:
                        resultXDSIndexing['distance'] = float(listLines[indexLine].split()[-1])
                elif doParseLattice:
                    if listLines[indexLine].startswith(" * ") and not listLines[indexLine + 1].startswith(" * "):
                        listLine = listLines[indexLine].split()
                        latticeCharacter = int(listLine[1])
                        bravaisLattice = listLine[2]
                        spaceGroup = UtilsSymmetry.getMinimumSymmetrySpaceGroupFromBravaisLattice(bravaisLattice)
                        spaceGroupNumber = UtilsSymmetry.getITNumberFromSpaceGroupName(spaceGroup)
                        qualityOfFit = float(listLine[3])
                        resultXDSIndexing.update( {
                            'latticeCharacter': latticeCharacter,
                            'spaceGroupNumber': spaceGroupNumber,
                            'qualityOfFit': qualityOfFit,
                            'a': float(listLine[4]),
                            'b': float(listLine[5]),
                            'c': float(listLine[6]),
                            'alpha': float(listLine[7]),
                            'beta':  float(listLine[8]),
                            'gamma': float(listLine[9])
                        } )
                indexLine += 1
        return resultXDSIndexing

    @staticmethod
    def volum(cell):
        """
        Calculate the cell volum from either:
         - the 6 standard cell parameters (a, b, c, alpha, beta, gamma)
         - or the 3 vectors A, B, C
        Inspired from XOconv written by Pierre Legrand:
        https://github.com/legrandp/xdsme/blob/67001a75f3c363bfe19b8bd7cae999f4fb9ad49d/XOconv/XOconv.py#L758        """
        r2d = 180 / math.pi
        cosd = lambda a: math.cos(a / r2d)
        if len(cell) == 6 and isinstance(cell[0], float):
            # expect a, b, c, alpha, beta, gamma (angles in degree).
            ca, cb, cg = map(cosd, cell[3:6])
            return cell[0] * cell[1] * cell[2] * (1 - ca ** 2 - cb ** 2 - cg ** 2 + 2 * ca * cb * cg) ** 0.5
        elif len(cell) == 3 and isinstance(cell[0], np.array):
            # expect vectors of the 3 cell parameters
            A, B, C = cell
            return A * B.cross(C)
        else:
            return "Can't parse input arguments."

    @staticmethod
    def reciprocal(cell):
        """
        Calculate the 6 reciprocal cell parameters: a*, b*, c*, alpha*, beta*...
        Inspired from XOconv written by Pierre Legrand:
        https://github.com/legrandp/xdsme/blob/67001a75f3c363bfe19b8bd7cae999f4fb9ad49d/XOconv/XOconv.py#L776
        """
        r2d = 180 / math.pi
        cosd = lambda a: math.cos(a / r2d)
        sind = lambda a: math.sin(a / r2d)
        sa, sb, sg = map(sind, cell[3:6])
        ca, cb, cg = map(cosd, cell[3:6])
        v = XDSIndexingTask.volum(cell)
        rc = (cell[1] * cell[2] * sa / v,
              cell[2] * cell[0] * sb / v,
              cell[0] * cell[1] * sg / v,
              math.acos((cb * cg - ca) / (sb * sg)) * r2d,
              math.acos((ca * cg - cb) / (sa * sg)) * r2d,
              math.acos((ca * cb - cg) / (sa * sb)) * r2d)
        return rc

    @staticmethod
    def BusingLevy(rcell):
        """
        Inspired from XOconv written by Pierre Legrand:
        https://github.com/legrandp/xdsme/blob/67001a75f3c363bfe19b8bd7cae999f4fb9ad49d/XOconv/XOconv.py#L816
        """
        ex = np.array([1,0,0])
        ey = np.array([0,1,0])
        r2d = 180 / math.pi
        cosd = lambda a: math.cos(a / r2d)
        sind = lambda a: math.sin(a / r2d)
        cosr = list(map(cosd, rcell[3:6]))
        sinr = list(map(sind, rcell[3:6]))
        Vr = XDSIndexingTask.volum(rcell)
        BX = ex * rcell[0]
        BY = rcell[1] * (ex * cosr[2] + ey * sinr[2])
        c = rcell[0] * rcell[1] * sinr[2] / Vr
        cosAlpha = (cosr[1] * cosr[2] - cosr[0]) / (sinr[1] * sinr[2])
        BZ = np.array([rcell[2] * cosr[1],
                   -1 * rcell[2] * sinr[1] * cosAlpha,
                   1 / c])
        return np.array([BX, BY, BZ]).transpose()

    @staticmethod
    def parseXparm(pathToXparmXds):
        """
        Inspired from parse_xparm written by Pierre Legrand:
        https://github.com/legrandp/xdsme/blob/67001a75f3c363bfe19b8bd7cae999f4fb9ad49d/XOconv/XOconv.py#L372
        """
        with open(str(pathToXparmXds)) as f:
            xparm = f.readlines()
        xparamDict = {
            "rot":          list(map(float, xparm[1].split()[3:])),
            "beam":         list(map(float, xparm[2].split()[1:])),
            "distance":     float(xparm[8].split()[2]),
            "originXDS":    list(map(float, xparm[8].split()[:2])),
            "A":            list(map(float, xparm[4].split())),
            "B":            list(map(float, xparm[5].split())),
            "C":            list(map(float, xparm[6].split())),
            "cell":         list(map(float, xparm[3].split()[1:])),
            "pixel_size":   list(map(float, xparm[7].split()[3:])),
            "pixel_numb":   list(map(float, xparm[7].split()[1:])),
            "symmetry":     int(xparm[3].split()[0]),
            "num_init":     list(map(float, xparm[1].split()[:3]))[0],
            "phi_init":     list(map(float, xparm[1].split()[:3]))[1],
            "delta_phi":    list(map(float, xparm[1].split()[:3]))[2],
            "detector_X":   list(map(float, xparm[9].split())),
            "detector_Y":   list(map(float, xparm[10].split()))
        }
        A = np.array(xparamDict["A"])
        B = np.array(xparamDict["B"])
        C = np.array(xparamDict["C"])

        volum = np.cross(A, B).dot(C)
        Ar = np.cross(B, C) / volum
        Br = np.cross(C, A) / volum
        Cr = np.cross(A, B) / volum
        UBxds = np.array([Ar, Br, Cr]).transpose()

        BEAM = np.array(xparamDict["beam"])
        ROT = np.array(xparamDict["rot"])
        wavelength = 1 / np.linalg.norm(BEAM)

        xparamDict["cell_volum"] = volum
        xparamDict["wavelength"] = wavelength
        xparamDict["Ar"] = Ar.tolist()
        xparamDict["Br"] = Br.tolist()
        xparamDict["Cr"] = Cr.tolist()
        xparamDict["UB"] = UBxds.tolist()

        normROT = float(np.linalg.norm(ROT))
        CAMERA_z = np.true_divide(ROT, normROT)
        CAMERA_y = np.cross(CAMERA_z, BEAM)
        normCAMERA_y = float(np.linalg.norm(CAMERA_y))
        CAMERA_y = np.true_divide(CAMERA_y, normCAMERA_y)
        CAMERA_x = np.cross(CAMERA_y, CAMERA_z)
        CAMERA = np.transpose(np.array([CAMERA_x, CAMERA_y, CAMERA_z]))

        mosflmUB = CAMERA.dot(UBxds)*xparamDict["wavelength"]
        # mosflmUB = UBxds*xparamDict["wavelength"]
        xparamDict["mosflmUB"] = mosflmUB.tolist()

        reciprocCell = XDSIndexingTask.reciprocal(xparamDict["cell"])
        B = XDSIndexingTask.BusingLevy(reciprocCell)
        mosflmU = np.dot(mosflmUB, np.linalg.inv(B)) / xparamDict["wavelength"]
        xparamDict["mosflmU"] = mosflmU.tolist()
        return xparamDict

