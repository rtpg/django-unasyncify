django-unasyncify
=================

``django-unasyncify`` is a project to help maintain sync and async implementations of APIs, focused on code relying on Django's asynchronous API design.

It uses code generation to create separate sets of functions, that have no runtime dependencies on ``django-unasyncify`` nor do they rely on any wrappers to manage functionality, meaning there are no runtime costs to using this tool.


It helps you to transform code like::

  def asave_instance(qs):
    await (await qs.aget()).asave()

into::

  def save_instance(qs):
    qs.get().save()

Please check out the `documentation <https://django-unasyncify.readthedocs.io/en/latest/>`_  for more details on how this project works and tips on how to use it.
