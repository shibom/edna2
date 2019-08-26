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
__date__ = '2019/08/08'


import os
import pathlib
import json
import jsonschema
import logging
import subprocess as sub
import time
from collections import Counter
from datetime import datetime

from edna2.lib.autocryst.src.Image import ImageHandler as Im
from edna2.lib.autocryst.src.cell_analysis import Cell
from edna2.lib.autocryst.src.geom import Geom
from edna2.lib.autocryst.src.point_group import *
from edna2.lib.autocryst.src.stream import Stream
from edna2.lib.autocryst.src.parser import ResultParser

logger = logging.getLogger('autoCryst')


class AutoCrystFEL(object):
    """

    :rtype: object to run CrystFEL at ESRF or elsewhere as an automated workflow.
    One can run it as a module with required dependencies. It is part of autocryst project
    Input and output - both are json dictionaries. One can run it on commandLine.
    python run_crystfel.py --help : check how to run as commandLine, which essentially calls AutoCrystFEL
    as a module and creates necessary input dictionary based on commandLine.

    """
    def __init__(self, jData):
        self._ioDict = dict()
        self._ioDict['inData'] = json.dumps(jData, default=str)
        self._ioDict['outData'] = json.dumps(dict(), default=str)
        self._ioDict['success'] = True
        self._ioDict['crystFEL_WorkingDirectory'] = None
        self.filelist = []
        return

    def get_inData(self):
        return json.loads(self._ioDict['inData'])

    def set_inData(self, jData):
        self._ioDict['inData'] = json.dumps(jData, default=str)

    jshandle = property(get_inData, set_inData)

    def get_outData(self):
        return json.loads(self._ioDict['outData'])

    def set_outData(self, results):
        self._ioDict['outData'] = json.dumps(results, default=str)

    results = property(get_outData, set_outData)

    def writeInputData(self, inData):
        # Write input data
        if self._ioDict['crystFEL_WorkingDirectory'] is not None:
            jsonName = "inData_" + self.__class__.__name__ + ".json"
            with open(str(self.getOutputDirectory() / jsonName), 'w') as f:
                f.write(json.dumps(inData, default=str, indent=4))
        return

    def writeOutputData(self, results):
        self.set_outData(results)
        if self._ioDict['crystFEL_WorkingDirectory'] is not None:
            jsonName = "outData_" + self.__class__.__name__ + ".json"
            with open(str(self.getOutputDirectory() / jsonName), 'w') as f:
                f.write(json.dumps(results, default=str, indent=4))
        return

    def setFailure(self):
        self._ioDict['success'] = False

    def is_success(self):
        return self._ioDict['success']

    def setOutputDirectory(self, path=None):
        if path is None:
            directory = self.jshandle.get('processing_directory', os.getcwd())
            self._ioDict['crystFEL_WorkingDirectory'] = pathlib.Path(directory)
        else:
            self._ioDict['crystFEL_WorkingDirectory'] = pathlib.Path(path)

    def getOutputDirectory(self):
        return self._ioDict['crystFEL_WorkingDirectory']

    @staticmethod
    def getInDataSchema():
        return {
            "type": "object",
            "required": ["image_directory", "detectorType", "prefix", "suffix"],
            "properties": {
                "image_directory": {"type": "string"},
                "detectorType": {"type": "string"},
                "suffix": {"type": "string"},
                "prefix": {"type": "string"},
                "maxchunksize": {"type": "integer"},
                "processing_directory": {"type": "string"},
                "doMerging": {"type": "boolean"},
                "GeneratePeaklist": {"type": "boolean"},
                "geometry_file": {"type": "string"},
                "unit_cell_file": {"type": "string"},
                "num_processors": {"type": "string"},
                "beamline": {"type": "string"},
                "indexing_method": {"type": "string"},
                "peak_search": {"type": "string"},
                "peak_info": {"type": "string"},
                "int_method": {"type": "string"},
                "peak_radius": {"type": "string"},
                "int_radius": {"type": "string"},
                "min_peaks": {"type": "string"},
                "min_snr": {"type": "string"},
                "threshold": {"type": "string"},
                "local_bg_radius": {"type": "string"},
                "min_res": {"type": "string"},
                "highres": {"type": "string"}
            },
        }

    @staticmethod
    def getOutDataSchema():
        return {
            "type": "object",
            "properties": {
                "QualityMetrics": {
                    "type": "object",
                    "properties": {
                        "centering": {"type": "string"},
                        "num_indexed_frames": {"type": "integer"},
                        "lattice": {"type": "string"},
                        "unique_axis": {"type": "string"},
                        "unit_cell": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                        "point_group": {"type": "string"},
                        "space_group": {"type": "string"},
                        "resolution_limit": {"type": "number"},
                        "average_num_spots": {"type": "number"}
                    }
                },
                "PeaksDictionary": {
                    "type": "object",
                    "properties": {
                        "items": {"type": "array"},
                    }
                }
            }
        }

    @staticmethod
    def is_executable(program):
        def is_exe(filepath):
            return os.path.isfile(filepath) and os.access(filepath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            return is_exe(program)

        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return True

        return

    @staticmethod
    def run_as_command(command):
        pipes = sub.Popen(command, shell=True, stdout=sub.PIPE, stderr=sub.PIPE, cwd=os.getcwd())
        stdout, stderr = pipes.communicate()
        if pipes.returncode != 0:
            err = '{0}, code {1}'.format(stderr, pipes.returncode)
            logger.error('Error:'.format(err))
        return

    @staticmethod
    def oarshell_submit(shellfile, crystfel_cmd):
        oar_handle = open(shellfile, 'w')

        oar_handle.write("#!/bin/bash \n\n")

        oar_handle.write("#OAR -q mx \n")
        oar_handle.write("#OAR -n autoCryst \n")
        oar_handle.write("#OAR -l nodes=1, walltime=01:00:00 \n\n")
        oar_handle.write(crystfel_cmd)
        oar_handle.close()
        sub.call('chmod +x %s' % shellfile, shell=True)

        AutoCrystFEL.run_as_command('oarsub -S %s' % shellfile)
        return

    @staticmethod
    def slurm_submit(shellfile, crystfel_cmd):
        slurm_handle = open(shellfile, 'w')
        slurm_handle.write("#!/bin/bash \n\n")
        slurm_handle.write(crystfel_cmd)
        slurm_handle.close()
        sub.call('chmod +x %s' % shellfile, shell=True)

        AutoCrystFEL.run_as_command('sbatch -p mx -J autoCryst %s' % shellfile)
        return

    @staticmethod
    def combine_streams():
        slurm_handle = open('tmp_cat.sh', 'w')
        slurm_handle.write("#!/bin/bash \n\n")
        slurm_handle.write("cat *.stream >> alltogether.stream")
        slurm_handle.close()
        AutoCrystFEL.run_as_command('chmod +x tmp_cat.sh')
        AutoCrystFEL.run_as_command('sbatch -d singleton -J autoCryst -t 1:00 tmp_cat.sh')
        return

    @staticmethod
    def partialator_cmd(stream_name, point_group, nproc):
        base_str = stream_name.split('.')
        outhkl = base_str[0] + '.hkl'
        command = 'partialator -i %s -o %s -y %s ' \
                  % (stream_name, outhkl, point_group)
        command += ' --model=unity --push-res=1.5 --iterations=1 -j %s --no-deltacchalf --no-logs' % nproc

        return command

    @staticmethod
    def check_hkl_cmd(hklfile, point_group, cellfile, rescut):
        statfile = hklfile.split('.')[0] + '_snr.dat'
        command = 'check_hkl -y %s -p %s --nshells=20 --shell-file=%s ' \
                  % (point_group, cellfile, statfile)
        command += '--lowres=20 --highres=%f %s' % (rescut, hklfile)

        return command

    @staticmethod
    def compare_hkl_cmd(hkl1, hkl2, cellfile, rescut, fom='CCstar'):
        base_str = hkl1.split('.')[0]
        statout = base_str + '_' + fom + '.dat'

        command = 'compare_hkl -p %s --nshells=20 --shell-file=%s ' % (cellfile, statout)
        command += '--fom=%s --lowres=20 --highres=%s ' % (fom, rescut)
        command += '%s %s' % (hkl1, hkl2)
        return command

    @staticmethod
    def write_cell_file(cellinfo):
        #  Method to write out crystFEL formatted *.cell file, compatible with other crystFEL programs
        try:
            cwrite = open('auto.cell', 'w')
            cwrite.write('CrystFEL unit cell file version 1.0\n\n')
            cwrite.write('lattice_type = %s\n' % cellinfo['lattice'])
            cwrite.write('centering = %s\n' % cellinfo['centering'])
            cwrite.write('unique_axis = %s\n' % cellinfo['unique_axis'])
            cwrite.write('a = %s A\n' % cellinfo['unit_cell'][0])
            cwrite.write('b = %s A\n' % cellinfo['unit_cell'][1])
            cwrite.write('c = %s A\n' % cellinfo['unit_cell'][2])
            cwrite.write('al = %s deg\n' % cellinfo['unit_cell'][3])
            cwrite.write('be = %s deg\n' % cellinfo['unit_cell'][4])
            cwrite.write('ga = %s deg\n' % cellinfo['unit_cell'][5])
            cwrite.close()

        except (OSError, KeyError) as err:
            logger.info('Cell_file_Error:{}'.format(err))
            print("Needed a dictionary with keys: lattice, centering, unique_axis, and unit_cell\n")
            print("unit_cell key has a list of cell parameters as value")
            raise err
        return

    def datafinder(self):
        datadir = pathlib.Path(self.jshandle['image_directory'])
        if datadir.exists():
            listofimagefiles = list(datadir.glob(self.jshandle['prefix'] + '*' + self.jshandle['suffix']))
            for fname in listofimagefiles:
                if 'master' not in str(fname):
                    self.filelist.append(fname.as_posix())
                else:
                    pass
        else:
            self.setFailure()
            logger.error('dataError:{}'.format('no data found'))
        return

    def makeOutputDirectory(self):
        self.setOutputDirectory()
        datadir = pathlib.Path(self.jshandle['image_directory'])
        image_folder_basename = datadir.name
        image_folder_structure = datadir.parents
        procdir = self.getOutputDirectory() / image_folder_structure[0].name / image_folder_basename
        outname = datetime.now().strftime('autoCryst_%Y-%m-%d_%H-%M-%S')
        crystfel_dir = procdir / outname
        crystfel_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(str(crystfel_dir))
        self.setOutputDirectory(str(crystfel_dir))
        return

    def make_geometry_file(self, **kwargs):
        geomfile = self.jshandle.get('geometry_file', None)
        if geomfile is None:
            image1 = type('', (), {})  # initialize image1 as an empty object
            if self.jshandle['detectorType'] == 'pilatus2m' or self.jshandle['detectorType'] == 'pilatus6m':
                image1 = Im(self.filelist[0])
            elif self.jshandle['detectorType'] == 'eiger4m':
                master_str = self.jshandle['prefix'] + '*master.h5'
                masterfile = list(pathlib.Path(self.jshandle['image_directory']).glob(master_str))[0]
                image1 = Im(str(masterfile))
            else:
                self.setFailure()
                logger.error('format_error:{}'.format('cbf/h5/cxi formats supported'))
            g = Geom(image1.imobject.headers['detector_name'][0], image1.imobject.headers['detector_name'][1])
            g.write_geomfile(image1.imobject.headers, **kwargs)
            geomfile = self.getOutputDirectory() / g.geomfilename
        else:
            geomfile = pathlib.Path(geomfile)
        return geomfile

    def make_list_events(self, geometryfile):
        if self.jshandle['suffix'] == 'cxi' or self.jshandle['suffix'] == 'h5':
            datalst = str(self.getOutputDirectory() / 'input.lst')
            fh = open(datalst, 'w')
            for fname in self.filelist:
                fh.write(fname)
                fh.write('\n')
            fh.close()
            if os.path.exists(geometryfile):
                self.filelist = []
                all_events = str(self.getOutputDirectory() / 'all_events.lst')
                cmd = 'list_events -i %s -g %s -o %s' % (datalst, geometryfile, all_events)
                self.run_as_command(cmd)
                f = open(all_events, 'r')
                for line in f:
                    line = line.strip('\n')
                    self.filelist.append(line)
                f.close()
            else:
                self.setFailure()
                logger.error('List_events_Error:No Geom file exists')
        else:
            # cbf files are not multi-events
            pass
        return

    def indexamajig_cmd(self, infile, streamfile, geometryfile):
        command = ""
        unitcell = self.jshandle.get('unit_cell_file', None)
        indexing_method = self.jshandle.get('indexing_method', 'mosflm')
        peak_search = self.jshandle.get('peak_search', 'peakfinder8')
        int_method = self.jshandle.get('int_method', 'rings-cen-rescut')
        int_radius = self.jshandle.get('int_radius', '3,4,6')
        highres = self.jshandle.get('highres', '0.0')
        nproc = self.jshandle.get('num_processors', '20')

        if self.is_executable('indexamajig'):
            command = 'indexamajig -i %s -o %s -g %s' \
                      % (infile, streamfile, geometryfile)
            command += ' --indexing=%s --multi --no-cell-combinations --peaks=%s' \
                       % (indexing_method, peak_search)
            command += ' --integration=%s --int-radius=%s -j %s --no-check-peaks --highres=%s' \
                       % (int_method, int_radius, nproc, highres)

            if unitcell is not None and os.path.isfile(unitcell):
                command += ' -p %s --tolerance=%s' % (unitcell, '10,10,10,1.5')

            if peak_search == 'cxi' or peak_search == 'hdf5':
                peak_info = self.jshandle.get('peak_info', '/data/peakinfo')
                command += ' --hdf5-peaks=%s --no-revalidate' % peak_info

            else:
                peak_radius = self.jshandle.get('peak_radius', '3,4,5')
                local_bg_radius = self.jshandle.get('local_bg_radius', '10')
                min_peaks = self.jshandle.get('min_peaks', '30')
                min_snr = self.jshandle.get('min_snr', '4')
                min_res = self.jshandle.get('min_res', '50')
                threshold = self.jshandle.get('threshold', '10')

                command += ' --peak-radius=%s --min-peaks=%s' \
                           % (peak_radius, min_peaks)
                command += ' --min-snr=%s --threshold=%s --local-bg-radius=%s --min-res=%s' \
                           % (min_snr, threshold, local_bg_radius, min_res)
                command += ' --no-non-hits-in-stream'
        else:
            self.setFailure()
            logger.error('Error:{}'.format('indexamajig could not be found in PATH'))

        return command

    def scale_merge(self, streamfile):
        stat = dict()
        try:
            nproc = self.jshandle.get('num_processors', '20')
            final_stream = pathlib.Path(streamfile)
            base_str = str(final_stream.name)  # type: str
            base_str = base_str.split('.')  # type: list
            ohkl = str(final_stream.parent / (base_str[0] + '.hkl'))  # type: str
            ohkl1 = str(final_stream.parent / (base_str[0] + '.hkl1'))  # type: str
            ohkl2 = str(final_stream.parent / (base_str[0] + '.hkl2'))  # type: str
            snrfile = ohkl.split('.')[0] + '_snr.dat'
            ccfile = ohkl.split('.')[0] + '_CCstar.dat'
            rsplitfile = ohkl.split('.')[0] + '_Rsplit.dat'

            cmd = self.partialator_cmd(str(final_stream), self.results['point_group'], nproc)
            cmd += '\n\n'

            cmd += self.check_hkl_cmd(ohkl, self.results['point_group'], 'auto.cell', self.results['resolution_limit'])
            cmd += '\n\n'

            cmd += self.compare_hkl_cmd(ohkl1, ohkl2, 'auto.cell', self.results['resolution_limit'])
            cmd += '\n\n'

            cmd += self.compare_hkl_cmd(ohkl1, ohkl2, 'auto.cell', self.results['resolution_limit'], fom='Rsplit')
            cmd += '\n\n'
            shellfile = str(self.getOutputDirectory() / 'merge.sh')
            if self.is_executable('oarsub'):
                self.oarshell_submit(shellfile, cmd)
                self.check_oarstat(wait_count=6000)
            elif self.is_executable('sbatch'):
                self.slurm_submit(shellfile, cmd)
            else:
                self.run_as_command(cmd)

            if self.is_success():
                statparser = ResultParser()
                for statfile, fom in zip([snrfile, ccfile, rsplitfile], ['snr', 'ccstar', 'rsplit']):
                    statparser.getstats(statfile, fom=fom)
                    stat[fom] = statparser.results['DataQuality']
            else:
                logger.error('Merging did not run')

        except (IOError, KeyError) as err:
            self.setFailure()
            logger.error('Merging_Error:{}'.format(err))
        return stat

    def run_indexing(self):

        try:
            jsonschema.validate(instance=self.jshandle, schema=self.getInDataSchema())
            self.datafinder()
            self.makeOutputDirectory()
            kk = {}
            if self.jshandle['suffix'] == 'cxi':
                kk['cxi'] = """dim0 = %\ndim1 = ss\ndim2 = fs\ndata = /data/data\n"""
                geomfile = self.make_geometry_file(**kk)
            else:
                geomfile = self.make_geometry_file(**kk)

            self.make_list_events(str(geomfile))

            maxchunksize = self.jshandle.get('maxchunksize', 10)
            if len(self.filelist) <= maxchunksize:
                infile = str(self.getOutputDirectory() / 'input.lst')
                outname = datetime.now().strftime('%H-%M-%S.stream')
                outstream = str(self.getOutputDirectory() / outname)

                ofh = open(infile, 'w')
                for fname in self.filelist:
                    ofh.write(fname)
                    ofh.write('\n')
                ofh.close()

                self.run_as_command(self.indexamajig_cmd(infile, outstream, str(geomfile)))
            elif len(self.filelist) > maxchunksize:
                file_chunk = int(len(self.filelist) / maxchunksize) + 1
                for jj in range(file_chunk):
                    start = maxchunksize * jj
                    stop = maxchunksize * (jj + 1)
                    try:
                        images = self.filelist[start:stop]
                    except IndexError:
                        stop = start + (len(self.filelist) - stop)
                        images = self.filelist[start:stop]

                    infile = str(self.getOutputDirectory() / ('%d.lst' % jj))
                    outstream = str(self.getOutputDirectory() / ('%d.stream' % jj))
                    shellfile = str(self.getOutputDirectory() / ('%d.sh' % jj))

                    ofh = open(infile, 'w')
                    for fname in images:
                        ofh.write(fname)
                        ofh.write('\n')
                    ofh.close()

                    if self.is_executable('oarsub'):
                        self.oarshell_submit(shellfile, self.indexamajig_cmd(infile, outstream, str(geomfile)))
                    elif self.is_executable('sbatch'):
                        self.slurm_submit(shellfile, self.indexamajig_cmd(infile, outstream, str(geomfile)))
                    else:
                        self.run_as_command(self.indexamajig_cmd(infile, outstream, str(geomfile)))

        except Exception as err:
            self.setFailure()
            logger.error('Error:{}'.format(err))
        return

    def check_oarstat(self, wait_count=200):
        wait = 0
        njobs = sub.check_output('oarstat -u $USER | wc -l', shell=True)[:-1]
        wait_max = int(njobs) * wait_count
        while int(njobs) > 2:
            time.sleep(1)
            msg = "all jobs are not yet finished"
            logger.info('Indexing_running:{}'.format(msg))
            wait += 2
            njobs = sub.check_output('oarstat -u $USER | wc -l', shell=True)[:-1]
            njobs = int(njobs)
            if wait > wait_max:
                logger.error('Run_Error:{}'.format('OAR is taking too long to finish'))
                self.setFailure()
                break
            else:
                pass
        '''
        if self.is_success():
            cmd = 'cat *.stream >> alltogether.stream'
            self.run_as_command(cmd)
        else:
            pass
        '''
        return

    def report_cell(self, streampath):
        # cellobject = type('', (), {})  # c is a Cell type which is initialized as None type for python 2.7.
        results = dict()
        if os.path.exists(streampath):
            cellobject = Cell(streampath)
            cellobject.get_lattices()
            cellobject.calc_modal_cell()
            results['cellobject'] = cellobject
            try:
                results['centering'] = cellobject.most_common_centering
                lat, ua, cell_list = lattice_from_cell([cellobject.a_mode, cellobject.b_mode,
                                                        cellobject.c_mode, cellobject.al_mode,
                                                        cellobject.be_mode, cellobject.ga_mode])

                results['num_indexed_frames'] = cellobject.cell_array.shape[0]

                assert isinstance(lat, str)
                results['lattice'] = lat
                assert isinstance(ua, str)
                results['unique_axis'] = ua
                assert isinstance(cell_list, list)
                results['unit_cell'] = cell_list
                pg, sg_str, sg_num = assign_point_group(results['lattice'], results['centering'],
                                                        results['unique_axis'])
                assert isinstance(pg, str)
                results['point_group'] = pg
                results['space_group'] = sg_str
                results['space_group_number'] = sg_num

            except AssertionError as err:
                self.setFailure()
                logger.error("Cell_Error:{}".format(err))
        else:
            self.setFailure()
        return results

    def report_stats(self, streampath):
        stats = {}
        try:
            stats = self.report_cell(streampath)
            if not self.is_success():
                err = 'alltogether.stream file does not exist or empty'
                logger.error('Job_Error:'.format(err))
                return

            rescut = []
            npeaks = []

            for each_chunk in stats['cellobject'].stream_handle.stream_data:
                try:
                    rescut.append(each_chunk['rescut'])
                    npeaks.append(each_chunk['nPeaks'])
                except KeyError:
                    pass
            if len(rescut) > 0 and len(npeaks) > 0:
                stats['resolution_limit'] = Counter(rescut).most_common(1)[0][0]
                stats['average_num_spots'] = Counter(npeaks).most_common(1)[0][0]
            else:
                self.setFailure()
                err = "either nothing detected as hit or indexed in the stream file"
                logger.error('Job_Error:{}'.format(err))

            # Run partialator and calculate standard stats from crystfel..
            # self.scale_merge(streampath)

        except Exception as err:
            self.setFailure()
            logger.error('Job_Error:{}'.format(err))

        return stats

    def extract_peaklist(self, streampath):
        spots_data = {}
        try:
            sh = Stream(streampath)  # streampath is a string, not Path object
            sh.get_chunk_pointers()
            sh.read_chunks()
            sh.get_peaklist()
            sh.close()
            spots_data['peaks_per_pattern'] = sh.image_peaks
        except Exception as err:
            self.setFailure()
            logger.error('Stream_Error:{}'.format(err))
        return spots_data


def __run__(inData):
    crystTask = AutoCrystFEL(inData)
    results = {}
    try:
        crystTask.run_indexing()
        crystTask.writeInputData(inData)

        if crystTask.is_executable('oarsub'):
            crystTask.check_oarstat()

        elif crystTask.is_executable('sbatch'):
            crystTask.combine_streams()
        else:
            pass
        if crystTask.is_success():
            crystTask.run_as_command('cat *.stream >> alltogether.stream')
        else:
            pass
        streampath = crystTask.getOutputDirectory() / 'alltogether.stream'
        results['QualityMetrics'] = crystTask.report_stats(str(streampath))
        crystTask.write_cell_file(results['QualityMetrics'])

        if inData.get("doMerging", False):
            crystTask.set_outData(results['QualityMetrics'])
            merging_stats = crystTask.scale_merge(str(streampath))
            results['QualityMetrics'].update(merging_stats)

        if inData.get("GeneratePeaklist", False):
            results['PeaksDictionary'] = crystTask.extract_peaklist(str(streampath))
        if crystTask.is_success():
            crystTask.writeOutputData(results)
            logger.info('Indexing_Results:{}'.format(crystTask.results))
        else:
            crystTask.setFailure()
            logger.error("AutoCrystFEL_ERROR:{}".format("crystfel pipeline upstream error"))
    except Exception as err:
        crystTask.setFailure()
        logger.error("Error:{}".format(err))
    return results


def optparser():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_directory", type=str, required=True,
                        help="provide path MeshScan, containing images in cbf or h5 formats")
    parser.add_argument("--detectorType", type=str, required=True,
                        help="provide detector type, either pilatus or eiger")
    parser.add_argument("--prefix", type=str, required=True,
                        help="filename prefix, a wildcard to look for files")
    parser.add_argument("--suffix", type=str, required=True,
                        help="image fileformat, either cbf, h5, or cxi")
    parser.add_argument("--maxchunksize", type=int, required=True,
                        help="max number of images per batch")
    parser.add_argument("--num_processors", type=str, default='20')
    parser.add_argument("--beamline", type=str,
                        help="optional key, not needed")
    parser.add_argument("--processing_directory", type=str,
                        help="optional key, if you want to dump at a different folder")
    parser.add_argument("--doMerging", type=bool, default=False)
    parser.add_argument("--GeneratePeaklist", type=bool, default=False)
    parser.add_argument("--indexing_method", type=str, default="mosflm",
                        help="change to asdf,or dirax or xds if needed")
    parser.add_argument("--peak_search", type=str, default="peakfinder8",
                        help="alternatively, peakfinder9 can be tried")
    parser.add_argument("--peak_info", type=str, default="/data/peakinfo")
    parser.add_argument("--int_method", type=str, default='rings-grad-rescut')
    parser.add_argument("--int_radius", type=str, default='3,4,6')
    parser.add_argument("--min_peaks", type=str, default='30')
    parser.add_argument("--peak_radius", type=str, default='3,4,6')
    parser.add_argument("--min_snr", type=str, default='4.0')
    parser.add_argument("--threshold", type=str, default='10')
    parser.add_argument("--local_bg_radius", type=str, default='10')
    parser.add_argument("--min_res", type=str, default='70',
                        help="Applied to avoid regions near beamstop in peak search")
    parser.add_argument("--unit_cell_file", type=str,
                        help="optional key, if you want to index with a given unit-cell")
    parser.add_argument("--geometry_file", type=str,
                        help="optional key, only if you have a better detector geometry file")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='autoCryst.log',
                        filemode='a+')
    op = optparser()
    input_Dict = dict()
    for k, v in op.__dict__.items():
        if v is not None:
            input_Dict[k] = v
        else:
            pass
    output = __run__(input_Dict)
