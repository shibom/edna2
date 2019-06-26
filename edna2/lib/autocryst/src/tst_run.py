from __future__ import print_function
import os
import sys
import json
import src.saveDozor as sd
import src.crystfel_utils
import logging

logger = logging.getLogger('autoCryst')


def run(jsonfile):
    dd = sd.Dozor(jsonfile)
    try:
        dd.extract_olof_json(dd.jshandle['olof_json'])
    except (KeyError, IOError):
        logger.info("MSG:{}".format("Olof json file was not provided"))
        if dd.jshandle['dozorfolder'] is None:
            dd.run_dozor()
        elif os.path.exists(dd.jshandle['dozorfolder']):
            dd.prep_spot()
    if dd.success:
        with open('headers.json', 'w') as jhead:
            json.dump(dd.cbfheader, jhead, sort_keys=True, indent=2)
        if dd.stacklength <= 100:
            dd.create_stack()
        else:
            dd.mp_stack()
        try:
            args = dict()
            args['peak_search'] = 'cxi'
            args['peak_info'] = '/data/peakinfo'
            args['highres'] = '4.0'
            cwd = os.getcwd()
            cryst = src.crystfel_utils.Utils(cwd, 'dozor_*', 'cxi', **args)
            cryst.run_indexing()
            cryst.check_oarstat()
            cryst.report_stats()
            # status, results = crystfel_utils.__run__(cwd, 'dozor_2', 'cxi', **args)
            if cryst.status:
                logger.info("MeshScan-results:{}".format(cryst.results))
            else:
                logger.info("Error:{}".format("crystfel pipeline has errors"))
                cryst.status = False
        except Exception as err:
            logger.info("Error-crystfel:{}".format(err))
            dd.success = False

    else:
        logger.info("Dozor did not run properly")
        dd.success = False
    return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%y-%m-%d %H:%M',
                        filename='autoCryst.log',
                        filemode='a+')
    run(sys.argv[1])
