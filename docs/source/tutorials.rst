EDNA2 tutorials and examples
============================

Setup for tutorials:

.. code-block:: bash

    % mkdir edna2_tests
    % cd edna2_tests
    % git clone https://github.com/olofsvensson/edna2
    % export PYTHONPATH=`pwd`/edna2/edna2
    % export PATH=`pwd`/edna2/bin:$PATH

Check that the edna2.py command works:

.. code-block:: bash

    % edna2.py
    usage: edna2.py [-h] [--inData INDATA] [--inDataFile INDATAFILE]
                    [--outDataFile OUTDATAFILE] [--debug] [--warning] [--error]
                    taskName
    edna2.py: error: the following arguments are required: taskName


Hello world!
------------

This is 'Hello world!' in EDNA2:

.. code-block:: python

    from edna2.tasks.AbstractTask import AbstractTask


    class HelloWorldTask(AbstractTask):
        """
        Example EDNA2 task
        """

        def run(self, inData):
            name = inData.get('name', None)
            if name is None:
                helloWorld = 'Hello world!'
            else:
                helloWorld = 'Hello world {0}!'.format(name)
            outData = {'results': helloWorld}
            return outData

This code is part of the source code and can be found in
edna2/edna2/examples/HelloWorldTask.py.

One can run this task from the command line using the 'edna2.py' command:

.. code-block:: bash

    % edna2.py HelloWorldTask
    {
        "results": "Hello world!"
    }

We can now also provide some indata:

.. code-block:: bash

    % edna2.py --inData '{"name": "Someone"}' HelloWorldTask
    {
        "results": "Hello world Someone!"
    }
