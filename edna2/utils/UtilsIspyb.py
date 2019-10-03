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

__authors__ = ['O. Svensson']
__license__ = 'MIT'
__date__ = '05/09/2019'

import os
import json
import requests

from edna2.utils import UtilsLogging

logger = UtilsLogging.getLogger()


def getDataFromURL(url):
    if "http_proxy" in os.environ:
        os.environ["http_proxy"] = ""
    response = requests.get(url)
    data = {
        'statusCode': response.status_code
    }
    if response.status_code == 200:
        data['data'] = json.loads(response.text)[0]
    else:
        data['text'] = response.text
    return data


def getRawDataFromURL(url):
    if "http_proxy" in os.environ:
        os.environ["http_proxy"] = ""
    response = requests.get(url)
    data = {
        'statusCode': response.status_code
    }
    if response.status_code == 200:
        data['content'] = response.content
    else:
        data['text'] = response.text
    return data
