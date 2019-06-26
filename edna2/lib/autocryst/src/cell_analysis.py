"""
Created on 17-Dec-2018
Author: S. Basu
"""

from __future__ import division, print_function
import sys
from collections import Counter
import numpy as np
# import scipy.cluster.vq as cvq
# import scipy.cluster.hierarchy as sch
from scipy import stats
import math
import logging
from src.stream import Stream


logger = logging.getLogger('autoCryst')


def round_up(n, decimals=0):
    multiplier = 10**decimals
    val = math.ceil(n*multiplier)/multiplier
    return val


def round_down(n, decimals=0):
    multiplier = 10**decimals
    val = math.floor(n*multiplier)/multiplier
    return val


class Cell(object):

    def __init__(self, streamfile):
        self.status = False
        self.stream_handle = Stream(streamfile)
        self.stream_handle.get_chunk_pointers()
        self.stream_handle.read_chunks()
        self.stream_handle.close()
        self.stream_handle.get_indexed_only()
        if self.stream_handle.cells_only:
            self.cell_array = np.empty((len(self.stream_handle.cells_only), 6))
            self.cell_vector = np.empty((len(self.stream_handle.cells_only), 3))
            self.status = True
            self.get_cells()
            self.most_common_centering = 'P'
            self.most_common_lattice_type = 'triclinic'
            self.most_common_unique_axis = '*'
            self.a_mode = self.b_mode = self.c_mode = 0.0
            self.al_mode = self.be_mode = self.ga_mode = 0.0
        else:
            err = "Nothing is indexed in stream file"
            logger.info('Cell_Error:{}'.format(err))
            self.status = False
        return

    def get_lattices(self):
        lattices = []
        centers = []
        uaxis = []
        for each_chunk in self.stream_handle.stream_data:
            try:
                lattices.append(each_chunk['lattice_type'])
                centers.append(each_chunk['centering'])
                uaxis.append(each_chunk['unique_axis'])
            except KeyError:
                pass
        self.most_common_lattice_type = Counter(lattices).most_common(1)[0][0]
        self.most_common_centering = Counter(centers).most_common(1)[0][0]
        self.most_common_unique_axis = Counter(uaxis).most_common(1)[0][0]
        return

    def get_cells(self):
        if self.status:
            for i in range(len(self.stream_handle.cells_only)):
                self.cell_array[i, 0] = self.stream_handle.cells_only[i]['a']*10  # nm->Ang
                self.cell_array[i, 1] = self.stream_handle.cells_only[i]['b']*10
                self.cell_array[i, 2] = self.stream_handle.cells_only[i]['c']*10
                self.cell_array[i, 3] = self.stream_handle.cells_only[i]['al']
                self.cell_array[i, 4] = self.stream_handle.cells_only[i]['be']
                self.cell_array[i, 5] = self.stream_handle.cells_only[i]['ga']

        else:
            err = "Nothing is indexed in stream file, returning empty cell_array"
            logger.info('Cell_Error:{}'.format(err))
            self.status = False
        return

    def calc_vector(self):
        try:
            for i in range(self.cell_vector.shape[0]):
                self.cell_vector[i, 0] = np.sqrt(self.cell_array[i, 0]**2 + self.cell_array[i, 1]**2 -
                                                 2*self.cell_array[i, 0]*self.cell_array[i, 1] *
                                                 np.cos(np.pi-np.deg2rad(self.cell_array[i, 5])))
                self.cell_vector[i, 1] = np.sqrt(self.cell_array[i, 1]**2 + self.cell_array[i, 2]**2 -
                                                 2*self.cell_array[i, 1]*self.cell_array[i, 2] *
                                                 np.cos(np.pi-np.deg2rad(self.cell_array[i, 3])))
                self.cell_vector[i, 2] = np.sqrt(self.cell_array[i, 2]**2 + self.cell_array[i, 0]**2 -
                                                 2*self.cell_array[i, 2]*self.cell_array[i, 0] *
                                                 np.cos(np.pi-np.deg2rad(self.cell_array[i, 4])))
            self.status = True
        except (IndexError, ValueError) as err:
            self.status = False
            logger.info('Cell_Error:{}'.format(err))
        return

    @staticmethod
    def reject_outlier(array):

        ohne_outlier = array[abs(array - np.mean(array)) <= 1.0*np.std(array)]
        ohne_indx = np.where(abs(array - np.mean(array)) <= 1.0*np.std(array))
        ohne_indx = ohne_indx[0].tolist()

        return ohne_outlier, ohne_indx

    @staticmethod
    def calc_mode_or_median(array):
        mode_val = stats.mode(array)[0][0]
        if mode_val == array.min():
            mode_val = np.median(array)
        else:
            pass
        return mode_val

    def calc_modal_cell(self):
        try:
            a_ohne, a_indx = self.reject_outlier(self.cell_array[:, 0])
            b_ohne, b_indx = self.reject_outlier(self.cell_array[:, 1])
            c_ohne, c_indx = self.reject_outlier(self.cell_array[:, 2])
            al_ohne, al_indx = self.reject_outlier(self.cell_array[:, 3])
            be_ohne, be_indx = self.reject_outlier(self.cell_array[:, 4])
            ga_ohne, ga_indx = self.reject_outlier(self.cell_array[:, 5])
            # calculate modal/median values for unit cell parameters..
            self.a_mode = round_down(self.calc_mode_or_median(a_ohne), 1)
            self.b_mode = round_down(self.calc_mode_or_median(b_ohne), 1)
            self.c_mode = round_down(self.calc_mode_or_median(c_ohne), 1)
            self.al_mode = round(self.calc_mode_or_median(al_ohne))
            self.be_mode = round(self.calc_mode_or_median(be_ohne))
            self.ga_mode = round(self.calc_mode_or_median(ga_ohne))

            self.status = True
        except Exception as err:
            self.status = False
            logger.info('Cell_Error:{}'.format(err))
        return


if __name__ == '__main__':

    c = Cell(sys.argv[1])
    c.get_lattices()
    c.get_cells()
    c.calc_modal_cell()

    print(c.a_mode, c.b_mode, c.c_mode, c.al_mode, c.be_mode, c.ga_mode)
    print(c.most_common_lattice_type)
    print(c.most_common_centering)
