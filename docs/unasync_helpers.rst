
.. _unasync-helpers:

Unasync Helpers
===============

``django-unasyncify`` uses a handful of decorators and constants to guide the unasyncification process.

In order to avoid a runtime dependency on ``django-unasyncify``, the tool will create a file based on :confval:`unasync_helpers_path` with defeintions for these decorators and constants.

.. attention::
   You do not need to import these names manually. During the unasyncification process, imports for these names will be automatically added.

.. caution::
   ``django-unasyncify`` looks for these specific names, as its transformations are purely syntactic.

   Something like the following will fail, as we are looking for ``@generate_unasynced`` specifically!::

       some_other_name = generate_unasynced

       # this won't be picked up!
       @some_other_name
       async def aoperation():
            ...


@generate_unasynced
-------------------

A marker for functions we want to unasyncify. This can be called with or without parentheses, as a decorator.

Usage::

  @generate_unasynced
  async def aoperation():
    ...

  @generate_unaynced()
  async def aoperation2():
    ...


IS_ASYNC
--------

``IS_ASYNC`` is a constant that evaluates to ``True``. During unasyncification, ``IS_ASYNC``  gets mapped to ``False``.

This is useful for conditional branching based on whether you're in the async or sync variant of a function (see :ref:`is-async-usage`)


@from_codegen
-------------

A marker used to indicate that ``django-unasyncify`` created this function. Code marked by this decorator gets removed during the transformation process (see :ref:`transformation-rules`)

It is unlikely that you ever want to use this directly.
