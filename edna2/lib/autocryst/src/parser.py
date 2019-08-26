#
# Copyright (c) European Molecular Biology Laboratory (EMBL)
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

__author__ = ['S. Basu']
__license__ = 'MIT'
__date__ = '2019/08/16'

import logging
import pathlib
import json
import sys

logger = logging.getLogger('autoCryst')


class ResultParser(object):
    def __init__(self):
        self._ioDict = dict()
        self._ioDict['outData'] = json.dumps(dict(), default=str)
        self._ioDict['success'] = True
        return

    def get_outData(self):
        return json.loads(self._ioDict['outData'])

    def set_outData(self, results):
        self._ioDict['outData'] = json.dumps(results, default=str)

    results = property(get_outData, set_outData)

    def is_success(self):
        return self._ioDict['success']

    def setFailure(self):
        self._ioDict['success'] = False

    def stat_parser(self, statfile, fom='snr'):
        output = dict()
        output['DataQuality'] = []
        count = 1
        statfile = pathlib.Path(statfile)
        if statfile.exists():
            statfh = open(statfile, 'r')
            _all = statfh.readlines()
            statfh.close()
        else:
            self.setFailure()
            logger.error('IOError:{}'.format('%s File not found' % statfile))
            return output
        for lines in _all:
            if 'd(A)' in lines:
                pass
            else:
                line = lines.split()
                if len(line) == 12 and fom == 'snr':
                    each_row = dict()
                    each_row['order'] = count
                    each_row['q'] = '%4.3f' % (float(line[0]) / 10)
                    each_row['unique_refs'] = int(line[1])
                    each_row['possible_refs'] = int(line[2])
                    each_row['completeness'] = float(line[3])
                    each_row['total_refs'] = int(line[4])
                    each_row['multiplicity'] = float(line[5])
                    each_row['snr'] = float(line[6])
                    each_row['std_dev'] = float(line[7])
                    each_row['mean'] = float(line[8])
                    each_row['resolution'] = float(line[9])
                    output['DataQuality'].append(each_row)
                    count += 1
                elif len(line) == 6:
                    each_row = dict()
                    each_row['order'] = count
                    each_row['q'] = float(line[0]) / 10
                    each_row['resolution'] = float(line[3])
                    each_row['refs_common'] = int(line[2])
                    each_row[fom] = float(line[1])
                    output['DataQuality'].append(each_row)
                    count += 1
                else:
                    self.setFailure()
                    logger.error('statError:{}'.format('Error in reading the file'))
        return output

    def getstats(self, statfile, fom):
        stat = self.stat_parser(statfile, fom)
        self.set_outData(stat)
        return

    def writeOutputFile(self, stat):
        self.set_outData(stat)
        jsonName = "outData_" + self.__class__.__name__ + ".json"
        with open(str(jsonName), 'w') as f:
            f.write(json.dumps(self.results, default=str, indent=4))
        return


if __name__ == '__main__':
    statparse = ResultParser()
    statparse.getstats(sys.argv[1], fom='snr')
    print(statparse.results)
