"""
Created on 27-March-2019
Author: S. Basu
"""
import os
import sys

from workflow_lib import ispyb
from workflow_lib import common
from workflow_lib import collect
from workflow_lib import edna_mxv1
from workflow_lib import collect_and_ispyb
from workflow_lib import workflow_logging, path
from autoCryst import crystfel_utils

def run(beamline, workflowParameters, directory, meshPositionFile, run_number, expTypePrefix, workflow_working_dir,
        prefix, suffix, workflow_id, grid_info, workflow_title, workflow_type,
        data_threshold, data_collection_max_positions, radius, list_node_id=None, firstImagePath=None,
        pyarch_html_dir=None, diffractionSignalDetection="Dozor", resultMeshPath=None, token=None, **kwargs):

    crystfel_result = {}
    try:
        sys.path.insert(0, '/opt/pxsoft/ccp4/v7.0/linux-x86_64/ccp4-7.0/lib/py2/cctbx/lib')
        # sys.path.insert(1, '/usr/local/BES/id30a2/workflow/autoCryst/src')
        logger = workflow_logging.getLogger(beamline)
        logger.info('PYTHONPATH:{}'.format(sys.path))
        # from autoCryst import crystfel_utils
        args = {}
        args['beamline'] = beamline
        # args['indexing_method'] = 'xgandalf'
        # suffix = 'cbf' or 'h5'
        prefix = expTypePrefix + prefix
        status, crystfel_result = crystfel_utils.__run__(directory, prefix, suffix, **args)
        if status:
           logger.info('crystFEL:{}'.format(crystfel_result))
        else:
           logger.info('crystFEL:{}'.format('crystfel pipeline has errors'))

    except Exception as err:
        common.logStackTrace(workflowParameters)
        raise err

    return crystfel_result

def check():
    try:
        sys.path.insert(0, '/opt/pxsoft/ccp4/v7.0/linux-x86_64/ccp4-7.0/lib/py2/cctbx/lib')
        sys.path.insert(1, '/usr/local/BES/id30a2/workflow/autoCryst/src')
        print 'PYTHONPATH:{}'.format(sys.path)
        import crystfel_utils
    except Exception as err:
        raise err

if __name__ == '__main__':
   check()
