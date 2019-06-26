
__authors__ = ["S. Basu"]
__license__ = "MIT"
__date__ = "20/06/2019"

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy
from numpy.distutils.misc_util import Configuration

'''
cython build can be done with numpy configuration option. Its elegant but generates build and lib folders
which is bit of over-do for one .pyx script. In future, if we expand for many C++ wrappers, then we should 
deploy advanced configuration. For now, a simple distutils.core.setup will suffice our purpose.
'''


def configuration(parent_package='', top_path=None):
    config = Configuration('ext', parent_package, top_path)

    config.add_extension(
        name="fast_array_ext",
        sources=["pyx/fast_array_ext.c"],
        include_dirs=[numpy.get_include()],
        language='c')
    return config


if __name__ == "__main__":

    # from numpy.distutils.core import setup

    # setup(configuration=configuration)
    '''
    Usage: python setup.py build_ext --inplace
    
    Mac users, note: numpy/arrayobject.h or other numpy header paths may not get parsed to GCC compiler. 
    A specific Mac OSX error. This works fine on Linux platform. 
    Current work-around for Mac-user:
    export $CFLAGS="/my/path/to/numpy/include:$CFLAGS"
    run this export command before running setup.py on the same terminal window, it will work.. 
    '''

    extensions = [
        Extension("fast_array_ext", ["pyx/fast_array_ext.pyx"])]
    setup(
        name="fast_array_ext",
        ext_modules=cythonize(extensions, include_path=[numpy.get_include()]),
    )
