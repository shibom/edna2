"""
Created on 14-Dec-2018
Author: S. Basu
"""
from __future__ import division, print_function, unicode_literals
from io import open
import os
import sys
import copy
import re
import logging
import numpy as np
from src.point_group import *
import json


logger = logging.getLogger('autoCryst')


class Stream(object):

    def __init__(self, stream_name):
        """

        :rtype: object to handle large files as a file handler and load as a table.
        """
        if not os.path.exists(stream_name):
            err = "%s file does not exist" % stream_name
            logger.info('Stream_Error:{}'.format(err))
            return
        else:
            self.streamfile = stream_name
            self.fobject = open(self.streamfile, 'r')
            """
            :rtype: line -> str
            """
            length = sum(1 for line in self.fobject)

            self.store_line_lengths = np.zeros(length)
            self.begin_chunk_id = []
            self.end_chunk_id = []
            self.begin_peak_list = []
            self.end_peak_list = []
            self.begin_reflist = []
            self.end_reflist = []

            self.stream_data = []
            self.cells_only = []
            self.image_peaks = dict()
            self.image_refls = dict()
            self.each_chunk_dict = dict()
            self.mean_xshift = self.mean_yshift = 0.0

            # patterns search to extract useful infos from each image..
            self.rx_dict = dict(image=re.compile(r'Image\sfilename:\s(?P<image>.*)\n'),
                                nPeaks=re.compile(r'num_peaks\s=\s(?P<nPeaks>[0-9]+)\n'),
                                hits=re.compile(r'hits\s=\s(?P<hits>[0-1])\n'),
                                nRefs=re.compile(r'num_reflections\s=\s(?P<nRefs>[0-9]+)\n'),
                                lattice_type=re.compile(r'lattice_type\s=\s(?P<lattice_type>[a-z]+)\n'),
                                centering=re.compile(r'centering\s=\s(?P<centering>[A-Z])\n'),
                                unique_axis=re.compile(r'unique_axis\s=\s(?P<unique_axis>[a-c*?])\n'),
                                rescut=re.compile(r'^diffraction_resolution_limit\s='
                                                  r'\s(?P<rescut>([0-9.]+)\snm\^-1\sor\s([0-9.]+)\sA$)\n'),
                                cell=re.compile(r'^Cell\sparameters\s(?P<cell>([0-9.]+)\s([0-9.]+)\s([0-9.]+)\snm,'
                                                r'\s([0-9.]+)\s([0-9.]+)\s([0-9.]+)\sdeg$)\n'),
                                xy_shift=re.compile(r'^predict_refine/det_shift\sx\s='
                                                    r'\s(?P<xy_shift>([0-9.\-]+)\sy\s=\s([0-9.\-]+)\smm$)\n'),
                                z_shift=re.compile(r'^predict_refine/clen_shift\s=\s(?P<z_shift>([0-9.\-]+)\smm$)\n'))
            return

    def get_chunk_pointers(self):
        """
        This method allows to store each chunks of the Large Stream file as table and access by line number
        """
        chunk1 = re.compile("----- Begin chunk")
        chunk2 = re.compile("----- End chunk")
        peak_start = re.compile("Peaks from peak search")
        peak_end = re.compile("End of peak list")
        refls_start = re.compile("Reflections measured after indexing")
        refls_end = re.compile("End of reflections")

        len_each_line = 0
        with open(self.streamfile, 'r') as f:
            for index, line in enumerate(f):
                self.store_line_lengths[index] = len_each_line
                len_each_line += len(line)

                if chunk1.search(line):
                    self.begin_chunk_id.append(index)
                if chunk2.search(line):
                    self.end_chunk_id.append(index)
                if peak_start.search(line):
                    self.begin_peak_list.append(index)
                if peak_end.search(line):
                    self.end_peak_list.append(index)
                if refls_start.search(line):
                    self.begin_reflist.append(index)
                if refls_end.search(line):
                    self.end_reflist.append(index)
        return

    def read_chunks(self):
        self.fobject.seek(0)  # set the file pointer at the start position..

        for start, end in zip(self.begin_chunk_id, self.end_chunk_id):
            self.each_chunk_dict = copy.deepcopy({})  # store info from each chunk as dictionary..
            for ii in range(start, end+1):
                self.fobject.seek(self.store_line_lengths[ii])  # bring the pointer to the correct line number..
                line = self.fobject.readline()  # read one line at a time, faster for large files

                for k, pat in self.rx_dict.items():
                    match = pat.search(line)
                    if match:
                        if k == 'image':
                            self.each_chunk_dict[k] = match.group('image')
                        if k == 'nPeaks':
                            self.each_chunk_dict[k] = int(match.group('nPeaks'))
                        if k == 'nRefs':
                            self.each_chunk_dict[k] = int(match.group('nRefs'))
                        if k == 'lattice_type':
                            self.each_chunk_dict[k] = match.group('lattice_type')
                        if k == 'centering':
                            self.each_chunk_dict[k] = match.group('centering')
                        if k == 'unique_axis':
                            self.each_chunk_dict[k] = match.group('unique_axis')
                        if k == 'rescut':
                            self.each_chunk_dict[k] = float(match.group('rescut').split()[3])
                        if k == 'cell':
                            param = match.group('cell')
                            param = param.split()
                            unit_cell = {'a': float(param[0]), 'b': float(param[1]), 'c': float(param[2]),
                                         'al': float(param[4]), 'be': float(param[5]), 'ga': float(param[6])}
                            self.each_chunk_dict[k] = unit_cell
                        if k == 'xy_shift':
                            self.each_chunk_dict['x_shift'] = float(match.group('xy_shift').split()[0])

                            self.each_chunk_dict['y_shift'] = float(match.group('xy_shift').split()[3])
                        if k == 'z_shift':
                            self.each_chunk_dict['z_shift'] = float(match.group('z_shift').split()[0])

            # store everything as a list of dictionaries ..
            self.stream_data.append(self.each_chunk_dict)

        return

    def get_peaklist(self):
        try:
            for start, end, each_chunk in zip(self.begin_peak_list, self.end_peak_list, self.stream_data):
                self.image_peaks[each_chunk['image']] = []
                for jj in range(start+2, end):
                    self.fobject.seek(self.store_line_lengths[jj])
                    line = self.fobject.readline()
                    as_float = list(map(float, line.split()[:4]))
                    self.image_peaks[each_chunk['image']].append(as_float)

        except (IndexError, ValueError, KeyError) as err:
            logger.info('Stream_Error:{}'.format(err))
        return

    def get_reflections_list(self):
        try:
            for start, end, each_chunk in zip(self.begin_reflist, self.end_reflist, self.stream_data):
                if 'cell' in each_chunk.keys():
                    self.image_refls[each_chunk['image']] = {}
                    self.image_refls[each_chunk['image']]['cell'] = each_chunk['cell']
                    self.image_refls[each_chunk['image']]['lattice_type'] = each_chunk['lattice_type']
                    self.image_refls[each_chunk['image']]['centering'] = each_chunk['centering']
                    self.image_refls[each_chunk['image']]['unique_axis'] = each_chunk['unique_axis']
                    self.image_refls[each_chunk['image']]['refList'] = []
                    for jj in range(start+2, end):
                        self.fobject.seek(self.store_line_lengths[jj])
                        line = self.fobject.readline()
                        as_float = list(map(float, line.split()[:9]))
                        self.image_refls[each_chunk['image']]['refList'].append(as_float)
                else:
                    pass
        except (IndexError, ValueError, KeyError) as err:
            logger.info('Stream_Error:{}'.format(err))
        return

    @staticmethod
    def create_reflist_json(reflist_dict_stream_class):
        if not reflist_dict_stream_class:
            pass
        else:
            with open('Reflections.json', 'w') as js:
                json.dump(reflist_dict_stream_class, js, sort_keys=True, indent=2)
        return

    def convert_chunk_to_xdsascii(self):
        num_ascii_total = len(self.image_refls.keys())
        if num_ascii_total > 0:
            for ii in range(num_ascii_total):
                image = self.image_refls.keys()[ii]  # type list
                cell_this_image = self.image_refls[image]['cell']
                cen = self.image_refls[image]['centering']
                cell_as_lst = [cell_this_image['a'], cell_this_image['b'], cell_this_image['c'],
                               cell_this_image['al'], cell_this_image['be'], cell_this_image['ga']]
                lat, ua, cell_as_lst = lattice_from_cell(cell_as_lst)
                pg = assign_point_group(lat, cen, ua)

                asciiname = 'xds_%d.HKL' % ii
                fh = open(asciiname, 'w')
                fh.write("!FORMAT=XDS_ASCII   MERGE=FALSE   FRIEDEL'S_LAW=TRUE\n")
                fh.write("!SPACE_GROUP_NUMBER=%s\n" % pg)
                fh.write("!UNIT_CELL_CONSTANTS=%f %f %f %f %f %f\n" % (cell_as_lst[0], cell_as_lst[1], cell_as_lst[2],
                                                                       cell_as_lst[3], cell_as_lst[4], cell_as_lst[5]))
                fh.write("!NUMBER_OF_ITEMS_IN_EACH_DATA_RECORD=5\n")
                fh.write("!X-RAY_WAVELENGTH= -1.0\n")
                fh.write("!ITEM_H=1\n")
                fh.write("!ITEM_K=2\n")
                fh.write("!ITEM_L=3\n")
                fh.write("!ITEM_IOBS=4\n")
                fh.write("!ITEM_SIGMA(IOBS)=5\n")
                fh.write("!END_OF_HEADER\n")
                for reflection in self.image_refls[image]['refList']:
                    fh.write("%6i %6i %5i %9.2f %9.2f\n" % (int(reflection[0]), int(reflection[1]), int(reflection[2]),
                                                            reflection[3], reflection[5]))
                fh.write("!END_OF_DATA")
                fh.close()
        else:
            err = "Nothing got indexed, no reflections"
            logger.info('Stream_Error:{}'.format(err))
            pass
        return

    def close(self):
        self.fobject.close()
        return

    def tell(self):
        # Method to return last pointer position, which can be used along with seek method..
        self.fobject.tell()
        return

    def get_indexed_only(self):
        if self.stream_data:
            for chunk_dict in self.stream_data:
                try:
                    self.cells_only.append(chunk_dict['cell'])
                except KeyError:
                    pass
        else:
            err = "Nothing in the stream data, check if stream exists"
            logger.info('Stream_Error:{}'.format(err))
        return

    def detector_shift(self):
        x_shift = []
        y_shift = []
        z_shift = []

        for chunk in self.stream_data:
            try:
                x_shift.append(chunk['x_shift'])
                y_shift.append(chunk['y_shift'])
                z_shift.append(chunk['z_shift'])
            except KeyError:
                pass
        self.mean_xshift = sum(x_shift) / len(x_shift)
        self.mean_yshift = sum(y_shift) / len(y_shift)
        return


if __name__ == '__main__':

    s = Stream(sys.argv[1])
    s.get_chunk_pointers()
    s.read_chunks()
    s.get_reflections_list()
    s.close()

    Stream.create_reflist_json(s.image_refls)
    print(s.stream_data)
