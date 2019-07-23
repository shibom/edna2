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

from __future__ import division, print_function
import os
import sys
from datetime import datetime
import json
import logging


import edna2.lib.autocryst.src.saveDozor as sd
from edna2.lib.autocryst.src.crystfel_utils import Utils

from edna2.tasks.AbstractTask import AbstractTask
from edna2.utils import UtilsLogging


__author__ = ['S. Basu']
__license__ = 'MIT'
__date__ = '05/07/2019'

logger = UtilsLogging.getLogger()


class ExeCrystFEL(AbstractTask):

    def run(self, inData):
        outData = {}
        self.setWorkingDirectory(inData)
        dd = sd.Dozor(inData)
        dd.extract_olof_json(inData)
        dd.workingDir = self.getWorkingDirectory()
        headerfile = dd.workingDir / 'headers.json'
        if dd.success:
            os.chdir(str(dd.workingDir))
            if not headerfile.exists():
                with open(str(headerfile), 'w') as jhead:
                    json.dump(dd.cbfheader, jhead, sort_keys=True, indent=2)
            else:
                pass

            if dd.stacklength <= 100:
                dd.create_stack()
            else:
                dd.mp_stack()
            try:
                cxi_all = list(dd.workingDir.glob('dozor*cxi'))
                current = len(cxi_all) - 1
                prefix = 'dozor_%d' % current
                args = dict()
                args['peak_search'] = 'cxi'
                args['peak_info'] = '/data/peakinfo'
                args['highres'] = '4.0'
                # cwd = self.getWorkingDirectory()  # - this yielded None type, which is default value

                cryst = Utils(str(dd.workingDir), prefix, 'cxi', **args)
                cryst.find_files()
                cryst.crystfel_dir = str(dd.workingDir)

                geomfile = list(dd.workingDir.glob('*.geom'))
                if len(geomfile) > 0:
                    cryst.geometry_file = geomfile[0]
                else:
                    kk = {'cxi': """dim0 = %\ndim1 = ss\ndim2 = fs\ndata = /data/data\n"""}
                    cryst.make_geomfile(**kk)

                cryst.make_list_events()

                if len(cryst.filelist) > 10 and os.path.isfile(cryst.geometry_file):

                    nchunk = len(cryst.filelist) // 10
                    for jj in range(nchunk):
                        start = 10 * jj
                        stop = 10 * (jj + 1)
                        try:
                            images = cryst.filelist[start:stop]
                        except IndexError:
                            stop = start + (len(cryst.filelist) - stop)
                            images = cryst.filelist[start:stop]

                        cryst.infile = os.path.join(cryst.crystfel_dir, ('%d.lst' % jj))
                        cryst.outstream = os.path.join(cryst.crystfel_dir, ('%d.stream' % jj))
                        shellfile = os.path.join(cryst.crystfel_dir, ('%d.sh' % jj))
                        ofh = open(cryst.infile, 'w')
                        for fname in images:
                            ofh.write(fname)
                            ofh.write('\n')
                        ofh.close()

                        if Utils.is_executable('oarsub'):
                            Utils.oarshell_submit(shellfile, cryst.indexamajig_cmd())
                        else:
                            self.runCommandLine(cryst.indexamajig_cmd())
                    cryst.check_oarstat()

                elif len(cryst.filelist) <= 10 and os.path.isfile(cryst.geometry_file):

                    cryst.infile = os.path.join(os.getcwd(), 'input.lst')
                    outname = datetime.now().strftime('%H-%M-%S.stream')
                    cryst.outstream = os.path.join(cryst.crystfel_dir, outname)

                    ofh = open(cryst.infile, 'w')
                    for fname in cryst.filelist:
                        ofh.write(fname)
                        ofh.write('\n')
                    ofh.close()

                    cmd = cryst.indexamajig_cmd()
                    self.runCommandLine(cmd)

                if cryst.status and os.path.exists(cryst.outstream):
                    cryst.report_stats(cryst.outstream)
                    logger.info("MeshScan-results:{}".format(cryst.results))
                    outData = cryst.results

                else:
                    logger.info("Error:{}".format("crystfel pipeline has errors"))
                    cryst.status = False
                    self.setFailure()
            except Exception as err:
                logger.error("Error-crystfel:{}".format(err))
                dd.success = False
                self.setFailure()

        else:
            logger.error("something not correct with ImageQualityIndicator parsing")
            dd.success = False
        return outData

    @staticmethod
    def run_in_batch_mode(procdir, filelist, command):
        if len(filelist) == 0 or os.path.exists(procdir) is False:
            logger.debug("filelist empty or procdir does not exist")
            return
        nchunk = len(procdir) // 10
        for jj in range(nchunk):
            start = 10 * jj
            stop = 10 * (jj + 1)
            try:
                images = filelist[start:stop]
            except IndexError:
                stop = start + (len(filelist) - stop)
                images = filelist[start:stop]

            infile = os.path.join(procdir, ('%d.lst' % jj))
            outstream = os.path.join(procdir, ('%d.stream' % jj))
            shellfile = os.path.join(procdir, ('%d.sh' % jj))
            ofh = open(infile, 'w')
            for fname in range(images):
                ofh.write(fname)
                ofh.write('\n')
            ofh.close()

            if Utils.is_executable('oarsub'):
                Utils.oarshell_submit(shellfile, command)
            else:
                pass
        return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s%(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='autocryst.log',
                        filemode='a+')
    fh = open(sys.argv[1], 'r')
    inData = json.load(fh)
    fh.close()
    crystfel = ExeCrystFEL(inData)
    result = crystfel.run(inData)
    print(result)
