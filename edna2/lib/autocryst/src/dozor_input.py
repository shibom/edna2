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
__date__ = '2019/05/15'


dozor_input = dict()

dozor_input['base'] = """\
!
detector {det}
exposure {exposure}
spot_size 3
detector_distance {detector_distance}
X-ray_wavelength {wavelength}
fraction_polarization 0.990
pixel_min 0
pixel_max 64000
orgx {beamx}
orgy {beamy}
oscillation_range {oscillation_range}
image_step 1.0
starting_angle {starting_angle}
first_image_number 1
number_images {nframes}
name_template_image {name_template}
"""

dozor_input['2m'] = dozor_input['base'] + """\
ix_min 717
ix_max 1475
iy_min 809
iy_max 850
end
"""

dozor_input['6m'] = dozor_input['base'] + """\
ix_min 717
ix_max 2462
iy_min 809
iy_max 850
end
"""
