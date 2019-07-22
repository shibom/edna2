from __future__ import division, print_function
import json
import jsonschema
import subprocess as sub
import pathlib
import sys
import os
import multiprocessing as mp


__author__ = ['S. Basu']
__license__ = 'MIT'
__date__ = '2019/07/03'


class ExeCrystFEL(object):
    def __init__(self, jsonfile=None, jstr=None):
        self.success = False
        self.filelist = []
        self.all_jobs = []
        self.datadir = None
        self.outdir = None
        self.geomfile = None
        self.cellfile = None
        self.suffix = '*cbf'
        self.prefix = None

        if os.path.exists(jsonfile) and jstr is None:
            fh = open(jsonfile, 'r')
            self.jshandle = json.load(fh)
            fh.close()
            self.success = True
        elif jstr is not None and jsonfile is None:
            self.jshandle = json.loads(jstr, default=str)
            self.success = True
        else:
            error = "input json file does not exist, Quit!"
            print('Error:{}'.format(error))
            self.success = False
            sys.exit()

        return

    @staticmethod
    def getInDataSchema():
        return {
            "type": "object",
            "required": ["image_folder", "proc_folder", "geometry_file", "unit_cell_file"],
            "properties": {
                "image_folder": {"type": "string"},
                "proc_folder": {"type": "string"},
                "geometry_file": {"type": "string"},
                "unit_cell_file": {"type": "string"},
                "suffix": {"type": "string"},
                "prefix": {"type": "string"}
            },
        }

    def get_paths(self):
        try:
            jsonschema.validate(instance=self.jshandle, schema=self.getInDataSchema())
            self.datadir = pathlib.Path(self.jshandle['image_folder'])
            self.outdir = pathlib.Path(self.jshandle['proc_folder'])
            self.geomfile = pathlib.Path(self.jshandle['geometry_file'])
            self.cellfile = pathlib.Path(self.jshandle['unit_cell_file'])
            self.suffix = self.jshandle['data_suffix']
            self.prefix = self.jshandle.get('data_prefix', self.datadir.name)
            self.success = True
        except Exception as err:
            print('patherror:{}'.format(err))
            self.success = False
        return

    def make_outdir(self):
        if self.datadir.exists():
            parents = self.datadir.parents
            dir1 = self.datadir.name
            dir2 = parents[0].name
            if self.outdir is None:
                self.outdir = pathlib.Path.cwd()
            elif self.outdir.exists() and self.prefix != self.datadir.name:
                self.outdir = self.outdir / dir1 / self.prefix
            elif self.outdir.exists() and self.prefix == self.datadir.name:
                self.outdir = self.outdir / dir2 / dir1
                print('Output directory path did work\n')
            self.outdir.mkdir(parents=True, exist_ok=True)
            self.success = True
        else:
            print('Error:{}'.format('Data directory path does not exist'))
        return

    def find_data(self):
        if self.datadir.exists() and self.prefix != self.datadir.name:
            for fname in list(self.datadir.glob((self.prefix + self.suffix))):
                self.filelist.append(fname.as_posix())
                self.success = True
        elif self.datadir.exists() and self.prefix == self.datadir.name:
            for fname in list(self.datadir.glob(self.suffix)):
                self.filelist.append(fname.as_posix())
                self.success = True
        else:
            print("No data found!!")
            self.success = False
        if self.geomfile.exists():
            self.geomfile = self.geomfile.as_posix()
            self.success = True
        else:
            print("Geometry file not provided")
            self.success = False
        if self.cellfile.exists():
            self.cellfile = self.cellfile.as_posix()
            self.success = True
        else:
            print("Unit cell file not found")
            self.cellfile = None
        return

    @staticmethod
    def indexing_cmd(infile, streamfile, geomfile, cellfile):
        command = '/mx-beta/crystfel/crystfel-0.8.0/bin/indexamajig -i %s -o %s -g %s' \
                  % (infile, streamfile, geomfile)
        command += ' --indexing=%s --multi -p %s --peaks=%s --peak-radius=%s --min-peaks=%s' \
                   % ('xgandalf', cellfile, 'peakfinder8', '3,4,6', '10')
        command += ' --min-snr=%s --threshold=%s --local-bg-radius=%s --min-res=%s' \
                   % ('4', '10', '10', '50')
        command += ' --integration=%s --int-radius=%s -j 10 --no-check-peaks' \
                   % ('rings-nocen-rescut', '3,4,6')
        command += ' --no-non-hits-in-stream'

        return command

    @staticmethod
    def run_script(command, fname):
        ofh = open(fname, 'w')
        ofh.write('#!/bin/bash \n\n')
        ofh.write(command)
        ofh.close()

        sub.call('chmod +x %s' % fname, shell=True)
        sub.call('./%s' % fname, shell=True)
        return

    def run_indexing(self):
        try:
            self.get_paths()
            self.find_data()
            self.make_outdir()
        except Exception as err2:
            print('Error:{}'.format(err2))
            self.success = False
        if self.success:
            os.chdir(self.outdir.as_posix())
            if len(self.filelist) > 1000:
                nchunk = int(len(self.filelist) / 1000) + 1
                for jj in range(nchunk):
                    start = 1000 * jj
                    stop = 1000 * (jj + 1)
                    try:
                        images = self.filelist[start:stop]
                    except IndexError:
                        stop = start + (len(self.filelist) - stop)
                        images = self.filelist[start:stop]

                    infile = os.path.join(os.getcwd(), ('%d.lst' % jj))
                    outstream = os.path.join(os.getcwd(), ('%d.stream' % jj))
                    shellfile = '%d.sh' % jj
                    ofh = open(infile, 'w')
                    for fname in images:
                        ofh.write(fname)
                        ofh.write('\n')
                    ofh.close()
                    cmd = ExeCrystFEL.indexing_cmd(infile, outstream, self.geomfile, self.cellfile)
                    self.all_jobs.append(mp.Process(target=ExeCrystFEL.run_script, args=(cmd, shellfile)))
            else:
                infile = os.path.join(os.getcwd(), 'input.lst')
                outstream = os.path.join(os.getcwd(), 'input.stream')
                ofh = open(infile, 'w')
                for fname in self.filelist:
                    ofh.write(fname)
                    ofh.write('\n')
                ofh.close()
                cmd = ExeCrystFEL.indexing_cmd(infile, outstream, self.geomfile, self.cellfile)
                sub.call(cmd)
                self.success = True
        else:
            print("something wrong upstream, not running indexing")
            self.success = False
        return

    def run_as_mpi(self):
        self.run_indexing()
        if self.success is True and len(self.all_jobs) > 0:
            block_size = 6
            nblocks = (len(self.all_jobs) // block_size) + 1

            for i in range(nblocks):
                start = i * block_size
                stop = start + block_size
                if stop <= len(self.all_jobs):
                    proc = self.all_jobs[start:stop]
                else:
                    stop = start + (len(self.all_jobs) - start)
                    proc = self.all_jobs[start:stop]
                    break
                for p in proc:
                    p.start()
                for p in proc:
                    p.join()
                print("%d crystfel batch jobs attempted" % i)
        else:
            pass
        return


if __name__ == '__main__':

    cryst = ExeCrystFEL(sys.argv[1])
    cryst.run_as_mpi()
