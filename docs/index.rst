.. django-unasyncify documentation master file, created by
   sphinx-quickstart on Fri Jan 31 16:05:27 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

django-unasyncify documentation
===============================

``django-unasyncify`` is a project to help maintain sync and async implementations of APIs, focused on code relying on Django's asynchronous API design.

It uses code generation to create separate sets of functions, that have no runtime dependencies on ``django-unasyncify`` nor do they rely on any wrappers to manage functionality, meaning there are no runtime costs to using this tool.

.. note::

   This project is still exploring the design space for this problem. If you encounter any difficulties using this tool, please reach out and share feedback! The hope is that this tool should work well out of the box for projects needing to manage interactions with Django's async API layer.

It does this by relying on `libCST <https://libcst.readthedocs.io/en/latest/index.html>`_'s code modification tooling.

What It Does
------------

``django-unasyncify`` generates a synchronous variant of a method based on an asynchronous implementation.

For example, consider the following snippet::

    @generate_unasynced
    async def acreate_model_instance(self, data):
        """
        Return a new instance of the session model object, which
        represents the current session state.
        Intended to be used for saving the
        session data to the database.
        """
        return self.model(
            session_key=await self._aget_or_create_session_key(),
            session_data=self.encode(data),
            expire_date=await self.aget_expiry_date(),
        )

The above method is annotated with ``@generate_unasynced``, indicating we want a synchronous variant for this method.

After running ``django-unasyncify``, the file containing this method is modified to become the following::

    @from_codegen
    def create_model_instance(self, data):
        """
        Return a new instance of the session model object, which
        represents the current session state.
        Intended to be used for saving the
        session data to the database.
        """
        return self.model(
            session_key=self._get_or_create_session_key(),
            session_data=self.encode(data),
            expire_date=self.get_expiry_date(),
        )

    @generate_unasynced
    async def acreate_model_instance(self, data):
        """
        Return a new instance of the session model object, which
        represents the current session state.
        Intended to be used for saving the
        session data to the database.
        """
        return self.model(
            session_key=await self._aget_or_create_session_key(),
            session_data=self.encode(data),
            expire_date=await self.aget_expiry_date(),
        )

From the async implementation, a synchronous variant has been generated. It maintains comments and layout, but rewrites ``await`` expressions to no longer be ``await``. It is able to do this for Django-related code by relying on the naming conventions for sync and async variants of Django APIs.

The synchronous variant has also been annotated with ``@from_codegen``. This decorator serves both as documentation and a way for ``django-unasyncify`` to be able to run idempotently.

The rough naming convention for a Django API is that the asynchronous variant for a synchronous API is gotten by adding an ``a`` to the name. ``get`` becomes ``aget``, ``save`` becomes ``asave``, etc.

.. note::

   - Asynchronous methods have names starting with ``a``.
   - Their synchronous variant is found by removing the ``a``.
   - Asynchronous private methods have names starting with ``_a``.
   - Their synchronous variant is found by replacing ``_a`` with ``_``.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   configuration
   usage_tips
   unasync_helpers
   transformation_rules
   why_not_sync_to_async
