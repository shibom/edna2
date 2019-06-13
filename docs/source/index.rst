.. EDNA2 documentation master file, created by
   sphinx-quickstart on Thu Jun 13 09:24:41 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

EDNA2 version |version|
=======================

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

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   install
   tutorials
   modules/index.rst
