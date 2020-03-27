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
__date__ = '26/03/2020'

DETECTOR_PARAMS = {
    'pilatus2m': {
        'nx': 1475,
        'ny': 1679,
        'pixel': 0.172
    },
    'pilatus6m': {
        'nx': 2463,
        'ny': 2527,
        'pixel': 0.172
    },
    'eiger4m': {
        'nx': 2070,
        'ny': 2167,
        'pixel': 0.075
    }
}


def getNxNyPixelsize(detectorType):
    if detectorType in DETECTOR_PARAMS:
        p = DETECTOR_PARAMS[detectorType]
        return p['nx'], p['ny'], p['pixel']
    else:
        raise RuntimeError('Detector type "{0}" not defined in UtilsDetector.py!')
