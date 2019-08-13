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
__date__ = '2018/12/10'


from io import open
import logging
import numpy as np
import os
import json
import fabio


logger = logging.getLogger('autoCryst')


class CBFreader(object):
    def __init__(self, filename):

        """
        rtype: type(headers) -> dict
        rtype: type(data) -> numpy array 2D
        """
        if not os.path.exists(filename):
            err = 'File does not exist %s.' % filename
            logger.info('IOError:{}'.format(err))
            return
        self.cbf_file = filename
        self.headers = {}
        self.data = np.empty([])
        return

    def read_cbfheaders(self):
        self.headers['filename'] = self.cbf_file
        self.headers['dimension'] = []
        fh = open(self.cbf_file, 'rb')
        for record in fh:
            if b'X-Binary-Size-Padding' in record:
                break
            if b'Pixel_size' in record:
                self.headers['pixel_size'] = float(record.decode().split()[2])
            if b'Detector_distance' in record:
                self.headers['detector_distance'] = float(record.decode().split()[2])
            if b'Wavelength' in record:
                self.headers['photon_energy'] = 12398 / float(record.decode().split()[2])
            if b'Beam_xy' in record:
                beam = map(float, record.decode().replace('(', '').replace(')', '').replace(',', '').split()[2:4])
                beam = list(beam)
                self.headers['beam_center_x'] = beam[0]
                self.headers['beam_center_y'] = beam[1]
            if b'Detector:' in record:
                self.headers['detector_name'] = record.decode().replace(',', '').split()[2:4]
            if b'Exposure_time' in record:
                self.headers['exposure'] = float(record.decode().split()[2])
            if b'Start_angle' in record:
                self.headers['starting_angle'] = float(record.decode().split()[2])
            if b'Angle_increment' in record:
                self.headers['oscillation_range'] = float(record.decode().split()[2])
            if b'X-Binary-Size-Fastest-Dimension' in record:
                self.headers['dimension'].append(int(record.decode().split()[1]))
            if b'X-Binary-Size-Second-Dimension' in record:
                self.headers['dimension'].append(int(record.decode().split()[1]))
            else:
                pass
        fh.close()
        return

    def read_cbfdata(self):
        handler = fabio.open(self.cbf_file)
        self.data = handler.data.flatten()
        return

    '''
    # pycbf is not supported for python 3. So, switching to fabio module.
    def read_cbfdata(self):
        handler = pycbf.cbf_handle_struct()
        handler.read_file(self.cbf_file, pycbf.MSG_DIGEST)
        handler.rewind_datablock()
        handler.select_datablock(0)
        handler.select_category(0)
        handler.select_column(1)
        handler.select_row(0)
        type = handler.get_typeofvalue()
        if type.find('bnry') > -1:
            img_as_string = handler.get_integerarray_as_string()
            self.data = np.fromstring(img_as_string, np.int32)  # look for image.py in dials/util
            # self.dimension = (handler.get_integerarrayparameters_wdims()[10], 
            handler.get_integerarrayparameters_wdims()[9])
            # self.data = self.data.reshape(self.dimension)
            # from scitbx.array_family import flex
            # self.data = flex.int(self.data)
            # self.data.reshape(flex.grid(*self.dimension))
        else:
            raise TypeError('cannot find image %s' % self.cbf_file)
        return
    '''

    @staticmethod
    def write_cbf():
        try:
            import pycbf
        except ImportError as err:
            logger.info('ImportError:{}'.format(err))
        "Method to write a cbf image file"
        return


class EigerReader(object):
    def __init__(self, filename):

        """
        :rtype: type(headers) -> dict
        :rtype: type(data) -> numpy array 2D
        """
        if not os.path.exists(filename):
            err = "File does not exist %s" % filename
            logger.info('IOError:{}'.format(err))
            return

        self.eiger_file = filename
        self.headers = {}
        self.data = np.empty([])
        try:
            import h5py
            self.eiger_handle = h5py.File(self.eiger_file, 'r')
        except (ImportError, NameError) as err:
            logger.info('ImportError:{}'.format(err))
        return

    def read_h5headers(self):
        if 'master' not in self.eiger_file:
            err = '%s is not a master file, no header info' % self.eiger_file
            logger.info('ValueError:{}'.format(err))
            return
        else:
            self.headers['filename'] = self.eiger_file
            pix_size = self.eiger_handle['/entry/instrument/detector/x_pixel_size']
            self.headers['pixel_size'] = np.array(pix_size)
            detector_name = self.eiger_handle['/entry/instrument/detector/description']
            detector_name = np.array(detector_name).tolist()  # type: bytes
            self.headers['detector_name'] = detector_name.decode().split()[1:3]
            detector_distance = self.eiger_handle['/entry/instrument/detector/detector_distance']
            self.headers['detector_distance'] = np.array(detector_distance)
            beamx = self.eiger_handle['/entry/instrument/detector/beam_center_x']
            self.headers['beam_center_x'] = np.array(beamx)
            beamy = self.eiger_handle['/entry/instrument/detector/beam_center_y']
            self.headers['beam_center_y'] = np.array(beamy)
            wave = self.eiger_handle['/entry/instrument/beam/incident_wavelength']
            self.headers['photon_energy'] = 12398 / np.array(wave)
            return

    def read_h5data(self):
        self.data = self.eiger_handle['/data/data']
        self.data = np.array(self.data, np.int32)
        return

    def write_h5(self):
        """ Method to write an Eiger h5 image """
        return


class ImageHandler(object):
    def __init__(self, filename):

        self.imagefile = filename
        self.imobject = type('', (), {})
        self.imobject.headers = {}
        if not os.path.exists(self.imagefile):
            err = 'File does not exist: %s' % filename
            logger.info('ImportError:{}'.format(err))
            return
        else:
            if '.cbf' in self.imagefile:
                self.imobject = CBFreader(self.imagefile)
                self.imobject.read_cbfheaders()
            elif 'master' in self.imagefile:
                self.imobject = EigerReader(self.imagefile)
                self.imobject.read_h5headers()
            elif '.cxi' in self.imagefile:
                dirname = os.path.dirname(self.imagefile)
                if os.path.isfile(os.path.join(dirname, 'headers.json')):
                    cxi = open(os.path.join(dirname, 'headers.json'), 'r')
                    self.imobject.headers = json.load(cxi)
                else:
                    err = 'cxi file exists but no header json file'
                    logger.info('DozorHit_Error:{}'.format(err))
            else:
                pass
        return

    def read_datablock(self):

        if isinstance(self.imobject, CBFreader):
            self.imobject.read_cbfdata()
        elif isinstance(self.imobject, EigerReader):
            self.imobject.read_h5data()
        else:
            pass
        return

    def check_icerings(self):

        """Method for ice rings analysis"""

        return

    def create_powdersum(self):
        """Method to write a powder pattern, useful for background checking"""

        return

    def create_maskfile(self):
        """Method for writing a mask file based on powder sum"""
        return

    def radial_avg(self):
        return


def dstack(array_lst):
    # data_stack = np.empty(array_lst.[0].shape[0],array_lst.[0].shape[1],len(array_lst))
    if array_lst:
        return np.dstack(array_lst)
    else:
        print("Empty list of arrays")
        return


def create_h5stack(list_of_cbfs):
    if len(list_of_cbfs) == 0:
        print("Need a list of many cbfs; got empty list")
        return
    else:
        image1 = CBFreader(list_of_cbfs[0])
        image1.read_cbfheaders()
        stacksize = (len(list_of_cbfs),) + tuple(image1.headers['dimension'])
        data_stack = np.empty(stacksize, dtype=np.int32)
        """
        :rtype: ii -> int
        """

        for ii in range(len(list_of_cbfs)):
            try:
                c = CBFreader(list_of_cbfs[ii])
                c.read_cbfdata()
                data_stack[ii, :, :] = c.data.reshape((image1.headers['dimension']))
                del c
            except Exception as e:
                raise e
    return data_stack


if __name__ == '__main__':
    '''
    import glob
    import h5py

    lst_cbfs = glob.glob('/data/id23eh2/inhouse/opid232/20181208/RAW_DATA/Sample-1-1-03/MeshScan_02/*.cbf')
    nframes = len(lst_cbfs)
    nchunks = int(nframes / 100) + 1
    for i in range(nchunks):
        start = 100 * i
        stop = 100 * (i + 1)
        try:
            data_stacks = create_h5stack(lst_cbfs[start:stop])
            prefix = 'data_stack_' + str(i) + '.h5'
            fh = h5py.File(prefix, 'w')
            fh.create_dataset('/data/data', data=data_stacks)
            fh.close()
            for j in range(start, stop):
                print(data_stacks[j, :, :].max())
        except IndexError:
            pass

    '''
    # img = CBFreader('/data/id23eh2/inhouse/opid232/20181208/RAW_DATA/
    # Sample-1-1-03/MeshScan_02/mesh-insu_3_0_0100.cbf')
    img = CBFreader('/Users/shbasu/work/autoCryst/examples/mesh-insu_2_0_1143.cbf')
    img.read_cbfheaders()
    print(img.headers)
    img.read_cbfdata()
    print(img.data.shape)

    h5 = EigerReader('/Users/shbasu/work/autoCryst/examples/mesh-x_2_1_master.h5')
    h5.read_h5headers()
    print(h5.headers['pixel_size'])
