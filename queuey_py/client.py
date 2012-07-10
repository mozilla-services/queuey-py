# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import wraps
from random import choice
from urlparse import urljoin
from urlparse import urlsplit

from requests import exceptions
from requests import session
from requests.exceptions import ConnectionError
from requests.exceptions import SSLError
from requests.exceptions import Timeout
import ujson
from ujson import decode as ujson_decode


def retry(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        for n in range(self.retries):
            try:
                return func(self, *args, **kwargs)
            except Timeout:
                pass
        # raise timeout after all
        raise
    return wrapped


def fallback(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (SSLError, ConnectionError):
            if self.fallback_urls:
                self.failed_urls.append(self.app_url)
                self.app_url = self.fallback_urls.pop()
                return func(self, *args, **kwargs)
            # raise connection error after all
            raise
    return wrapped


class HTTPError(exceptions.HTTPError):
    """An HTTP error occurred.

    Provides two arguments. First the response status code and second the
    full response object.
    """


class Client(object):
    """Represents a connection to a :term:`Queuey` server or cluster.

    :param app_key: The applications key used for authorization
    :type app_key: str
    :param connection: Connection information for the Queuey server.
        Either a single full URL to the Queuey app or multiple comma
        separated URLs.
    :type connection: str
    :param retries: Number of retries on connection timeouts, defaults to 3.
    :type retries: int
    :param timeout: Connection timeout in seconds, defaults to 5.0.
    :type timeout: float
    """

    def __init__(self, app_key,
                 connection=u'https://127.0.0.1:5001/v1/queuey/',
                 retries=3, timeout=5.0):
        self.app_key = app_key
        self.retries = retries
        self.timeout = timeout
        self.failed_urls = []
        headers = {u'Authorization': u'Application %s' % app_key}
        # Setting pool_maxsize to 1 ensures we re-use the same connection.
        # requests/urllib3 will always create maxsize connections and then
        # cycle through them one after the other
        self.session = session(headers=headers, timeout=self.timeout,
            config={u'pool_maxsize': 1, u'keep_alive': True}, prefetch=True)
        self._configure_connection(connection)

    def _configure_connection(self, connection):
        self.connection = [c.strip() for c in connection.split(',')]
        if len(self.connection) == 1:
            self.app_url = self.connection[0]
            self.fallback_urls = []
        else:
            # choose random server, but prefer local ones
            local = []
            remote = []
            for c in self.connection:
                netloc = urlsplit(c).netloc
                if netloc.startswith((u'127.0.0.', u'localhost', u'::1')):
                    local.append(c)
                else:
                    remote.append(c)
            all_servers = preferred = local + remote
            if len(local) > 0:
                preferred = local
            self.app_url = choice(preferred)
            all_servers.remove(self.app_url)
            self.fallback_urls = all_servers

    @fallback
    @retry
    def connect(self):
        """Establish a connection to the :term:`Queuey` heartbeat url, retry
        up to :py:attr:`retries` times on connection timeout.

        :raises: :py:exc:`requests.exceptions.ConnectionError`
        """
        parts = urlsplit(self.app_url)
        url = parts.scheme + u'://' + parts.netloc + u'/__heartbeat__'
        return self.session.head(url)

    @fallback
    @retry
    def get(self, url='', params=None):
        """Perform a GET request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL to get, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        return self.session.get(url,
            params=params, timeout=self.timeout)

    @fallback
    @retry
    def post(self, url='', params=None, data='', headers=None):
        """Perform a POST request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL to post to, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :param data: The body payload, either a string for a single message
            or a list of strings for posting multiple messages or a dict
            for form encoded values.
        :type data: str
        :param headers: Additional request headers.
        :type headers: dict
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        if isinstance(data, list):
            # support message batches
            messages = []
            for d in data:
                messages.append({u'body': d, u'ttl': 259200})  # three days
            data = ujson.encode({u'messages': messages})
            headers = {u'content-type': u'application/json'}
        return self.session.post(url, headers=headers,
            params=params, timeout=self.timeout, data=data)

    @fallback
    @retry
    def put(self, url='', params=None, data='', headers=None):
        """Perform a PUT request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL for put, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :param data: The body payload as a single message string.
        :type data: str
        :param headers: Additional request headers.
        :type headers: dict
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        return self.session.put(url, headers=headers,
            params=params, timeout=self.timeout, data=data)

    @fallback
    @retry
    def delete(self, url='', params=None):
        """Perform a DELETE request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL to post to, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        return self.session.delete(url,
            params=params, timeout=self.timeout)

    def create_queue(self, partitions=1, queue_name=None):
        """Create a new queue and return its name.

        :param partitions: Number of partitions to create, defaults to 1.
        :type partitions: int
        :param queue_name: Optional explicit queue name, otherwise Queuey
            will auto-generate one.
        :type queue_name: unicode
        :raises: :py:exc:`queuey_py.client.HTTPError`
        :rtype: unicode
        """
        data = {u'partitions': partitions}
        if queue_name is not None:
            data[u'queue_name'] = queue_name
        response = self.post(data=data)
        if response.ok:
            return ujson.decode(response.text)[u'queue_name']
        # failure
        raise HTTPError(response.status_code, response)

    def messages(self, queue_name, partition=1, since=None, limit=100,
                  order='ascending'):
        """Returns messages for a queue, by default from oldest to newest.

        :param queue_name: Queue name
        :type queue_name: unicode
        :param partition: Partition number, defaults to 1.
        :type partition: int
        :param since: Only return messages after (not including) a given
            message id, defaults to no restriction.
        :type since: str
        :param limit: Only return N number of messages, defaults to 100.
        :type limit: int
        :param order: 'descending' or 'ascending', defaults to ascending
        :type order: str
        :raises: :py:exc:`queuey_py.client.HTTPError`
        :rtype: list
        """
        params = {
            u'limit': limit,
            u'order': order,
            u'partitions': partition,
        }
        if since:
            params[u'since'] = since
        response = self.get(queue_name, params=params)
        if response.ok:
            messages = ujson_decode(response.text)[u'messages']
            # filter out exact timestamp matches
            return [m for m in messages if m[u'message_id'] != since]
        # failure
        raise HTTPError(response.status_code, response)
