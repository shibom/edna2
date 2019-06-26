"""
Created on 15-May-2019
Author: S. Basu
"""
from __future__ import division, print_function
import os
import sys
import subprocess as sub
import logging
import numpy as np
import glob
import h5py
import json
import base64
import src.dozor_input as di
from src.Image import CBFreader
import ext.fast_array_ext as af

logger = logging.getLogger('autoCryst')


class Dozor(object):
    stacks = dict()

    def __init__(self, jsonfile):
        if os.path.exists(jsonfile):
            fh = open(jsonfile, 'r')
            self.jshandle = json.load(fh)
            fh.close()
        else:
            error = "input json file does not exist, Quit!"
            logger.info('Error:{}'.format(error))
            self.success = False
            sys.exit()

        self.input_dict = dict()
        self.lst_of_files = []
        self.cbfheader = dict()
        self.dozor_results = []
        self.max_npeaks = 0
        self.stacklength = 0
        self.success = True
        return

    def prep_dozorinput(self):
        try:
            self.lst_of_files = sorted(glob.glob(os.path.join(self.jshandle['image_folder'], '*.cbf')))
        except KeyError as kerr:
            logger.info('Dozor-Error:{}'.format(kerr))
            self.success = False
        try:
            cbf = CBFreader(self.lst_of_files[0])
            cbf.read_cbfheaders()
            name = os.path.basename(cbf.cbf_file)
            name = name.strip('.cbf')[:-4]
            name = name + '????.cbf'
            name_template = os.path.join(self.jshandle['image_folder'], name)
        except (IndexError, ValueError, IOError) as ivio:
            logger.info('DozorHit_Error:{}'.format(ivio))
            self.success = False
            return

        if cbf.headers['detector_name'][0] == 'PILATUS3':
            det = 'pilatus'
        elif cbf.headers['detector_name'][0] == 'PILATUS':
            det = 'pilatus'
        else:
            det = 'eiger'

        det += cbf.headers['detector_name'][1].lower()
        self.input_dict['det'] = det
        self.input_dict['exposure'] = cbf.headers['exposure']
        self.input_dict['detector_distance'] = '%6.3f' % (cbf.headers['detector_distance'] * 1000)
        self.input_dict['wavelength'] = '%1.3f' % (12398 / cbf.headers['photon_energy'])
        self.input_dict['beamx'] = cbf.headers['beam_center_x']
        self.input_dict['beamy'] = cbf.headers['beam_center_y']
        self.input_dict['oscillation_range'] = cbf.headers['oscillation_range']
        self.input_dict['starting_angle'] = cbf.headers['starting_angle']
        self.input_dict['nframes'] = len(self.lst_of_files)
        self.input_dict['name_template'] = name_template

        return

    def run_dozor(self):
        self.prep_dozorinput()
        if self.success:
            if self.input_dict['det'] == 'pilatus2m':
                dozor_str = di.dozor_input['2m']
            elif self.input_dict['det'] == 'pilatus6m':
                dozor_str = di.dozor_input['6m']
            else:
                dozor_str = 'detector type not supported - only 2m and 6m pilatus'
            with open('dozor.dat', 'w') as dh:
                dh.write(dozor_str.format(**self.input_dict))
            cmd = 'dozor__v1.3.8 -p dozor.dat > /dev/null'
            sub.call(cmd, shell=True)
            self.success = True
        else:
            dozor_err = 'dozor could not be run'
            logger.info('DozorHit_Error:{}'.format(dozor_err))
            self.success = False
        return

    def prep_spot(self):
        if self.jshandle['dozorfolder'] is None:
            cwd = os.getcwd()
        else:
            cwd = self.jshandle['dozorfolder']
        spotfiles = glob.glob(os.path.join(cwd, '*.spot'))

        if len(spotfiles) > 0 and self.success is True:
            for fname in spotfiles:
                dozorDict = dict()
                basename = os.path.basename(fname)
                index = int(basename.strip('.spot'))
                imgName = glob.glob(os.path.join(self.jshandle['image_folder'], ('*_%04d.cbf' % index)))[0]
                if os.path.isfile(imgName):
                    dozorDict['image_name'] = imgName
                else:
                    logger.info('image name not found %s' % imgName)
                data_array, npeaks = Dozor.read_spotfile(fname)
                if npeaks > 5:
                    # dozorDict['DozorSpotList'] = spotList
                    dozorDict['nPeaks'] = npeaks
                    dozorDict['PeakXPosRaw'] = data_array[:, 1]
                    dozorDict['PeakYPosRaw'] = data_array[:, 2]
                    dozorDict['PeakTotalIntensity'] = data_array[:, 3]
                    self.dozor_results.append(dozorDict)
                    self.success = True
                    if dozorDict['nPeaks'] > self.max_npeaks:
                        self.max_npeaks = dozorDict['nPeaks']
                else:
                    pass
        else:
            logger.info("No spot files found")
            self.success = False
        if self.success:
            self.stacklength = len(self.dozor_results)
            cbf_unicode = self.dozor_results[0]['image_name']
            c = CBFreader(cbf_unicode)
            c.read_cbfheaders()
            c.headers['dimension'].reverse()  # transpose each image
            self.cbfheader = c.headers
        return

    @staticmethod
    def read_spotfile(fname):
        data = np.array([])
        npeaks = 0
        if os.path.isfile(fname):
            data = np.loadtxt(fname, skiprows=3)
            npeaks = data.shape[0]
        else:
            spot_err = "No spot file found"
            logger.info('DozorHit_Error:{}'.format(spot_err))
        return data, npeaks

    def write_json(self):
        if len(self.dozor_results) == 0:
            json_err = 'Nothing to dump, either dozor did not run or no spots found'
            logger.info('Error: {}'.format(json_err))
            return

        with open('dozorspots.json', 'w') as jsh:
            for image in self.dozor_results:
                for k in image.keys():
                    if isinstance(image[k], np.ndarray):
                        image[k] = image[k].tolist()
                json.dump(image, jsh, sort_keys=True, indent=2)

        return

    def extract_olof_json(self, olof_json):  # Olof's json file
        try:
            fh = open(olof_json, 'r')
            js = json.load(fh)
            fh.close()
            # self.success = True
        except (IOError, TypeError):
            logger.info('DozorHit_Error:{}'.format("Olof json file does not exist"))
            self.success = False
            return
        try:
            for image in js['meshPositions']:
                if len(image['dozorSpotListShape']) > 0 and image['dozorSpotListShape'][0] > 5:
                    dozorDict = dict()
                    imgPrefix = js['directory']
                    dozorDict['image_name'] = os.path.join(imgPrefix, image['imageName'])
                    dozorDict['nPeaks'] = image['dozorSpotListShape'][0]
                    spot_arr = np.fromstring(base64.b64decode(image['dozorSpotList']))
                    spot_arr = spot_arr.reshape((spot_arr.size // 5, 5))
                    dozorDict['PeakXPosRaw'] = spot_arr[:, 1]
                    dozorDict['PeakYPosRaw'] = spot_arr[:, 2]
                    dozorDict['PeakTotalIntensity'] = spot_arr[:, 3]
                    # dozorDict['DozorSpotList'] = spot_arr.tolist()
                    self.dozor_results.append(dozorDict)
                    if dozorDict['nPeaks'] > self.max_npeaks:
                        self.max_npeaks = dozorDict['nPeaks']
                else:
                    pass
                self.success = True
        except KeyError as e:
            logger.info('DozorHit_Error:{}'.format(e))
            self.success = False
        if self.success:
            self.stacklength = len(self.dozor_results)
            cbf_unicode = self.dozor_results[0]['image_name']
            c = CBFreader(cbf_unicode)
            c.read_cbfheaders()
            c.headers['dimension'].reverse()  # transpose each image
            self.cbfheader = c.headers
        return

    @staticmethod
    def get_dozor_peaks(dozor_lst_dict, max_peak_count, imagesize):
        chunk_size = len(dozor_lst_dict)
        assert type(imagesize) == tuple and len(imagesize) == 2
        size_3d = (chunk_size,) + imagesize
         
        Dozor.stacks['npeaks'] = np.empty(chunk_size)
        Dozor.stacks['xpos_arr'] = np.zeros((chunk_size, max_peak_count))
        Dozor.stacks['ypos_arr'] = np.zeros((chunk_size, max_peak_count))
        Dozor.stacks['peak_int_arr'] = np.zeros((chunk_size, max_peak_count))
        cbf_ar = np.empty(chunk_size, dtype='U256')

        for i in range(chunk_size):
            cbf_ar[i] = dozor_lst_dict[i]['image_name']
            Dozor.stacks['npeaks'][i] = dozor_lst_dict[i]['nPeaks']
            Dozor.stacks['xpos_arr'][i, 0:dozor_lst_dict[i]['nPeaks']] = dozor_lst_dict[i]['PeakXPosRaw']
            Dozor.stacks['ypos_arr'][i, 0:dozor_lst_dict[i]['nPeaks']] = dozor_lst_dict[i]['PeakYPosRaw']
            Dozor.stacks['peak_int_arr'][i, 0:dozor_lst_dict[i]['nPeaks']] = dozor_lst_dict[i]['PeakTotalIntensity']
        
        Dozor.stacks['data_stack_3d'] = af.stack3d(cbf_ar, imagesize[0], imagesize[1]) 
        Dozor.stacks['data_stack_3d'] = Dozor.stacks['data_stack_3d'].reshape(size_3d)
        return

    def create_stack(self):
        if len(self.dozor_results) == 0:
            msg = "dozor did not work or no hits"
            logger.info('DozorHits_MSG:{}'.format(msg))
            self.success = False
            return

        if self.stacklength < 100:
            Dozor.get_dozor_peaks(self.dozor_results, self.max_npeaks, tuple(self.cbfheader['dimension']))
            Dozor.save_h5(Dozor.stacks, 'dozor_0.cxi')
            self.success = True
        else:
            nchunk = int(self.stacklength / 100) + 1

            for i in range(nchunk):
                start = 100 * i
                stop = 100 * (i + 1)
                h5name = 'dozor_%d.cxi' % i
                try:
                    Dozor.get_dozor_peaks(self.dozor_results[start:stop], self.max_npeaks,
                                          tuple(self.cbfheader['dimension']))
                except IndexError:
                    stop = start + (self.stacklength - start)
                    Dozor.get_dozor_peaks(self.dozor_results[start:stop], self.max_npeaks,
                                          tuple(self.cbfheader['dimension']))
                Dozor.save_h5(Dozor.stacks, h5name)
            self.success = True

        return

    @staticmethod
    def create_write(lst_of_dict, maxpeaks, imagesize, h5name):
        Dozor.get_dozor_peaks(lst_of_dict, maxpeaks, imagesize)
        Dozor.save_h5(Dozor.stacks, h5name)
        return

    def mp_stack(self):
        import multiprocessing as mp
        nchunk = int(len(self.dozor_results) / 100) + 1
        njobs = 5
        for i in range((nchunk//njobs)+1):
            proc = []
            for j in range(njobs):
                start = 100*(njobs*i+j)
                stop = start + 100
                h5name = 'dozor_%d.cxi' % (njobs*i+j)
                if stop <= len(self.dozor_results):
                    job = mp.Process(target=Dozor.create_write, args=(self.dozor_results[start:stop], self.max_npeaks,
                                                                      tuple(self.cbfheader['dimension']), h5name))
                    proc.append(job)
                else:
                    stop = start + (len(self.dozor_results) - start)
                    job = mp.Process(target=Dozor.create_write, args=(self.dozor_results[start:stop], self.max_npeaks,
                                                                      tuple(self.cbfheader['dimension']), h5name))
                    proc.append(job)
                    break
            for p in proc:
                p.start()
            for p in proc:
                p.join()
        return

    @staticmethod
    def save_h5(dict_with_peakinfo, h5name):
        cxis_all = glob.glob('dozor*cxi')
        if h5name in cxis_all:
            cnt = len(cxis_all)
            h5name = 'dozor_%d.cxi' % cnt
        else:
            pass
        hf = h5py.File(h5name, 'w', libver='latest')
        try:
            hf.create_dataset('/data/data', data=dict_with_peakinfo['data_stack_3d'])
            hf.create_dataset('/data/peakinfo/nPeaks', data=dict_with_peakinfo['npeaks'])
            hf.create_dataset('/data/peakinfo/peakXPosRaw', data=dict_with_peakinfo['xpos_arr'])
            hf.create_dataset('/data/peakinfo/peakYPosRaw', data=dict_with_peakinfo['ypos_arr'])
            hf.create_dataset('/data/peakinfo/peakTotalIntensity', data=dict_with_peakinfo['peak_int_arr'])
        except (KeyError, ValueError) as kv_err:
            logger.info('DozorHit_Error:{}'.format(kv_err))
        hf.close()
        return


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='test.log',
                        filemode='a+')
    dd = Dozor(sys.argv[1])
    try:
        dd.extract_olof_json(dd.jshandle['olof_json'])
    except (KeyError, IOError) as err:
        print("Olof json file was not provided")
        if dd.jshandle['dozorfolder'] is None:
            dd.run_dozor()
        elif os.path.exists(dd.jshandle['dozorfolder']):
            dd.prep_spot()
    if dd.success:
        with open('headers.json', 'w') as jhead:
            json.dump(dd.cbfheader, jhead, sort_keys=True, indent=2)
        dd.mp_stack()
    else:
        pass
    # print(dd.dozor_results)
