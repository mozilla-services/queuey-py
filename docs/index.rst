===========================================
queuey-py: Python client library for Queuey
===========================================

This is a Python client library used for interacting with messages from a
Mozilla Services message queue. More soon, in the meantime, you can read the
`spec <https://wiki.mozilla.org/Services/Sagrada/Queuey>`_ on the Mozilla
wiki or look at the message queue implementation called
`Queuey <http://queuey.readthedocs.org>`_ itself.

Quick intro
===========

Connect to Queuey, create a queue and post a message:

.. code-block:: python

    from queuey_py import Client

    # Specify application key and URL
    client = Client('67e8107559e34fa48f91a746e775a751',
                    'http://127.0.0.1:5001/v1/queuey/)
    client.connect()
    name = client.create_queue()
    client.post(name, data='Hello world')

Contents
========

.. toctree::
   :maxdepth: 2

   api
   development
   changelog

Index and Glossary
==================

* :ref:`glossary`
* :ref:`genindex`
* :ref:`search`

.. toctree::
   :hidden:

   glossary
