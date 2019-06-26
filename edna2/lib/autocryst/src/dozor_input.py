"""
Created on 22-May-2019
Author: S. Basu
"""
from __future__ import print_function

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
