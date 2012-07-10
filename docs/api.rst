=================
API Documentation
=================

:mod:`queuey_py.client`
-----------------------

Contains a :term:`Queuey` connection helper.

The connection automatically handles retries on connection timeouts and fall
back to alternate :term:`Queuey` servers on SSL or connection errors. If
multiple servers are provided, one will be selected at random, though
`localhost` or a `127.0.0.1` / `::1` server will be preferred. Currently fall
back to secondary servers happens exactly once per server, after which it is
considered inactive. You have to restart the process to reset the inactive
status.

The connection uses a connection pool as provided by the
`requests <http://docs.python-requests.org>`_ library and turns on keep alive
connections. SSL is supported by default and certificates will be checked for
validity. If you want to use a private certificate, you can configure one
via providing the full path to it in the `REQUESTS_CA_BUNDLE` environment
variable.

.. automodule:: queuey_py.client

Exceptions
~~~~~~~~~~

.. autoexception:: HTTPError

Classes
~~~~~~~

.. autoclass:: Client

    .. automethod:: connect()
    .. automethod:: get(url='', params=None)
    .. automethod:: post(url='', params=None, data='')
    .. automethod:: delete(url='', params=None)
    .. automethod:: create_queue(partitions=1, queue_name=None)
    .. automethod:: messages(queue_name, partition=1, since=None, limit=100, order='ascending')

Functions
~~~~~~~~~

.. py:decorator:: retry

   On connection timeouts, retry the action.

.. py:decorator:: fallback

   On connection errors, fall back to alternate servers.
