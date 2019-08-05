"""
Created on 10-May-2019
Author: S. Basu
"""
from __future__ import division, print_function
import numpy as np
import os
import copy
import h5py
import ctypes
import multiprocessing as mp
from contextlib import closing
from edna2.lib.autocryst.src.Image import CBFreader


def prep_spot(imgPrefix, dozorfolder):
    spotfiles = glob.glob(os.path.join(dozorfolder, '*.spot'))
    # imgList = glob.glob(os.path.join(imgPrefix, '*.cbf'))
    dozor_results = []
    dozorDict = copy.deepcopy({})
    if len(spotfiles) > 0:
        for fname in spotfiles:
            try:
                basename = os.path.basename(fname)
                index = int(basename.strip('.spot'))
                imgName = glob.glob(os.path.join(imgPrefix, ('*_%04d.cbf' % index)))[0]
                if os.path.isfile(imgName):
                    dozorDict['image_name'] = imgName
                else:
                    print('image name not found %s' % imgName)
                data_array, spotList, npeaks = read_spotfile(fname)
                dozorDict['DozorSpotList'] = spotList
                dozorDict['nPeaks'] = npeaks
                dozorDict['PeakXPosRaw'] = data_array[:, 1]
                dozorDict['PeakYPosRaw'] = data_array[:, 2]
                dozorDict['PeakTotalIntensity'] = data_array[:, 3]
                dozor_results.append(dozorDict)
            except Exception as e:
                raise e
    else:
        print("No spot files found")
    return dozor_results


def read_spotfile(fname):
    data = np.loadtxt(fname, skiprows=3)
    spotList = []
    for i in range(data.shape[0]):
        spotList.append(data[i, :].tolist())
    npeaks = len(spotList)
    return data, spotList, npeaks


class Pack_hdf5(CBFreader):
    def __init__(self, list_of_cbfs):
        self.cbf_list = list_of_cbfs

        if len(self.cbf_list) > 0:
            self.nframes = len(self.cbf_list)
            # self.chunksize = 100
            self.cbf_file = self.cbf_list[0]
        else:
            print("No cbf files in the list, quits")
            return
        # super().__init__(self.cbf_file) # syntax for python 3.7 with super() method sans arguments
        super(Pack_hdf5, self).__init__(self.cbf_file)

        self.read_cbfheaders()
        self.read_cbfdata()
        self.stacksize = (self.nframes,) + self.data.shape  # type: tuple
        self.size2d = (self.nframes,) + self.data.flatten().shape
        self.data_stack_2d = np.empty(self.size2d, dtype=np.int32)
        self.data_stack_3d = np.empty(self.stacksize, dtype=np.int32)
        totLen = self.stacksize[0] * self.stacksize[1] * self.stacksize[2]
        self.shared_arr = mp.Array(ctypes.c_int32, totLen)

        return

    @staticmethod
    def tonumpyarray(mp_arr):
        return np.frombuffer(mp_arr.get_obj())

    # @staticmethod
    def init(self, shared_arr_):
        self.shared_arr = shared_arr_  # must be inherited, not passed as an argument

    def f(self, i):
        """synchronized."""
        with self.shared_arr.get_lock():  # synchronize access
            self.g(i)

    def g(self, i):
        """no synchronization."""
        self.data_stack_3d = Pack_hdf5.tonumpyarray(self.shared_arr)
        # self.data_stack_3d.reshape(self.stacksize)
        block = self.stacksize[1] * self.stacksize[2]
        self.cbf_file = self.cbf_list[i]
        self.read_cbfdata()
        self.data_stack_3d[(i*block):(i+1)*block] = self.data
        print(self.data.max())
        return

    def populate_shared(self):

        # write to arr from different processes
        with closing(mp.Pool(initializer=self.init, initargs=(self.shared_arr,))) as p:
            # many processes access the same slice
            start = 0
            stop = self.nframes
            step = stop // 5
            try:
                p.map_async(self.f, [slice(i, i + step) for i in range(start, stop, step)])
            except IndexError:
                pass
            # many processes access different slices of the same array
            # assert M % 2 # odd
            # step = N // 10
            p.map_async(self.g, [slice(i, i + step) for i in range(start, stop, step)])
        p.join()
        return

    def populate_stack(self, index):

        self.cbf_file = self.cbf_list[index]
        self.read_cbfdata()
        self.data_stack_3d[index, :, :] = self.data
        # self.data = np.zeros((self.stacksize[0], self.stacksize[1]))
        return

    def multiproc(self):
        try:
            for i in range(len(self.cbf_list)):
                proc = []
                for j in range(0, 10):
                    try:
                        jobid = mp.Process(target=self.populate_stack, args=((i * 10) + j,))
                        proc.append(jobid)
                    except IndexError:
                        pass
                for p in proc:
                    p.start()
                for p in proc:
                    p.join()
        except Exception:
            pass

        self.data_stack.reshape(self.stacksize, dtype=np.int32)
        return

    def H5write(self, h5filename):
        hf = h5py.File(h5filename, 'w')
        # entry = hf.create_group('/entry')
        hf['/entry/data/data'] = self.data_stack_3d
        hf.close()

    def convert(self):
        try:
            if self.nframes > 100:
                n_chunks = int(self.nframes / 100) + 1
                for ii in range(n_chunks):
                    start = 100 * ii
                    stop = 100 * (ii + 1)
                    try:
                        for jj in range(start, stop):
                            self.populate_stack(jj)
                        prefix = "data_stack_" + str(ii) + '.h5'
                        self.H5write(prefix)
                    except IndexError:
                        pass
            else:
                for jj in range(self.nframes):
                    self.populate_stack(jj)
                prefix = "data_stack_01.h5"
                self.H5write(prefix)
        except Exception as e:
            raise e
        return


if __name__ == '__main__':
    import glob

    # lst_cbfs = glob.glob('/data/id23eh2/inhouse/opid232/20181208/RAW_DATA/Sample-1-1-03/MeshScan_02/*.cbf')
    image_prefix = '/data/id23eh2/inhouse/opid232/20181208/RAW_DATA/Sample-1-1-03/MeshScan_02'
    dozorfolder = '/users/basus/test/tst_cbfs2h5/dozor'
    dozor_results = prep_spot(image_prefix, dozorfolder)
    stacklength = len(dozor_results)
    lst_cbfs = []
    npeaks = np.empty((stacklength,))
    # PeakXPosRaw = np.empty(())
    for iminfo in dozor_results:
        lst_cbfs.append(iminfo['image_name'])
    packet = Pack_hdf5(lst_cbfs)
    packet.convert()
