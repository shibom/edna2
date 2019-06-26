"""
Created on: 2019.02.04
Shibom Basu
"""
from __future__ import division, print_function
import os
import re


class GeomLoader(object):
  def __init__(self, geomfname):
      self._fname = geomfname
      if os.path.exists(self._fname):
          self.geom = open(self._fname, 'r')
      else:
          print("geometry file does not exist")
          return
      self.re_dict = dict(photon_energy=re.compile(r'photon_energy\s=\s(?P<photon_energy>[1-9\.\+])\n'),
                            clen=re.compile(r'clen\s=\s(?P<clen>[1-9\.\+\-])\n'),
                            coffset=re.compile(r'coffset\s=\s(?P<coffset>[1-9\.\-\+])\n'),
                            adu_per_eV=re.compile(r'adu_per_eV\s=\s(?P<adu_per_eV>[1-9\.\+])\n'))
      self.params = dict()
      self.keys_per_panel = ['min_fs','max_fs', 'min_ss', 'max_ss', 'corner_x', 'corner_y','fs', 'ss']

      for k in self.keys_per_panel:
          self.params[k] = dict()

      return

  def close(self):
      self.geom.close()
      return

  def beam_param(self): # not working.. re pattern issue?
      for lines in self.geom:
          for k, pat in self.re_dict.items():
              match = pat.search(lines)
              if match:
                  if k == 'photon_energy':
                      self.params[k] = match.group('photon_energy')
                  if k == 'clen':
                      self.params[k] = match.group('clen')
                  if k == 'coffset':
                      self.params[k] = match.group('coffset')
                  if k == 'adu_per_eV':
                      self.params[k] = match.group('adu_per_eV')
      return
  def read(self):
      var = ''
      for lines in self.geom:
          fields = lines.split('=')
          if ';' not in fields[0] and '/' in fields[0]:
              var = fields[0].strip().split('/')
              for k in self.keys_per_panel:
                  if k in var:
                     self.params[k][var[0]] = fields[1].strip('\n')


          elif ';' not in fields[0] and '/' not in fields[0]:
              try:
                 self.params[fields[0]] = fields[1].strip('\n')
              except IndexError:
                 pass
          else:
              pass
      return

def main():
    from Image import CBFreader
    import matplotlib.pyplot as plt

    cbf = CBFreader('../examples/mesh-insu_2_0_1143.cbf')
    cbf.read_cbfdata()
    gg = GeomLoader('../examples/pilatus2m.geom')
    #gg.beam_param()
    gg.read()
    gg.close()

    return



if __name__ == '__main__':
    main()
