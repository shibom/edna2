"""
Created on 11-Jan-2019
Author: S. Basu
"""
from __future__ import division, print_function

"""
space_group = {
'1':{'lattice_type':'triclinic', 'centering':'P', 'group_name':'P1'},
'4':{'lattice_type': 'monoclinic', 'centering':'P','group_name':'P211'},
'5':{'lattice_type': 'monoclinic', 'centering':'C', 'group_name':'C112'},
'16':{'lattice_type': 'orthorhombic', 'centering':'P','group_name': 'P222'},
'21':{'lattice_type': 'orthorhombic', 'centering':'C','group_name': 'C222'},
'23':{'lattice_type': 'orthorhombic', 'centering':'I', 'group_name':'I222'},
'75':{'lattice_type': 'tetragonal', 'centering':'P', 'group_name':'P4'},
'79':{'lattice_type': 'tetragonal', 'centering':'I','group_name': 'I4'},
'89':{'lattice_type': 'tetragonal', 'centering':'P','group_name': 'P4222'},
'92':{'lattice_type': 'tetragonal', 'centering':'P','group_name': 'P41212'},
'95':{'lattice_type': 'tetragonal', 'centering':'P','group_name': 'P43212'},
'143':{'lattice_type': 'trigonal', 'centering':'P','group_name': 'P3'},
'155':{'lattice_type': 'rhombohedral', 'centering':'H','group_name': 'H32'},
'168':{'lattice_type': 'hexagonal', 'centering':'P','group_name': 'P622'},
'195':{'lattice_type': 'cubic', 'centering':'P','group_name': 'P23'},
'196':{'lattice_type': 'cubic', 'centering':'F','group_name': 'F23'},
'197':{'lattice_type': 'cubic', 'centering':'I','group_name': 'I23'}
}

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
        sg = 'H32'
    else:
        print("lattice or centering unknown types")

    return pg, sg


if __name__ == '__main__':
    print(lattice_from_cell([78.5, 79.6, 137.0, 92.0, 88.0, 90.0]))
