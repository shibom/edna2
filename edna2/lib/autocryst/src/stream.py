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
__date__ = '2018/12/14'

from io import open
import os
import sys
import copy
import re
import logging
import numpy as np
import json

from edna2.lib.autocryst.src.point_group import *

logger = logging.getLogger('autoCryst')

chunk_template = """\
----- Begin chunk -----
Image filename: {image} 
Event: {event}
Image serial number: {serial_number}
hit = {hit}
indexed_by = 'mosflm-nolatt-nocell' 
photon_energy_eV = {photon}
beam_divergence = {divergence}
beam_bandwidth = {bandwidth} 
average_camera_length = {distance}
num_peaks = {nPeaks}
num_saturated_peaks = {nSat}
Peaks from peak search 
  fs/px   ss/px (1/d)/nm^-1   Intensity  Panel 
"""
crystal_template = """\
End of peak list
--- Begin crystal
Cell parameters {cellstring} 
astar = {astar} 
bstar = {bstar} 
cstar = {cstar}
lattice_type = {lattice_type}
centering = {centering}
unique_axis = {unique_axis}
profile_radius = {profile_radius}
predict_refine/final_residual = {residual}
diffraction_resolution_limit = 2.33 nm^-1 or 4.28 A
num_reflections = {nRefs}
num_saturated_reflections = 0
num_implausible_reflections = 0
Reflections measured after indexing
   h    k    l          I   sigma(I)       peak background  fs/px  ss/px panel
"""


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
            self.header_index = []
            self.is_indexed = []
            self.codgas_lookup = dict()
            # attributes owing to the output data...
            self.header = []
            self.stream_data = []
            self.cells_only = []
            self.image_refls = []
            self.image_peaks = dict()
            self.mean_xshift = self.mean_yshift = 0.0

            # patterns search to extract useful infos from each image..
            self.rx_dict = dict(image=re.compile(r'Image\sfilename:\s(?P<image>.*)\n'),
                                event=re.compile(r"Event:\s(?P<event>.*)\n"),
                                serial_number=re.compile(r'Image\sserial\snumber:\s(?P<serial_number>[0-9]+)\n'),
                                nPeaks=re.compile(r'num_peaks\s=\s(?P<nPeaks>[0-9]+)\n'),
                                nSat=re.compile(r'num_saturated_peaks\s=\s(?P<nSat>[0-9]+)\n'),
                                hit=re.compile(r'hit\s=\s(?P<hits>[0-9]+)\n'),
                                photon=re.compile(r'photon_energy_eV\s=\s(?P<photon>[0-9.]+)\n'),
                                divergence=re.compile(r'beam_divergence\s=\s(?P<divergence>.*)\n'),
                                bandwidth=re.compile(r'beam_bandwidth\s=\s(?P<bandwidth>.*)\n'),
                                distance=re.compile(r'average_camera_length\s=\s(?P<distance>([0-9.]+)\sm)\n'),
                                nRefs=re.compile(r'num_reflections\s=\s(?P<nRefs>[0-9]+)\n'),
                                lattice_type=re.compile(r'lattice_type\s=\s(?P<lattice_type>[a-z]+)\n'),
                                centering=re.compile(r'centering\s=\s(?P<centering>[A-Z])\n'),
                                unique_axis=re.compile(r'unique_axis\s=\s(?P<unique_axis>[a-c*?])\n'),
                                rescut=re.compile(r'^diffraction_resolution_limit\s='
                                                  r'\s(?P<rescut>([0-9.]+)\snm\^-1\sor\s([0-9.]+)\sA$)\n'),
                                cell=re.compile(r'^Cell\sparameters\s(?P<cell>([0-9.]+)\s([0-9.]+)\s([0-9.]+)\snm,'
                                                r'\s([0-9.]+)\s([0-9.]+)\s([0-9.]+)\sdeg$)\n'),
                                astar=re.compile(r'astar\s=\s(?P<astar>.*)\n'),
                                bstar=re.compile(r'bstar\s=\s(?P<bstar>.*)\n'),
                                cstar=re.compile(r'cstar\s=\s(?P<cstar>.*)\n'),
                                profile_radius=re.compile(r'profile_radius\s=\s'
                                                          r'(?P<profile_radius>([0-9.]+)\snm\^-1)\n'),
                                residual=re.compile(r'predict_refine/final_residual\s=\s(?P<residual>.*)\n'),
                                xy_shift=re.compile(r'^predict_refine/det_shift\sx\s='
                                                    r'\s(?P<xy_shift>([0-9.\-]+)\sy\s=\s([0-9.\-]+)\smm$)\n'),
                                z_shift=re.compile(r'^predict_refine/clen_shift\s=\s(?P<z_shift>([0-9.\-]+)\smm$)\n'))
            return

    def get_chunk_pointers(self):
        """
        This method allows to store each chunks of the Large Stream file as table and access by line number
        """
        header_start = re.compile("CrystFEL stream format 2.3")
        header_end = re.compile("----- End geometry file -----")
        chunk1 = re.compile("----- Begin chunk")
        chunk2 = re.compile("----- End chunk")
        peak_start = re.compile("Peaks from peak search")
        peak_end = re.compile("End of peak list")
        ind1 = re.compile("^indexed_by")
        ind2 = re.compile("none")
        refls_start = re.compile("Reflections measured after indexing")
        refls_end = re.compile("End of reflections")

        self.codgas_lookup['begin_chunk_all'] = []
        self.codgas_lookup['end_chunk_all'] = []
        self.codgas_lookup['begin_peak_list_all'] = []
        self.codgas_lookup['end_peak_list_all'] = []
        self.codgas_lookup['begin_reflist'] = []
        self.codgas_lookup['end_reflist'] = []

        len_each_line = 0
        with open(self.streamfile, 'r') as f:
            for index, line in enumerate(f):
                self.store_line_lengths[index] = len_each_line
                len_each_line += len(line)

                if header_start.search(line):
                    self.header_index.append(index)
                if header_end.search(line):
                    self.header_index.append(index)

                if chunk1.search(line):
                    self.codgas_lookup['begin_chunk_all'].append(index)

                if chunk2.search(line):
                    self.codgas_lookup['end_chunk_all'].append(index)

                if peak_start.search(line):
                    self.codgas_lookup['begin_peak_list_all'].append(index)

                if peak_end.search(line):
                    self.codgas_lookup['end_peak_list_all'].append(index)

                if ind1.search(line):
                    if ind2.search(line):
                        indexed = False
                    else:
                        indexed = True
                    self.is_indexed.append(indexed)

                if refls_start.search(line):
                    self.codgas_lookup['begin_reflist'].append(index)

                if refls_end.search(line):
                    self.codgas_lookup['end_reflist'].append(index)

        self.codgas_lookup['begin_chunk'] = []
        self.codgas_lookup['end_chunk'] = []
        self.codgas_lookup['begin_peaklist'] = []
        self.codgas_lookup['end_peaklist'] = []

        for ii in range(len(self.is_indexed)):
            if self.is_indexed[ii]:
                self.codgas_lookup['begin_chunk'].append(self.codgas_lookup['begin_chunk_all'][ii])
                self.codgas_lookup['end_chunk'].append(self.codgas_lookup['end_chunk_all'][ii])
                self.codgas_lookup['begin_peaklist'].append(self.codgas_lookup['begin_peak_list_all'][ii])
                self.codgas_lookup['end_peaklist'].append(self.codgas_lookup['end_peak_list_all'][ii])
            else:
                pass

        return

    def read_chunks(self, begin_chunk_id, end_chunk_id):
        self.fobject.seek(0)  # set the file pointer at the start position..

        for jj in range(self.header_index[0], self.header_index[1]):
            self.fobject.seek(self.store_line_lengths[jj])
            line = self.fobject.readline().strip('\n')
            self.header.append(line)

        self.fobject.seek(0)
        for start, end in zip(begin_chunk_id, end_chunk_id):
            each_chunk_dict = copy.deepcopy({})  # store info from each chunk as dictionary..
            for ii in range(start, end+1):
                self.fobject.seek(self.store_line_lengths[ii])  # bring the pointer to the correct line number..
                line = self.fobject.readline()  # read one line at a time, faster for large files

                for k, pat in self.rx_dict.items():
                    match = pat.search(line)
                    if match:
                        if k == 'image':
                            each_chunk_dict[k] = match.group('image')
                        if k == 'event':
                            each_chunk_dict[k] = match.group('event')
                        if k == 'serial_number':
                            each_chunk_dict[k] = match.group('serial_number')
                        if k == 'nPeaks':
                            each_chunk_dict[k] = int(match.group('nPeaks'))
                        if k == 'nSat':
                            each_chunk_dict[k] = int(match.group('nSat'))
                        if k == 'hit':
                            each_chunk_dict[k] = int(match.group('hits'))
                        if k == 'photon':
                            each_chunk_dict[k] = float(match.group('photon'))
                        if k == 'divergence':
                            each_chunk_dict[k] = match.group('divergence')
                        if k == 'bandwidth':
                            each_chunk_dict[k] = match.group('bandwidth')
                        if k == 'distance':
                            each_chunk_dict[k] = match.group('distance')
                        if k == 'nRefs':
                            each_chunk_dict[k] = int(match.group('nRefs'))
                        if k == 'lattice_type':
                            each_chunk_dict[k] = match.group('lattice_type')
                        if k == 'centering':
                            each_chunk_dict[k] = match.group('centering')
                        if k == 'unique_axis':
                            each_chunk_dict[k] = match.group('unique_axis')
                        if k == 'rescut':
                            each_chunk_dict[k] = float(match.group('rescut').split()[3])
                        if k == 'cell':
                            param = match.group('cell')
                            each_chunk_dict['cellstring'] = param
                            param = param.split()
                            unit_cell = {'a': float(param[0]), 'b': float(param[1]), 'c': float(param[2]),
                                         'al': float(param[4]), 'be': float(param[5]), 'ga': float(param[6])}
                            each_chunk_dict[k] = unit_cell
                        if k == 'astar':
                            each_chunk_dict[k] = match.group('astar')
                        if k == 'bstar':
                            each_chunk_dict[k] = match.group('bstar')
                        if k == 'cstar':
                            each_chunk_dict[k] = match.group('cstar')
                        if k == 'profile_radius':
                            each_chunk_dict[k] = match.group('profile_radius')
                        if k == 'residual':
                            each_chunk_dict[k] = match.group('residual')

                        if k == 'xy_shift':
                            each_chunk_dict['x_shift'] = float(match.group('xy_shift').split()[0])

                            each_chunk_dict['y_shift'] = float(match.group('xy_shift').split()[3])
                        if k == 'z_shift':
                            each_chunk_dict['z_shift'] = float(match.group('z_shift').split()[0])

            event = each_chunk_dict.get('event', '0')
            if event != '0':
                each_chunk_dict['image'] = each_chunk_dict['image'] + each_chunk_dict['event']
            else:
                each_chunk_dict['event'] = event
            # store everything as a list of dictionaries ..
            self.stream_data.append(each_chunk_dict)

        return

    def get_peaklist(self, begin_peak_list, end_peak_list):
        try:
            for start, end, each_chunk in zip(begin_peak_list, end_peak_list, self.stream_data):

                self.image_peaks[each_chunk['image']] = []
                for jj in range(start+2, end):
                    self.fobject.seek(self.store_line_lengths[jj])
                    line = self.fobject.readline()
                    as_float = list(map(float, line.split()[:4]))
                    self.image_peaks[each_chunk['image']].append(as_float)

        except (IndexError, ValueError, KeyError) as err:
            logger.info('Stream_Error:{}'.format(err))
        return

    def get_reflections_list(self, begin_reflist, end_reflist):
        # Method to return a list of dictionaries, each of which contains indexed chunks
        # along with reflection list..
        self.fobject.seek(0)
        try:
            for start, end, each_chunk in zip(begin_reflist, end_reflist, self.stream_data):
                if 'cell' in each_chunk.keys():
                    each_chunk['refList'] = []

                    for jj in range(start+2, end):
                        self.fobject.seek(self.store_line_lengths[jj])
                        line = self.fobject.readline()
                        as_float = list(map(float, line.split()[:9]))
                        each_chunk['refList'].append(as_float)
                    self.image_refls.append(each_chunk)
                else:
                    pass
        except (IndexError, ValueError, KeyError) as err:
            logger.info('Stream_Error:{}'.format(err))
        return

    @staticmethod
    def create_reflist_json(reflist_stream_class):
        if not reflist_stream_class:
            pass
        else:
            outdata = 'reflections_Stream.json'
            with open(outdata, 'w') as js:
                json.dump({"ReflectionDictionary": reflist_stream_class}, js, sort_keys=True, indent=2)
        return

    @staticmethod
    def write_stream(listofrefsdict, peaksdict, header, outfile):
        with open(outfile, 'w') as sh:
            for line in header:
                sh.write(line)
                sh.write('\n')
            sh.write("----- End geometry file -----\n")
            for k, v in peaksdict.items():
                for chunk in listofrefsdict:
                    if chunk['image'] == k:
                        sh.write(chunk_template.format(**chunk))
                        for spot in v:
                            sh.write("%7.2f %7.2f %11.2f %11.2f %2i\n" % (spot[0], spot[1], spot[2], spot[3], 0))
                        sh.write(crystal_template.format(**chunk))
                        for ref in chunk['refList']:
                            sh.write("%4d %4d %4d %10.2f %10.2f %10.2f %10.2f %6.1f %6.1f %2d\n" %
                                     (int(ref[0]), int(ref[1]), int(ref[2]),
                                      ref[3], ref[4], ref[5], ref[6], ref[7], ref[8], 0))
                        sh.write("End of reflections\n")
                        sh.write("--- End crystal\n")
                        sh.write("----- End chunk -----\n")
        return

    def convert_chunk_to_xdsascii(self):
        num_ascii_total = len(self.image_refls)
        if num_ascii_total > 0:
            tracker = open('chunktrack.txt', 'w')
            for ii in range(num_ascii_total):
                image = self.image_refls[ii]  # type list
                cell_this_image = image['cell']
                cen = image['centering']
                cell_as_lst = [cell_this_image['a'], cell_this_image['b'], cell_this_image['c'],
                               cell_this_image['al'], cell_this_image['be'], cell_this_image['ga']]
                lat, ua, cell_as_lst = lattice_from_cell(cell_as_lst)
                pg, sg, sgn = assign_point_group(lat, cen, ua)
                asciiname = 'xds_%d.HKL' % ii
                tracker.write("ImageFile: %s --> %s\n" % (image['image'], asciiname))
                fh = open(asciiname, 'w')
                fh.write("!FORMAT=XDS_ASCII   MERGE=FALSE   FRIEDEL'S_LAW=TRUE\n")
                fh.write("!SPACE_GROUP_NUMBER=%s\n" % sgn)
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
                for reflection in image['refList']:
                    fh.write("%6i %6i %5i %9.2f %9.2f\n" % (int(reflection[0]), int(reflection[1]), int(reflection[2]),
                                                            reflection[3], reflection[5]))
                fh.write("!END_OF_DATA")
                fh.close()
            tracker.close()
        else:
            err = "Nothing got indexed, no reflections"
            logger.info('Stream_Error:{}'.format(err))

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


def stream2xdslist(streamlist):
    if len(streamlist) == 0:
        print("No streamfile provided\n")
        return
    else:
        current = os.getcwd()
        for streamfile in streamlist:
            try:
                folder = os.path.basename(streamfile).split('.')[0]
                os.path.join(current, folder)
                os.makedirs(folder, exist_ok=True)
                os.chdir(folder)
                s = Stream(streamfile)
                s.get_chunk_pointers()
                s.read_chunks(s.codgas_lookup['begin_chunk'], s.codgas_lookup['end_chunk'])
                s.get_reflections_list(s.codgas_lookup['begin_reflist'], s.codgas_lookup['end_reflist'])
                s.close()
                s.convert_chunk_to_xdsascii()
                print("%d HKLs were written from %s into %s folder" % (len(s.image_refls), streamfile, folder))
                os.chdir(current)
            except Exception as err:
                logger.error('Stream_Error: {}'.format(err))
    return


if __name__ == '__main__':

    s = Stream(sys.argv[1])
    s.get_chunk_pointers()

    s.read_chunks(s.codgas_lookup['begin_chunk'][:100], s.codgas_lookup['end_chunk'])
    s.get_peaklist(s.codgas_lookup['begin_peaklist'][:100], s.codgas_lookup['end_peaklist'][:100])
    s.get_reflections_list(s.codgas_lookup['begin_reflist'][:100], s.codgas_lookup['end_reflist'][:100])

    s.close()

    s.write_stream(s.image_refls, s.image_peaks, s.header, 'tst1.stream')
    '''
    fh = open('only_indexed_images.lst', 'w')
    for indexed_image in s.image_refls.keys():
        fh.write(indexed_image)
        fh.write('\n')
    fh.close()
    
    '''
