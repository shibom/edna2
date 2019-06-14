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

# Corresponding EDNA code:
# https://github.com/olofsvensson/edna-mx
# kernel/src/EDUtilsImage.py

import re
import pathlib


def __compileAndMatchRegexpTemplate(pathToImage):
    listResult = []
    if not isinstance(pathToImage, pathlib.Path):
        pathToImage = pathlib.Path(str(pathToImage))
    baseImageName = pathToImage.name
    regexp = re.compile(r'(.*)([^0^1^2^3^4^5^6^7^8^9])([0-9]*)\.(.*)')
    match = regexp.match(baseImageName)
    if match is not None:
        listResult = [
            match.group(0),
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4)
        ]
    return listResult


def getImageNumber(pathToImage):
    iImageNumber = None
    listResult = __compileAndMatchRegexpTemplate(pathToImage)
    if listResult is not None:
        iImageNumber = int(listResult[3])
    return iImageNumber


def getTemplate(pathToImage, symbol="#"):
    template = None
    listResult = __compileAndMatchRegexpTemplate(pathToImage)
    if listResult is not None:
        prefix = listResult[1]
        separator = listResult[2]
        imageNumber = listResult[3]
        suffix = listResult[4]
        hashes = ""
        for i in range(len(imageNumber)):
            hashes += symbol
        template = prefix + separator + hashes + "." + suffix
    return template


def getPrefix(pathToImage):
    prefix = None
    listResult = __compileAndMatchRegexpTemplate(pathToImage)
    if listResult is not None:
        prefix = listResult[1]
    return prefix


def getSuffix(pathToImage):
    suffix = None
    listResult = __compileAndMatchRegexpTemplate(pathToImage)
    if listResult is not None:
        suffix = listResult[4]
    return suffix
