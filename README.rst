EDNA2
=========

The EDNA2 project is a complete rewrite of the EDNA project.
For more info about the EDNA project see http://www.edna-site.org.
The version of ENDA used at the ESRF is: https://github.com/olofsvensson/edna-mx.

The EDNA2 project tries to keep the 'spirit' of the EDNA project and at the
same time make the framework lightweight. These are the main differences with the EDNA project:

- Not compatible with python 2.7 - requires python 3
- No data modelling framework
- Data persisted as json instead of XML
- Tasks instead of plugins
- Logging based on Python logging
- Python unit tests

These are the main features retained in the EDNA2 project:

- Asynchronous execution of tasks
- Task configuration based on sites
- Hierarchical working directory structure handled by the framework.

Wherever possible a link is provided in the EDNA2 source code to the
corresponding EDNA code.

Installation
------------

The EDNA2 project provides a setup.py file for installation.

Documentation
-------------

The documentation can be found at https://edna2.readthedocs.io.

Testing and code review
-----------------------

- Travis CI status: |Travis Status|
- Automatic code quality check: https://app.codacy.com/project/olofsvensson/edna2/dashboard

Contribute
----------

- Issue Tracker: https://github.com/olofsvensson/edna2/issues
- Source Code: https://github.com/olofsvensson/edna2

Support
-------

If you are having issues, please let us know via the issue tracker.

License
-------

The source code of *edna2* is licensed under the MIT license.
See the `LICENSE <https://github.com/olofsvensson/edna2/blob/master/LICENSE>`_
and `copyright <https://github.com/olofsvensson/edna2/blob/master/copyright>`_
files for details.

.. |Travis Status| image:: https://api.travis-ci.org/olofsvensson/edna2.svg?branch=master
   :target: https://travis-ci.org/olofsvensson/edna2?branch=master