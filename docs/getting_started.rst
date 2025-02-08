Getting Started
===============

``django-unasyncify`` is meant to be run as a command by developers of a codebase using it. It is not meant to be installed as a dependency of the codebase, and should only be installed as a developer dependency.

1. Install ``django-unasyncify`` as a developer dependency

2. Inside your ``project.toml``, configure ``django-unasyncify``::

     [tool.django_unasyncify]
     # paths that django-unasyncify should visit
     # (relative to pyproject.toml's location)
     paths_to_visit = [
        "src/some/code/folder/",
        "src/some/specific/file.py",
     ]

     # path to a python file that django-unasyncify
     # will manage with unasync helpers
     unasync_helpers_path = "src/pkg/_codegen.py"
     # The import path for the unasync helpers
     # (used in import statements)
     unasync_helpers_import_path = "pkg._codegen"

3. Decorate a method that you want to generate a synchronous variant of. Make sure to follow the Django naming convention of starting your async method with an ``a``!::


     # (django-unasyncify will create this
     #  on first run, using  the unasync_helpers_path
     #  settings)
     from pkg._codegen import generate_unasynced

     ...

     class SessionMgr:
        ...

        @generate_unasynced
        async def aexists(self, session_key):
            return await self.model.objects.filter(
              session_key=session_key
            ).aexists()

4. Once you have labelled your code, you can run ``djang-unasyncify`` at the root of the project (in the same working directory as your ``pyproject.toml``)::

     django-unasyncify

   If you're running it outside of the project root, you can run it by pointing directly to the project directory (where you have your ``pyproject.toml``)::

     django-unasyncify --project /path/to/project

5. After this, your file will have been modified with a sync variant::

    from pkg._codegen import generate_unasynced

    class SessionMgr:
        ...

        @from_codegen
        def exists(self, session_key):
            return self.models.objects.filter(
              session_key=session_key
            ).exists()

        @generate_unasynced
        async def aexists(self, session_key):
            return await self.models.objects.filter(
              session_key=session-key
            ).aexists()

6. Read up on :ref:`usage-tips` to have a better understanding of how to use ``django-unasyncify``.
