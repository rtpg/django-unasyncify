.. _usage-tips:

Usage Tips
==========

Here's an unordered set of tips on how to use ``django-unasyncify`` safely.


.. _naming-scheme:

Use the async/sync variant naming scheme
----------------------------------------

When writing code, follow the following template for naming your functions that have sync and async variants

+-----+-----------------+-------------------+--------------------+
|     |public functions | private functions | test functions     |
+-----+-----------------+-------------------+--------------------+
|sync |``foo``          |``_foo``           |``test_thing``      |
+-----+-----------------+-------------------+--------------------+
|async|``afoo``         |``_afoo``          |``test_async_thing``|
+-----+-----------------+-------------------+--------------------+


When function names are being unsyncified, three patterns being looked for are, based off the above naming pattern:

- the names start with ``test_async`` (so the sync method should start with ``test_``)
- the name starts with ``_a`` (so the sync method should start with ``_``)
- the name starts with ``a`` (so the sync method should just remove that ``a``)


.. _is-async-usage:
Conditionally Include Code With ``IS_ASYNC``
--------------------------------------------

``IS_ASYNC`` is a constant provided by the unasync helpers. It is ``True``, but when we run unasyncification we replace ``IS_ASYNC`` to ``False``!

You can use this to do conditional behavior::

  @generate_unasynced
  async def arun_calculation(data):
    result = {"used_async": IS_ASYNC}
    if IS_ASYNC:
      result["data"] = await third_party_lib.async_calc(data)
    else:
      result["data"] = another_third_party_lib.sync_calc(data)
    return result

The above snippet will generate the following sync variant::

    @from_codegen
    def run_calculation(data):
        result = {"used_async": False}
        result["data"] = another_third_party_lib.sync_calc(data)
        return result

A couple things to note in the above example:

- ``IS_ASYNC`` was replaced by ``False``
- the ``if IS_ASYNC`` branch in its entirety is simplified to only have the ``else`` case.

This can be a straightforward way to offer synced-ness branching, though it does mean that your coverage reports will not look great.

If coverage is a bigger issue here, then creating wrapper functions and calling that will also work::


    def calculate(data):
        return another_third_party_lib.sync_calc(data)

    async def acalculate(data):
        return await third_party_lib.async_calc(data)

    @generate_unasynced
    async def arun_calculation(data):
        result = {"used_async": IS_ASYNC}
        result["data"] = await acalculate(data)
        return result

Here we have defined two functions that follow the sync/async variant patterns. Not here how I didn't need to actually use the decorators, the naming convention is what is used.

With this our generated sync variant will look like::

    @from_codegen
    def run_calculation(data):
        result = {"used_async": False}
        result["data"] = calculate(data)
        return result
