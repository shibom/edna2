"""
Created on 18-Dec-2018
Author: S. Basu
"""

from __future__ import division, print_function
import os
import sys
import glob
import json
import logging
import subprocess as sub
import time
from collections import Counter
from datetime import datetime

from src.Image import ImageHandler as Im
from src.cell_analysis import Cell
from src.geom import Geom
from src.point_group import *
from src.stream import Stream

logger = logging.getLogger('autoCryst')


class Utils(object):

    def __init__(self, filedir, prefix, dataformat, **kwargs):
        self.status = False
        self.datadir = filedir  # Olof's 'directory' key from json
        self.results = {}
        self.prefix = prefix
        self.dataformat = dataformat
        # attributes declare and assigned later...
        self.crystfel_dir = None
        self.geometry_file = None
        self.detectorName = None
        self.infile = None
        self.outstream = None
        self.all_events = None
        self.cellobject = type('', (), {})
        self.filelist = []

        self.beamline = kwargs.get('beamline', None)
        self.outdir = kwargs.get('outdir', os.getcwd())
        self.indexing_method = kwargs.get('indexing_method', 'mosflm')
        self.peak_search = kwargs.get('peak_search', 'peakfinder8')
        self.peak_info = kwargs.get('peak_info', '/data/peakinfo')
        self.int_method = kwargs.get('int_method', 'rings-grad-rescut')
        self.peak_radius = kwargs.get('peak_radius', '3,4,6')  # '2,4,5'
        self.int_radius = kwargs.get('int_radius', '3,4,6')  # '2,4,5'
        self.min_peaks = kwargs.get('min_peaks', '30')  # grid of 15, 25, 30
        self.min_snr = kwargs.get('min_snr', '4.0')  # grid of 3, 4, 5
        self.threshold = kwargs.get('threshold', '10')  # grid of 5, 10, 20
        self.local_bg_radius = kwargs.get('local_bg_radius', '10')  # grid of 7, 10, 15, 20
        self.min_res = kwargs.get('min_res', '70')
        self.highres = kwargs.get('highres', '0.0')
        return

    def check_outdir(self):
        # for ESRF beamlines..

        if self.beamline is not None and os.path.isdir(self.datadir):
            list_path = self.datadir.split('/')
            if 'RAW_DATA' in list_path:
                idx = list_path.index('RAW_DATA')
                process_str = 'RAW_DATA'.replace('RAW', 'PROCESSED')
                list_path.insert(idx, process_str)
                list_path.remove('RAW_DATA')
                self.outdir = os.path.join('/', *list_path[1:])
                self.status = True
            else:
                err = "Check if you are on ESRF beamline data space"
                logger.info('Run_Error:{}'.format(err))
                self.status = False

        elif self.beamline is None and os.path.isdir(self.datadir):
            dirname = os.path.dirname(self.datadir)
            basename = os.path.basename(dirname)
            self.outdir = os.path.join(self.outdir, basename)
            self.status = True
        else:
            pass

        outname = datetime.now().strftime('autoCryst_%Y-%m-%d_%H-%M-%S')
        try:
            self.crystfel_dir = os.path.join(self.outdir, outname)
            # os.makedirs(self.crystfel_dir, 0o755)
            os.makedirs(self.crystfel_dir)
            self.status = True
        except Exception as err:
            logger.info('Output_dir_Error:{}'.format(err))
            self.status = False

        return

    def find_files(self):
        if os.path.isdir(self.datadir) and self.dataformat == 'cbf':
            search_str = self.prefix + '*.cbf'
            self.filelist = glob.glob(os.path.join(self.datadir, search_str))

            if len(self.filelist) > 0:
                self.status = True
                return

        elif os.path.isdir(self.datadir) and self.dataformat == 'hdf5':
            search_str = self.prefix + '*data*.h5'
            self.filelist = glob.glob(os.path.join(self.datadir, search_str))
            if len(self.filelist) > 0:
                self.status = True
                return
        elif os.path.isdir(self.datadir) and self.dataformat == 'cxi':
            search_str = self.prefix + '.cxi'
            self.filelist = glob.glob(os.path.join(self.datadir, search_str))
            if len(self.filelist) > 0:
                self.status = True
                return
        else:
            err = "No Mesh files found, check file directory"
            logger.info('Run_Error:{}'.format(err))
            self.status = False
            return

    def make_geomfile(self, **kwargs):
        # geom_args = ['coffset', 'fs0', 'ss0']
        try:
            image1 = type('', (), {})  # initialize image1 as an empty object
            if self.dataformat == 'cbf':
                image1 = Im(self.filelist[0])
            elif self.dataformat == 'hdf5':
                master_str = self.prefix + '*master.h5'
                image1 = Im(glob.glob(os.path.join(self.datadir, master_str))[0])
            elif self.dataformat == 'cxi':
                image1 = Im(self.filelist[0])
            else:
                logger.info('data_find_error:{}'.format('cbf or hdf5 are only supported'))
                pass

            g = Geom(image1.imobject.headers['detector_name'][0], image1.imobject.headers['detector_name'][1])
            g.write_geomfile(image1.imobject.headers, **kwargs)
            self.geometry_file = os.path.join(os.getcwd(), g.geomfilename)
            self.detectorName = g.detectorName
            if self.dataformat == 'hdf5' or self.dataformat == 'cxi':
                datalst = os.path.join(self.crystfel_dir, 'input.lst')
                fh = open(datalst, 'w')
                for fname in self.filelist:
                    fh.write(fname)
                    fh.write('\n')
                fh.close()
                if os.path.exists(self.geometry_file):
                    self.filelist = []
                    self.all_events = os.path.join(os.getcwd(), 'all_events.lst')
                    cmd = 'list_events -i %s -g %s -o %s' % (datalst, self.geometry_file, self.all_events)
                    sub.call(cmd, shell=True)
                    f = open(self.all_events, 'r')
                    for line in f:
                        line = line.strip('\n')
                        self.filelist.append(line)
                    f.close()
                else:
                    self.status = False
                    logger.info('Error:No Geom file exists')
            else:
                self.status = True  # cbf files are not multi-events
                pass
        except Exception as err:
            logger.info('Run_Error:{}'.format(err))
            self.status = False
        return

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
    def run_script(command):
        ofh = open('run.sh', 'w')
        ofh.write('#!/bin/bash \n\n')
        ofh.write(command)
        ofh.close()

        sub.call('chmod +x run.sh', shell=True)
        sub.call('./run.sh')
        return

    def indexamajig_cmd(self):
        if self.peak_search == 'cxi' or self.peak_search == 'hdf5':
            command = '/opt/pxsoft/bin/indexamajig -i %s -o %s -g %s' \
                      % (self.infile, self.outstream, self.geometry_file)
            command += ' --indexing=%s --multi --no-cell-combinations --peaks=%s --hdf5-peaks=%s' \
                       % (self.indexing_method, self.peak_search, self.peak_info)
            command += ' --integration=%s --int-radius=%s -j 20 --no-check-peaks --highres=%s --no-revalidate' \
                       % (self.int_method, self.int_radius, self.highres)
        else:
            command = '/opt/pxsoft/bin/indexamajig -i %s -o %s -g %s' \
                      % (self.infile, self.outstream, self.geometry_file)
            command += ' --indexing=%s --multi --no-cell-combinations --peaks=%s --peak-radius=%s --min-peaks=%s' \
                       % (self.indexing_method, self.peak_search, self.peak_radius, self.min_peaks)
            command += ' --min-snr=%s --threshold=%s --local-bg-radius=%s --min-res=%s' \
                       % (self.min_snr, self.threshold, self.local_bg_radius, self.min_res)
            command += ' --integration=%s --int-radius=%s -j 20 --no-check-peaks' \
                       % (self.int_method, self.int_radius)
            command += ' --no-non-hits-in-stream'

        return command

    @staticmethod
    def partialator_cmd(stream_name, point_group):
        base_str = stream_name.split('.')
        outhkl = base_str[0] + '.hkl'
        command = 'partialator -i %s -o %s -y %s ' \
                  % (stream_name, outhkl, point_group)
        command += ' --model=xsphere --push-res=1.5 --iterations=1 -j 24 --no-deltacchalf --no-logs'

        return command

    @staticmethod
    def check_hkl_cmd(hklfile, point_group, cellfile, rescut):
        statfile = hklfile.split('.')[0] + '_stat.dat'
        command = 'check_hkl -y %s -p %s --nshells=20 --shell-file=%s ' \
                  % (point_group, cellfile, statfile)
        command += '--lowres=20 --highres=%f %s' % (rescut, hklfile)

        return command

    @staticmethod
    def compare_hkl_cmd(hkl1, hkl2, cellfile, rescut, fom='CCstar'):
        base_str = hkl1.split('.')[0]
        statout = fom + '_' + base_str + '.dat'

        command = 'compare_hkl -p %s --nshells=20 --shell-file=%s ' % (cellfile, statout)
        command += '--fom=%s --lowres=20 --highres=%s ' % (fom, rescut)
        command += '%s %s' % (hkl1, hkl2)
        return command

    @staticmethod
    def oar_submit(crystfel_cmd):
        try:
            from oarpy.oarjob import submit
            job = submit(command=crystfel_cmd, name='autoCryst', core=20, walltime={'hours': 2})
            logger.info('MSG:{}'.format(job))
            # job.wait()
            if job.exit_code:
                logger.info('Failed:\n{}'.format(job.stderr))
            elif job.exit_code is None:
                logger.info('Interrupted:\n{}'.format(job.stdout))
            else:
                logger.info('Succes:\n{}'.format(job.stdout))

            job.remove_logs()
        except ImportError:
            submit = "submit module"
            logger.info('MSG:{}'.format('OAR %s not found, running locally' % submit))
            Utils.run_script(crystfel_cmd)
        return

    @staticmethod
    def oarshell_submit(shellfile, crystfel_cmd):
        oar_handle = open(shellfile, 'w')

        # dst = "/users/opid23/perl5/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games:\
        # /opt/demeter/bin:/usr/local/gd1/Scripts:/usr/local/gd1/Linux-x86_64:\
        # /sware/exp/gnxas/debian9:/opt/oar/utilities:/opt/pxsoft/bin"

        oar_handle.write("#!/bin/bash \n\n")

        oar_handle.write("#OAR -q mx \n")
        oar_handle.write("#OAR -n autoCryst \n")
        oar_handle.write("#OAR -l nodes=1, walltime=01:00:00 \n\n")
        oar_handle.write(crystfel_cmd)
        oar_handle.close()
        sub.call('chmod +x %s' % shellfile, shell=True)

        sub.call('oarsub -S ./%s' % shellfile, shell=True)
        return

    def scale_merge(self):
        try:
            final_stream = os.path.join(self.crystfel_dir, 'alltogether.stream')
            base_str = os.path.basename(final_stream)  # type: str
            base_str = base_str.split('.')  # type: list
            ohkl = base_str[0] + '.hkl'  # type: str
            ohkl1 = base_str[0] + '.hkl1'  # type: str
            ohkl2 = base_str[0] + '.hkl2'  # type: str
            cmd = Utils.partialator_cmd(final_stream, self.results['point_group'])
            cmd += '\n\n'

            cmd += Utils.check_hkl_cmd(ohkl, self.results['point_group'], 'auto.cell', self.results['resolution_limit'])
            cmd += '\n\n'

            cmd += Utils.compare_hkl_cmd(ohkl1, ohkl2, 'auto.cell', self.results['resolution_limit'])
            cmd += '\n\n'

            cmd += Utils.compare_hkl_cmd(ohkl1, ohkl2, 'auto.cell', self.results['resolution_limit'], fom='Rsplit')
            cmd += '\n\n'

            Utils.oarshell_submit('merge.sh', cmd)

        except (IOError, KeyError) as err:
            logger.info('Merging_Error:{}'.format(err))
            self.status = False
        return

    def run_indexing(self):

        try:
            self.check_outdir()
            os.chdir(self.crystfel_dir)
            self.find_files()
            kk = {}
            if self.dataformat == 'cxi':
                kk['cxi'] = """dim0 = %\ndim1 = ss\ndim2 = fs\ndata = /data/data\n"""
                self.make_geomfile(**kk)
            else:
                self.make_geomfile(**kk)
            self.status = True
        except (IOError, OSError) as err:
            self.status = False
            logger.info('Run_Error:{}'.format(err))
            return
        if len(self.filelist) < 50 and os.path.isfile(self.geometry_file):
            self.infile = os.path.join(os.getcwd(), 'input.lst')
            outname = datetime.now().strftime('%H-%M-%S.stream')
            self.outstream = os.path.join(os.getcwd(), outname)
            shellfile = 'input.sh'

            ofh = open(self.infile, 'w')
            for fname in self.filelist:
                ofh.write(fname)
                ofh.write('\n')
            ofh.close()

            if 'RAW_DATA' in self.datadir:
                Utils.oarshell_submit(shellfile, self.indexamajig_cmd())
            else:
                Utils.run_script(self.indexamajig_cmd())

        elif len(self.filelist) > 50 and os.path.isfile(self.geometry_file):
            file_chunk = int(len(self.filelist)/50) + 1
            for jj in range(file_chunk):
                start = 50*jj
                stop = 50*(jj+1)
                try:
                    images = self.filelist[start:stop]
                except IndexError:
                    stop = start + (len(self.filelist) - stop)
                    images = self.filelist[start:stop]

                self.infile = os.path.join(os.getcwd(), ('%d.lst' % jj))
                self.outstream = os.path.join(os.getcwd(), ('%d.stream' % jj))
                shellfile = '%d.sh' % jj
                ofh = open(self.infile, 'w')
                for fname in images:
                    ofh.write(fname)
                    ofh.write('\n')
                ofh.close()
                # self.oar_submit(self.indexamajig_cmd())
                if Utils.is_executable('oarsub'):
                    Utils.oarshell_submit(shellfile, self.indexamajig_cmd())
                else:
                    Utils.run_script(self.indexamajig_cmd())

            self.status = True
        else:
            err = "indexing job submission failed, check for filelist, paths, geometry_file"
            logger.info('Run_Error:{}'.format(err))
            self.status = False

        return

    def check_oarstat(self):
        wait = 0
        njobs = sub.check_output('oarstat -u $USER | wc -l', shell=True)[:-1]
        wait_max = int(njobs)*200
        while int(njobs) > 2:
            time.sleep(20)
            msg = "all jobs are not yet finished"
            logger.info('Indexing_running:{}'.format(msg))
            wait += 10
            njobs = sub.check_output('oarstat -u $USER | wc -l', shell=True)[:-1]
            njobs = int(njobs)
            if wait > wait_max:
                logger.info('Run_Error:{}'.format('OAR is taking too long to finish'))
                self.status = False
                break
            else:
                self.status = True

        if self.status is True:
            cmd = 'cat *.stream >> alltogether.stream'
            sub.call(cmd, shell=True)
        else:
            pass
        return

    def write_cell_file(self):
        try:
            cwrite = open('auto.cell', 'w')
            cwrite.write('CrystFEL unit cell file version 1.0\n\n')
            cwrite.write('lattice_type = %s\n' % self.results['lattice'])
            cwrite.write('centering = %s\n' % self.results['centering'])
            cwrite.write('unique_axis = %s\n' % self.results['unique_axis'])
            cwrite.write('a = %s A\n' % self.results['unit_cell'][0])
            cwrite.write('b = %s A\n' % self.results['unit_cell'][1])
            cwrite.write('c = %s A\n' % self.results['unit_cell'][2])
            cwrite.write('al = %s deg\n' % self.results['unit_cell'][3])
            cwrite.write('be = %s deg\n' % self.results['unit_cell'][4])
            cwrite.write('ga = %s deg\n' % self.results['unit_cell'][5])
            cwrite.close()
            self.status = True
        except (OSError, KeyError) as err:
            logger.info('Cell_file_Error:{}'.format(err))
            self.status = False
        return

    def report_cell(self):
        # c = type('', (), {})  # c is a Cell type which is initialized as None type for python 2.7.
        if os.path.exists(os.path.join(self.crystfel_dir, 'alltogether.stream')):
            self.cellobject = Cell(os.path.join(self.crystfel_dir, 'alltogether.stream'))
            self.cellobject.get_lattices()
            self.cellobject.calc_modal_cell()
            # self.results['unit_cell'] = [c.a_mode, c.b_mode, c.c_mode, c.al_mode, c.be_mode, c.ga_mode]
            # self.results['lattice_from_stream'] = self.cellobject.most_common_lattice_type
            self.results['centering'] = self.cellobject.most_common_centering
            # self.results['unique_axis_from_stream'] = self.cellobject.most_common_unique_axis
            lat, ua, cell_list = lattice_from_cell([self.cellobject.a_mode, self.cellobject.b_mode,
                                                    self.cellobject.c_mode, self.cellobject.al_mode,
                                                    self.cellobject.be_mode, self.cellobject.ga_mode])
            try:
                self.results['num_indexed_frames'] = self.cellobject.cell_array.shape[0]
                self.status = True
            except (IndexError, ValueError) as err:
                logger.info('Cell_Error:{}'.format(err))
                self.status = False
            try:
                assert isinstance(lat, str)
                self.results['lattice'] = lat
                assert isinstance(ua, str)
                self.results['unique_axis'] = ua
                assert isinstance(cell_list, list)
                self.results['unit_cell'] = cell_list
                pg, sg_str = assign_point_group(self.results['lattice'], self.results['centering'],
                                                self.results['unique_axis'])
                assert isinstance(pg, str)
                self.results['point_group'] = pg
                self.results['space_group'] = sg_str
                self.status = True
            except AssertionError as err:
                logger.info("Cell_Error:{}".format(err))
                self.status = False
        else:
            self.status = False
        return

    def report_stats(self):
        try:
            self.report_cell()
            self.write_cell_file()
            if not isinstance(self.cellobject, Cell) or self.status is False:
                err = 'altogether.stream file does not exist or empty'
                logger.info('Job_Error:'.format(err))
                return

            rescut = []
            npeaks = []

            for each_chunk in self.cellobject.stream_handle.stream_data:
                try:
                    rescut.append(each_chunk['rescut'])
                    npeaks.append(each_chunk['nPeaks'])
                except KeyError:
                    # logger.info('Stream_Error:{}'.format(err))
                    pass
            if len(rescut) > 0 and len(npeaks) > 0:
                self.status = True
                self.results['resolution_limit'] = Counter(rescut).most_common(1)[0][0]
                self.results['average_num_spots'] = Counter(npeaks).most_common(1)[0][0]
            else:
                self.status = False
                err = "either nothing detected as hit or indexed in the stream file"
                logger.info('Job_Error:{}'.format(err))

            # Run partialator and calculate standard stats from crystfel..
            # self.scale_merge()

        except Exception as err:
            self.status = False
            logger.info('Job_Error:{}'.format(err))

        logger.info('Indexing_Result:{}'.format(self.results))

        return

    def extract_peaklist(self):
        try:
            sh = Stream(os.path.join(self.crystfel_dir, 'alltogether.stream'))
            sh.get_chunk_pointers()
            sh.read_chunks()
            sh.get_peaklist()
            sh.close()
            self.results['peaks_per_pattern'] = sh.image_peaks
            self.status = True
        except Exception as err:
            logger.info('Stream_Error:{}'.format(err))
            self.status = False
        return


def __run__(directory_name, prefix, dataformat, **kwargs):
    cryst = Utils(directory_name, prefix, dataformat, **kwargs)
    cryst.run_indexing()
    cryst.check_oarstat()
    cryst.report_stats()
    # cryst.extract_peaklist()
    if cryst.status is True:
        with open('crystfel_output.json', 'w') as fh:
            json.dump(cryst.results, fh, sort_keys=True, indent=2)
    else:
        msg = "Nothing got indexed by crystfel or someother errors upstream"
        logger.info('Final_MSG:{}'.format(msg))
    return cryst.status, cryst.results


def optparser():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--meshdir", type=str,
                        help="provide path MeshScan, containing images in cbf or h5 formats")
    parser.add_argument("--prefix", type=str,
                        help="filename prefix, a wildcard to look for files")
    parser.add_argument("--format", type=str,
                        help="image fileformat, either cbf or hdf5")
    parser.add_argument("--beamline", type=str,
                        help="optional key, specify only if you the data is collected at ESRF to use OARsub "
                             "and folder structure")
    parser.add_argument("--outdir", type=str, default='current working directory',
                        help="optional key, if you want to dump at a different folder")
    parser.add_argument("--indexing", type=str, default="mosflm",
                        help="change to asdf,or dirax or xds if needed")
    parser.add_argument("--peaks", type=str, default="peakfinder8",
                        help="alternatively, peakfinder9 can be tried")
    parser.add_argument("--integration", type=str, default='rings-grad-rescut')
    parser.add_argument("--int_radius", type=str, default='3,4,6')
    parser.add_argument("--min_peaks", type=str, default='30')
    parser.add_argument("--peak_radius", type=str, default='3,4,6')
    parser.add_argument("--min_snr", type=str, default='4.0')
    parser.add_argument("--threshold", type=str, default='10')
    parser.add_argument("--local_bg_radius", type=str, default='10')
    parser.add_argument("--min-res", type=str, default='50',
                        help="Applied to avoid regions near beamstop in peak search")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='autoCryst.log',
                        filemode='a+')
    op = optparser()

    if op.meshdir is None:
        sys.exit("Need at least one directory path containing mesh scans")
    if op.prefix is None:
        sys.exit("Need filename prefix for searching")
    if op.format is None:
        sys.exit("Need fileformat, either cbf or hdf5")

    keywords = {}

    if op.beamline is not None:
        keywords['beamline'] = op.beamline
    if op.outdir is not None:
        keywords['outdir'] = op.outdir
    if op.indexing is not None:
        keywords['indexing_method'] = op.indexing
    if op.peaks is not None:
        keywords['peak_search'] = op.peaks
    if op.integration is not None:
        keywords['int_method'] = op.integration
    if op.peak_radius is not None:
        keywords['peak_radius'] = op.peak_radius
    if op.int_radius is not None:
        keywords['int_radius'] = op.int_radius
    if op.min_peaks is not None:
        keywords['min_peaks'] = op.min_peaks
    if op.min_snr is not None:
        keywords['min_snr'] = op.min_snr
    if op.threshold is not None:
        keywords['threshold'] = op.threshold
    if op.local_bg_radius is not None:
        keywords['local_bg_radius'] = op.local_bg_radius
    if op.min_res is not None:
        keywords['min_res'] = op.min_res
    else:
        pass

    __run__(op.meshdir, op.prefix, op.format, **keywords)
