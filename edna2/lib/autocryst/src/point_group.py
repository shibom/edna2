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
__date__ = '2019/01/11'


"""
point_group = {
'1':{'lattice_type':'triclinic', 'centering':'P','unique_axis': '*'},
'2':{'lattice_type': 'monoclinic', 'centering':'P or C','unique_axis':'* or b'},
'222':{'lattice_type': 'orthorhombic', 'centering':'P or C','unique_axis':'*'},
'4':{'lattice_type': 'tetragonal', 'centering':'P or I','unique_axis':'*'},
'422':{'lattice_type': 'tetragonal', 'centering':'P or I','unique_axis':'c'},
'3':{'lattice_type':'hexagonal', 'centering':'P', 'unique_axis':'c'},
'32':{'lattice_type':'rhombohedral', 'centering':'H', 'unique_axis':'c'},
'6':{'lattice_type':'hexagonal', 'centering':'P', 'unique_axis':'*'},
'622':{},
'23':{'lattice_type':'cubic', 'centering':'P or F or I', 'unique_axis':'*'},
'432':{'lattice_type':'cubic', 'centering':'P', 'unique_axis':'c'}
}
"""
space_group = {
    'P1': ('1', 'aP'),
    'P121': ('3', 'mP'),
    'P1211': ('4', 'mP'),
    'C121': ('5', 'mC'),
    'P222': ('16', 'oP'),
    'P2221': ('17', 'oP'),
    'P21212': ('18', 'oP'),
    'P212121': ('19', 'oP'),
    'C2221': ('20', 'oC'),
    'C222': ('21', 'oC'),
    'F222': ('22', 'oF'),
    'I222': ('23', 'oI'),
    'I212121': ('24', 'oI'),
    'P4': ('75', 'tP'),
    'P41': ('76', 'tP'),
    'P42': ('77', 'tP'),
    'P43': ('78', 'tP'),
    'I4': ('79', 'tI'),
    'I41': ('80', 'tI'),
    'P422': ('89', 'tP'),
    'P4212': ('90', 'tP'),
    'P4122': ('91', 'tP'),
    'P41212': ('92', 'tP'),
    'P4222': ('93', 'tP'),
    'P42212': ('94', 'tP'),
    'P4322': ('95', 'tP'),
    'P43212': ('96', 'tP'),
    'I422': ('97', 'tI'),
    'I4122': ('98', 'tI'),
    'P3': ('143', 'trP'),
    'P31': ('144', 'trP'),
    'P32': ('145', 'trP'),
    'R3': ('146', 'Rh'),
    'P312': ('149', 'trP'),
    'P321': ('150', 'trP'),
    'P3112': ('151', 'trP'),
    'P3121': ('152', 'trP'),
    'P3212': ('153', 'trP'),
    'P3221': ('154', 'trP'),
    'R32': ('155', 'Rh'),
    'P6': ('168', 'hP'),
    'P61': ('169', 'hP'),
    'P65': ('170', 'hP'),
    'P62': ('171', 'hP'),
    'P64': ('172', 'hP'),
    'P63': ('173', 'hP'),
    'P622': ('177', 'hP'),
    'P6122': ('178', 'hP'),
    'P6522': ('179', 'hP'),
    'P6222': ('180', 'hP'),
    'P6422': ('181', 'hP'),
    'P6322': ('182', 'hP'),
    'P23': ('195', 'cP'),
    'F23': ('196', 'cF'),
    'I23': ('197', 'cI'),
    'P213': ('198', 'cP'),
    'I213': ('199', 'cI'),
    'P432': ('207', 'cP'),
    'P4232': ('208', 'cP'),
    'F432': ('209', 'cF'),
    'F4132': ('210', 'cF'),
    'I432': ('211', 'cI'),
    'P4332': ('212', 'cP'),
    'P4132': ('213', 'cP'),
    'I4132': ('214', 'cI')
}


def lattice_from_cell(cell_in_list):
    if len(cell_in_list) == 6:
        a = cell_in_list[0]
        b = cell_in_list[1]
        c = cell_in_list[2]
        al = cell_in_list[3]
        be = cell_in_list[4]
        ga = cell_in_list[5]
    else:
        print("all cell_parameters were not provided")
        return
    lat = 'triclinic'
    ua = '*'
    if a == b == c and al == be == ga == 90.0:
        lat = 'cubic'
    elif a == b == c and 85.0 <= al <= be <= ga <= 92.0:
        lat = 'cubic'
    elif abs((a-b)) <= 5.0 and abs((b-c)) <= 5.0 and abs((c-a)) <= 5.0:
        cell_in_list[0] = cell_in_list[1] = cell_in_list[2]
        if 85.0 <= al <= be <= ga <= 92.0:
            lat = 'cubic'
    elif a == b or abs((a-b)) <= 5.0:
        cell_in_list[1] = cell_in_list[0]
        if 110.0 <= ga <= 130.0:
            lat = 'hexagonal'
            ua = 'c'
            cell_in_list[5] = 120.0

        elif ga == 90.0 and 88.0 <= al <= 92.0 and 88.0 <= be <= 92.0:
            lat = 'tetragonal'
            ua = 'c'
            cell_in_list[3] = cell_in_list[4] = cell_in_list[5] = 90.0
    elif b == c or abs((b-c)) <= 5.0:
        cell_in_list[2] = cell_in_list[1]
        if 110.0 <= al <= 130.0:
            lat = 'hexagonal'
            ua = 'a'
            cell_in_list[3] = 120.0

        elif al == 90.0 and 88.0 <= ga <= 92.0 and 88.0 <= be <= 92.0:
            lat = 'tetragonal'
            ua = 'a'
            cell_in_list[3] = cell_in_list[4] = cell_in_list[5] = 90.0
    elif a == c or abs((a-c)) <= 5.0:
        cell_in_list[2] = cell_in_list[0]
        if 110.0 <= be <= 130.0:
            lat = 'hexagonal'
            ua = 'b'
            cell_in_list[4] = 120.0
        elif be == 90.0 and 88.0 <= al <= 92.0 and 88.0 <= ga <= 92.0:
            lat = 'tetragonal'
            ua = 'b'
            cell_in_list[3] = cell_in_list[4] = cell_in_list[5] = 90.0

    elif abs((a-b)) >= 10.0 and abs((b-c)) >= 10.0 and abs((c-a)) >= 10.0:
        if 88.0 <= al <= 92.0 and 88.0 <= be <= 92.0 and 88.0 <= ga <= 92.0:
            lat = 'orthorhombic'
        elif al != 90.0 and be == ga == 90.0:
            lat = 'monoclinic'
            ua = 'a'
        elif be != 90.0 and al == ga == 90.0:
            lat = 'monoclinic'
            ua = 'b'
        elif ga != 90.0 and al == be == 90.0:
            lat = 'monoclinic'
            ua = 'c'
        else:
            lat = 'triclinic'

    return lat, ua, cell_in_list


def assign_point_group(lt, cen, ua):
    pg = '1'
    sg = 'P1'

    if lt == 'triclinic' and cen == 'P':
        pg = '1'
        sg = 'P1'

    elif lt == 'monoclinic' and (cen == 'P' or cen == 'C'):

        if ua == 'a':
            pg = '2/m_uaa'
            sg = cen + '211'
        elif ua == 'b':
            pg = '2/m_uab'
            sg = cen + '121'
        else:
            pg = '2/m_uac'
            sg = cen + '112'

    elif lt == 'orthorhombic':
        pg = 'mmm'
        sg = cen + '222'
    elif lt == 'tetragonal' and cen == 'P':
        sg = cen + '422'
        if ua == '*' or ua == '?':
            pg = '4/m'
        elif ua == 'a':
            pg = '4/mmm_uaa'
        elif ua == 'b':
            pg = '4/mmm_uab'
        else:
            pg = '4/mmm_uac'

    elif lt == 'cubic':
        pg = 'm-3'
        sg = cen + '432'

    elif lt == 'rhombohedral':
        sg = cen + '32'
        if cen == 'R':
            pg = '32_R'
        elif cen == 'H':
            pg = '321_H'
    elif lt == 'hexagonal' and cen == 'P':
        sg = cen + '622'
        if ua == 'a':
            pg = '6/m_uaa'
        elif ua == 'b':
            pg = '6/m_uab'
        else:
            pg = '6/m_uac'
    elif lt == 'hexagonal' and cen == 'H':
        pg = '321_H'
        sg = 'R32'
    else:
        print("lattice or centering unknown types")

    return pg, sg, space_group[sg][0]


if __name__ == '__main__':
    print(lattice_from_cell([78.5, 79.6, 137.0, 92.0, 88.0, 90.0]))
