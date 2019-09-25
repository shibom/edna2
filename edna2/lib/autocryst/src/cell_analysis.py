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
__date__ = '2018/12/17'

import sys
import os
from collections import Counter
import numpy as np
# import scipy.cluster.vq as cvq
# import scipy.cluster.hierarchy as sch
from scipy import stats
import math
import logging
from edna2.lib.autocryst.src.point_group import *
from edna2.lib.autocryst.src.stream import Stream

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
        self.stream_handle.read_chunks(self.stream_handle.codgas_lookup['begin_chunk'],
                                       self.stream_handle.codgas_lookup['end_chunk'])
        self.stream_handle.get_reflections_list(self.stream_handle.codgas_lookup['begin_chunk'],
                                                self.stream_handle.codgas_lookup['end_chunk'])
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
            logger.error('Cell_Error:{}'.format(err))
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
            logger.error('Cell_Error:{}'.format(err))
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
            logger.error('Cell_Error:{}'.format(err))
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
            logger.error('Cell_Error:{}'.format(err))
        return

    def convert_indexed_to_xdsascii(self):

        # Call this method after calling self.get_lattices(), self.get_cells(), and self.calc_modal_cell() methods

        if len(self.stream_handle.image_refls) == 0:
            logger.error('Cell_Error:{}'.format('Nothing is indexed'))
        else:
            num_ascii_total = len(self.stream_handle.image_refls)
            cell_as_lst = [self.a_mode, self.b_mode, self.c_mode, self.al_mode, self.be_mode, self.ga_mode]
            lat, ua, cell_as_lst = lattice_from_cell(cell_as_lst)
            pg, sg, sgn = assign_point_group(lat, self.most_common_centering, ua)
            print("No. of indexed chunks found: %d" % num_ascii_total)
            tracker = open('chunktrack.txt', 'w')
            for ii in range(num_ascii_total):
                image = self.stream_handle.image_refls[ii]  # type list

                asciiname = 'xds_%d.HKL' % ii
                tracker.write("ImageFile: %s --> %s\n" % (image['image'], asciiname))
                fh = open(asciiname, 'w')
                fh.write("!FORMAT=XDS_ASCII   MERGE=FALSE   FRIEDEL'S_LAW=TRUE\n")
                fh.write("!SPACE_GROUP_NUMBER=%s\n" % sgn)
                fh.write(
                    "!UNIT_CELL_CONSTANTS=%f %f %f %f %f %f\n" % (cell_as_lst[0], cell_as_lst[1], cell_as_lst[2],
                                                                  cell_as_lst[3], cell_as_lst[4], cell_as_lst[5]))
                fh.write("!NUMBER_OF_ITEMS_IN_EACH_DATA_RECORD=5\n")
                fh.write("!X-RAY_WAVELENGTH= -1.0\n")
                fh.write("!ITEM_H=1\n")
                fh.write("!ITEM_K=2\n")
                fh.write("!ITEM_L=3\n")
                fh.write("!ITEM_IOBS=4\n")
                fh.write("!ITEM_SIGMA(IOBS)=5\n")
                fh.write("!END_OF_HEADER\n")
                for reflection in image['refList']:
                    fh.write(
                        "%6i %6i %5i %9.2f %9.2f\n" % (int(reflection[0]), int(reflection[1]), int(reflection[2]),
                                                       reflection[3], reflection[5]))
                fh.write("!END_OF_DATA")
                fh.close()
            tracker.close()

        return


def stream2xdslist(streamlist):
    if len(streamlist) == 0:
        print("No streamfile provided\n")
        return
    else:
        current = os.getcwd()
        for streamfile in streamlist:
            try:
                folder = os.path.basename(streamfile).split('.')[0]
                folder = os.path.join(current, folder)
                s = Cell(streamfile)
                if s.status:
                    os.makedirs(folder, exist_ok=True)
                    os.chdir(folder)
                    s.get_lattices()
                    s.get_cells()
                    s.calc_modal_cell()
                    s.convert_indexed_to_xdsascii()
                    print("%d HKLs were written from %s into %s folder" % (len(s.stream_handle.image_refls),
                                                                           streamfile, folder))
                else:
                    pass
                os.chdir(current)
            except Exception as err:
                logger.error('Cell_Error: {}'.format(err))
    return


if __name__ == '__main__':

    c = Cell(sys.argv[1])
    c.get_lattices()
    c.get_cells()
    c.calc_modal_cell()
    c.convert_indexed_to_xdsascii()


