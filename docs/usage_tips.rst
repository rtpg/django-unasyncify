Usage Tips
==========

Here's an unordered set of tips you can use when working on this.


Use the async/sync variant naming scheme
----------------------------------------

When writing code, follow the following template for naming your functions that have sync and async variants::

+-----+-----------------+-------------------+--------------------+
|     |public functions | private functions | test functions     |
+-----+-----------------+-------------------+--------------------+
|sync |``foo``          |``_foo``           |``test_thing``      |
+-----+-----------------+-------------------+--------------------+
|async|``afoo``         |``_afoo``          |``test_async_thing``|
+-----+-----------------+-------------------+--------------------+

When code is being unsyncified, three patterns being looked for are:

- the names start with ``test_async`` (so the sync method should start with ``test_``)
- the name starts with ``_a`` (so the sync method should start with ``_``)
- the name starts with ``a`` (so the sync method should just remove that ``a``)

  F
