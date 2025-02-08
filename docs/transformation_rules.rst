.. _transformation-rules:

Transformation Rules
====================

The main transformation ``django-unasyncify`` applies is via a ``libCST`` Codemod, that traverses the Python code (much like an AST).

This tries to document the transformations that occur. Generally speaking ``django-unasyncify`` does the "right" thing when encountering async syntax, but this document might clarify why you're not seeing the transformation you expect.

.. note::

   If you are seeing behavior that you are not expecting and this document does not help, please report the issue. It could be we are simply missing an odd edge case.

@from_codegen
-------------

``django-unasyncify`` looks for any method with a decoartor called ``@from_codegen``, and removes it from the code. This enables the code generation from ``generate_unasynced`` to be idempotent.


@generate_unasynced
-------------------

A method with the ``@generate_unasynced`` decorator on it will do the following:

- Copy the method that it is decorating
- Apply the ``UnasyncifyMethod`` transformation to that copy
- Rename the copied method, generating a "sync variant" name to a method
  - A method name starting with ``a`` gets the leading ``a`` removed (``aget -> get``)
  - A method name stasting with ``_a`` replaces the ``_a`` with ``_`` (``_amethod -> _method``)
- Add the ``@from_codegen`` decorator to that copy
- Insert the copy *above* the original method


UnasyncifyMethod
----------------

``UnasyncifyMethod`` transforms async code into synchronous code.

Here is a list of transformation examples that capture what this does. For exact details, looking at the code for ``UnasyncifyMethod`` is recommended.

Async ``with`` statements are transformed::

    async with expr:
      body

    # Becomes

    with expr:
      body

Async ``for`` statements are transformed::

    async for for_loop_expr:
      body

    # Becomes

    for for_loop_expr:
      body

Async ``for`` comprehensions are transformed::

  expr async for elt in container

  # Becomes

  expr for elt in container

``If`` statements have tricky handling. If the test condition is exactly ``IS_ASYNC``, we try to remove the associated branch (because we are unasyncifying, ``IS_ASYNC`` branches should always be ``False``).

Thus::

  if IS_ASYNC:
    body1
  else:
    body2

  # Becomes
  body2

But also::

  if IS_ASYNC:
    body1
  elif other_condition:
    body2
  else:
    body3

  # Becomes
  if other_condition:
    body2
  else:
    body3



.. _handling-function-calls:

Handling Function Calls
^^^^^^^^^^^^^^^^^^^^^^^

To understand how function calls are handled, first we need to cover await depth.

We track how many "``await``'s deeps" we are while traversing the Python code::

  do_something( await (foo.bar(await baz)) )


In the above, the await depth of ``do_something`` is 0, the await depth of ``foo.bar``  (or ``foo``) is 1, and the await depth of ``baz`` is 2.

Tracking the await depth lets us know if some code we are transforming is an await node or not.


When looking at a function call, we consider many things.

If we're at some code at an await depth of 0, then we do not transform the function call itself::

  afoo(1, 3)

  # Becomes (or rather, remains)

  afoo(1, 3)

But even in this case, arguments will still be traversed, so they might be transformed::

  afoo(1, await self.ado_thing())

  # Becomes

  afoo(1, self.do_thing())


If we are at an await depth above 0, then we attempt to unasyncify the function call. The basic idea here is to determine a function's sync variant's name.

Rough examples of the name transformation:

  - Names starting with ``a`` remove the ``a`` to get the sync variant. ``aget`` becomes ``get``
  - Names starting with ``_a`` remove the ``a`` to get the sync variant. ``_ainternal_op`` becomes ``_internal_op``

Because this is a syntactic transformation, we can't handle things like ``getattr(self, "aget")``. We handle the following cases.

We handle direct calls to a function by name::

  await aget(1, 2)

  # Becomes (aget -> get)

  get(1, 2)


And we handle attribute lookups, by transforming the attribute name.::

  await self.aget()

  # Becomes (aget -> get)

  self.get()

This syntactic transformation happens only on the attribute part of an attribute lookup, not intermediate components.::

  await self.article.aget()

  # Becomes (aget -> get)

  self.article.get()

  # notice how article does not get mangled
  # into rticle!


As a reminder, these transformations happen only during function calls, and only within an ``await``.

Things that don't do what you might want them to do::

  my_method = self.aget
  await my_method()

  # Becomes

  # no attribute rewriting, because this wasn't in a function call
  my_method = self.aget
  # name rewriting happens on "my_method"!
  my_method()

Attribute accesses alone don't get rewritten, which might pose a problem if you have helper sync and async methods::

  result = await self.aconnection.aget()

  # Becomes

  result = self.aconnection.get()

In the above example, it might be that you want ``self.connection.get()`` in your sync variant. In this situation the following can give you that result::

  connection = self.aconnection if IS_ASYNC else self.connection

  result = await connection.aget()

  # Becomes

  connection = self.aconnection if False else self.connection
  result = connection.get()

Bit of an awkward reality but how things are working.

Finally, instances of ``IS_ASYNC`` as names get replaced with ``False``. ``IS_ASYNC`` itself has a value of ``True`` so it lets you do something like the following::

  log.info("Doing thing, async=%s", IS_ASYNC)

  # Becomes

  log.info("Doing thing, async=%s", False)

In the above snippet, the asynchronous variant will receive ``True``, the synchronous variant will receive ``False``.
