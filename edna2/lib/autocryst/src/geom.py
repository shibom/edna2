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

import logging
import sys


logger = logging.getLogger("autoCryst")

geom_template = """\
photon_energy = {photon_energy}
clen = {clen}
coffset = {coffset}
adu_per_eV = {adu_per_eV}
res = {res}
0/min_fs = {0/min_fs}
0/max_fs = {0/max_fs}
0/min_ss = {0/min_ss}
0/max_ss = {0/max_ss}
0/fs = {0/fs}
0/ss = {0/ss}
0/corner_x = {0/corner_x}
0/corner_y = {0/corner_y}
"""
geom_eiger = """
mask_file = {mask_file}
mask = {mask}
mask_good = 0x00
mask_bad = 0xFF
dim0 = %
dim1 = ss
dim2 = fs
data = /entry/data/data
"""
geom_eiger += geom_template

geom_cxi = geom_template + """\
dim0 = %
dim1 = ss
dim2 = fs
data = /data/data
"""


class Geom(object):

    def __init__(self, detectortype, detectorsize):
        self.detectorName = (detectortype + detectorsize).lower()
        self.detectorGeom = {}
        self.bad_regs = {}
        self.geomfilename = 'empty.geom'
        self.supportedType = ['pilatus3', 'pilatus', 'eiger']
        self.supportedSize = ["2m", "6m", "4m", "16m"]
        self.supportedList = ['pilatus32m', 'pilatus36m', 'pilatus6m', 'pilatus2m', 'eiger4m', 'eiger16m']
        if self.detectorName not in self.supportedList:
            err = "%s detector type not supported" % self.detectorName
            logger.info('Detector_Error:{}'.format(err))
            return
        elif self.detectorName == 'pilatus36m' or self.detectorName == 'pilatus6m':
            self.detectorName = 'pilatus36m'
        else:
            pass

        return

    def create_detector_geom(self, img_header, **kwargs):
        coffset = kwargs.get('coffset', 0.0)
        fs0 = kwargs.get('fs0', 'x')
        ss0 = kwargs.get('ss0', 'y')
        try:
            self.detectorGeom['photon_energy'] = img_header['photon_energy']
            self.detectorGeom['clen'] = img_header['detector_distance']
            self.detectorGeom['adu_per_eV'] = 1.0 / img_header['photon_energy']
            self.detectorGeom['res'] = 1.0 / img_header['pixel_size']
            self.detectorGeom['0/corner_x'] = -img_header['beam_center_x']
            self.detectorGeom['0/corner_y'] = -img_header['beam_center_y']
            self.detectorGeom['0/fs'] = fs0
            self.detectorGeom['0/ss'] = ss0
            self.detectorGeom['0/min_fs'] = 0
            self.detectorGeom['0/min_ss'] = 0
            self.detectorGeom['coffset'] = coffset
            if self.detectorName == 'pilatus32m':
                self.detectorGeom['0/max_fs'] = 1474
                self.detectorGeom['0/max_ss'] = 1678
            elif self.detectorName == 'pilatus36m':
                self.detectorGeom['0/max_fs'] = 2462
                self.detectorGeom['0/max_ss'] = 2526
            elif 'eiger' in self.detectorName:
                self.detectorGeom['mask_file'] = img_header['filename']
                self.detectorGeom['mask'] = '/entry/instrument/detector/detectorSpecific/pixel_mask'
                if self.detectorName == 'eiger16m':
                    self.detectorGeom['0/max_fs'] = 4149
                    self.detectorGeom['0/max_ss'] = 4370
                else:
                    self.detectorGeom['0/max_fs'] = 2069
                    self.detectorGeom['0/max_ss'] = 2166

        except KeyError:
            err = 'keyword not found in image header.Please check the image header'
            logger.info('Detector_Error: {}'.format(err))
            logger.info('Image_header: {}'.format(img_header))
        return

    @staticmethod
    def gaps_between_panels(fs_width, ss_width, n_hgaps, n_vgaps, gap_pix_v, gap_pix_h):
        list_bad_region = []
        tile_size_ss = (ss_width - (gap_pix_v * n_vgaps)) / (n_vgaps + 1)
        tile_size_fs = (fs_width - (gap_pix_h * n_hgaps)) / (n_hgaps + 1)

        for i in range(n_vgaps):
            bad_regs = {}
            min_ss = 'bad_v_' + str(i) + '/min_ss'
            bad_regs[min_ss] = tile_size_ss * (i + 1) + (gap_pix_v - 1) * i
            max_ss = 'bad_v_' + str(i) + '/max_ss'
            bad_regs[max_ss] = bad_regs[min_ss] + (gap_pix_v - 1)
            min_fs = 'bad_v_' + str(i) + '/min_fs'
            max_fs = 'bad_v_' + str(i) + '/max_fs'
            bad_regs[min_fs] = 0
            bad_regs[max_fs] = fs_width - 1
            list_bad_region.append(bad_regs)

        for i in range(n_hgaps):
            bad_regs = {}
            min_fs = 'bad_h_' + str(i) + '/min_fs'
            bad_regs[min_fs] = tile_size_fs * (i + 1) + (gap_pix_h - 1) * i
            max_fs = 'bad_h_' + str(i) + '/max_fs'
            bad_regs[max_fs] = bad_regs[min_fs] + (gap_pix_h - 1)
            min_ss = 'bad_h_' + str(i) + '/min_ss'
            max_ss = 'bad_h_' + str(i) + '/max_ss'
            bad_regs[min_ss] = 0
            bad_regs[max_ss] = ss_width - 1
            list_bad_region.append(bad_regs)

        return list_bad_region

    def add_bad_regions(self):
        if self.detectorName == 'pilatus32m':

            fs_width = 1475
            ss_width = 1679
            n_hgaps = 2
            n_vgaps = 7
            gap_pix_v = 17
            gap_pix_h = 7
            self.bad_regs = Geom.gaps_between_panels(fs_width, ss_width, n_hgaps, n_vgaps, gap_pix_v, gap_pix_h)
        elif self.detectorName == 'pilatus36m':
            fs_width = 2463
            ss_width = 2527
            n_hgaps = 4
            n_vgaps = 11
            gap_pix_v = 17
            gap_pix_h = 7
            self.bad_regs = Geom.gaps_between_panels(fs_width, ss_width, n_hgaps, n_vgaps, gap_pix_v, gap_pix_h)
        elif self.detectorName == 'eiger4m':
            fs_width = 2070
            ss_width = 2167
            n_hgaps = 1
            n_vgaps = 3
            gap_pix_v = 37
            gap_pix_h = 10
            self.bad_regs = Geom.gaps_between_panels(fs_width, ss_width, n_hgaps, n_vgaps, gap_pix_v, gap_pix_h)
        else:
            pass

        return

    def eiger16m_geom(self, img_header):
        return

    def write_geomfile(self, img_header, **kwargs):
        cxi = kwargs.get('cxi', "")
        self.create_detector_geom(img_header, **kwargs)
        self.add_bad_regions()
        # geom_template += cxi
        if self.detectorName == 'pilatus32m':
            self.geomfilename = 'pilatus2m.geom'
            ofh = open(self.geomfilename, 'w')
            ofh.write(cxi+'\n')
            ofh.write(geom_template.format(**self.detectorGeom))
            ofh.write('\n\n')
            for each_row in self.bad_regs:
                for k, v in each_row.items():
                    ofh.write('%s = %s\n' % (k, v))
                ofh.write('\n')
            ofh.close()

        elif self.detectorName == 'pilatus36m':
            self.geomfilename = 'pilatus6m.geom'
            ofh = open(self.geomfilename, 'w')
            ofh.write(cxi+'\n')
            ofh.write(geom_template.format(**self.detectorGeom))
            ofh.write('\n\n')
            for each_row in self.bad_regs:
                for k, v in each_row.items():
                    ofh.write('%s = %s\n' % (k, v))
                ofh.write('\n')
            ofh.close()

        elif self.detectorName == 'eiger16m':
            self.geomfilename = 'eiger16m.geom'
            ofh = open(self.geomfilename, 'w')
            ofh.write(geom_template.format(**self.detectorGeom))
            ofh.close()
        elif self.detectorName == 'eiger4m':
            self.geomfilename = 'eiger4m.geom'
            ofh = open(self.geomfilename, 'w')
            ofh.write(geom_eiger.format(**self.detectorGeom))
            ofh.write('\n\n')

            for each_row in self.bad_regs:
                for k, v in each_row.items():
                    ofh.write('%s = %s\n' % (k, v))
                ofh.write('\n')
            ofh.close()
        else:
            err = "Check detector name, maybe provided an unsupported one"
            logger.info('Detector_Error:{}'.format(err))
        return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='test.log',
                        filemode='a+')

    from edna2.lib.autocryst.src.Image import ImageHandler as Im

    c = Im(sys.argv[1])
    # c = Im('../examples/mesh-x_2_1_master.h5')
    g = Geom(c.imobject.headers['detector_name'][0], c.imobject.headers['detector_name'][1])
    kk = dict()
    kk['cxi'] = """dim0 = %\ndim1 = ss\ndim2 = fs\ndata = /data/data"""
    g.write_geomfile(c.imobject.headers, **kk)
