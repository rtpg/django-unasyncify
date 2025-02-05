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
        "src/some/specificic/file.py",
     ]

     # path to a python file that django-unasyncify will create
     # that holds decorators used for codegen
     codegen_decorators_path = "src/pkg/_codegen.py"
     # The import path for the decorator
     codegen_import_path = "pkg._codegen"

3. Decorate a method that you want to generate a synchronous variant of. Make sure to follow the Django naming convention of starting your async method with an ``a``!::

     # notice the path here, the same as the codegen_import_path setting
     # (this file will be created once you run django-unasync at least once)
     from pkg._codegen import generate_unasynced

     ...

     class SessionMgr:
        ...

        @generate_unasynced
        async def aexists(self, session_key):
            return await self.model.objects.filter(session_key=session_key).aexists()

4. Once you have labelled your code, you can run ``djang-unasyncify`` at the root of the project (in the same working directory as your ``pyproject.toml``)::

     django-unasyncify


5. After this, you should find your code modified with a sync variant::

    from pkg._codegen import generate_unasynced

    class SessionMgr:
        ...

        @from_codegen
        def exists(self, session_key):
            return self.models.objects.filter(session_key=session_key).exists()

        @generate_unasynced
        async def aexists(self, session_key):
            return await self.models.objects.filter(session_key=session-key).aexists()
