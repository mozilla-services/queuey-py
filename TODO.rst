TODO
====

- make ujson optional dependency and use any of simplejson, json or ujson
- implement smarter fallback on Queuey connections, not just try-once
- add nicer error handling, wrap non-2xx responses and JSON parsing problems
  in exceptions and print out response text as part of the exception /
  traceback

future
------

- provide more semantic API's similar to create_queue / messages. For example
  `post_message`, `post_messages`, `get_message`, `update_message` etc.
