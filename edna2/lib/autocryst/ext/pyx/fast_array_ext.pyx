
__authors__ = ["S. Basu"]
__license__ = "MIT"
__date__ = "19/06/2019"


import cython
from libc.stdlib cimport malloc, free
cimport numpy as np
import numpy as np
import fabio


DTYPE = np.int32

ctypedef np.int32_t DTYPE_t

@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def stack3d(np.ndarray cbf_lst, int dim1, int dim2):
    '''
    cython array does not have extra advantage. It fails to allocate
    array with 1000 images, same as c++ buffer. so let's keep numpy
    allocation. we can <free> buf pointer but not o_buf. One cannot copy
    the data to numpy and release the o_buf from this function. Copying
    will only pass the pointer. But it will not deallocate the memory.
    Its python which only passes pointers.
    '''
    cdef:
        int stacklength = cbf_lst.shape[0]
        int size = dim1 * dim2
        DTYPE_t * buf = <DTYPE_t*>malloc(sizeof(int) * size)
        DTYPE_t * o_buf = <DTYPE_t*>malloc(sizeof(int) * (stacklength*size))
        DTYPE_t[:] in_ary = <DTYPE_t[:size]>buf
        # DTYPE_t[:, :] in_ary = cvarray((dim1, dim2), sizeof(int), 'i', allocate_buffer=True)
        
        int i = 0, j = 0, k = 0
        DTYPE_t[:] out_ary = <DTYPE_t[:(stacklength*size)]>o_buf
        # DTYPE_t[:, :, :] out_ary = cvarray((stacklength, dim1, dim2), sizeof(int), 'i')

    for i in range(stacklength):
        img = fabio.open(cbf_lst[i])
        in_ary = np.ascontiguousarray(img.data.ravel(), dtype=DTYPE)
        assert in_ary.size == size            
        out_ary[i*size:(i+1)*size] = in_ary
        
    free(buf)
    return np.array(out_ary)

