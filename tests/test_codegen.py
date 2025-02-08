import asyncio
from pathlib import Path
from textwrap import dedent

from libcst.codemod import CodemodTest
from django_unasyncify.scaffolding import ensure_codegen_template

from django_unasyncify.codemod import UnasyncifyMethodCommand
from django_unasyncify.config import Config


class TestTranforms(CodemodTest):
    TRANSFORM = UnasyncifyMethodCommand

    def test_unasynced_generation(self):
        before = """
        @generate_unasynced()
        async def aoperation(self):
          # a comment to be preserved
          await self.afoo()
        """

        after = """
        from MISSING_IMPORT_PATH import from_codegen, generate_unasynced

        @from_codegen
        def operation(self):
          # a comment to be preserved
          self.foo()

        @generate_unasynced()
        async def aoperation(self):
          # a comment to be preserved
          await self.afoo()
        """

        self.assertCodemod(before, after, config=Config())

    def test_unasynced_generation_no_parens(self):
        before = """
        @generate_unasynced
        async def aoperation(self):
          # a comment to be preserved
          await self.afoo()
        """

        after = """
        from MISSING_IMPORT_PATH import from_codegen, generate_unasynced

        @from_codegen
        def operation(self):
          # a comment to be preserved
          self.foo()

        @generate_unasynced
        async def aoperation(self):
          # a comment to be preserved
          await self.afoo()
        """

        self.assertCodemod(before, after, config=Config())

    def test_usage_tip_example(self):
        before = """
        @generate_unasynced
        async def arun_calculation(data):
            result = {"used_async": IS_ASYNC}
            if IS_ASYNC:
                result["data"] = await third_party_lib.async_calc(data)
            else:
                result["data"] = another_third_party_lib.sync_calc(data)
            return result
        """

        after = """
        from MISSING_IMPORT_PATH import IS_ASYNC, from_codegen, generate_unasynced

        @from_codegen
        def run_calculation(data):
            result = {"used_async": False}
            result["data"] = another_third_party_lib.sync_calc(data)
            return result

        @generate_unasynced
        async def arun_calculation(data):
            result = {"used_async": IS_ASYNC}
            if IS_ASYNC:
                result["data"] = await third_party_lib.async_calc(data)
            else:
                result["data"] = another_third_party_lib.sync_calc(data)
            return result
        """

        self.assertCodemod(before, after, config=Config())


class TestRuns(CodemodTest):
    TRANSFORM = UnasyncifyMethodCommand

    @classmethod
    def setUpClass(cls):
        # write out the codegen template
        ensure_codegen_template(Path(__file__).parent / "_codegen.py")

        cls.config = Config(
            # hacky relative import
            unasync_helpers_import_path="_codegen"
        )

    def test_is_async(self):
        before = """
        @generate_unasynced
        async def ado_thing():
          if IS_ASYNC:
            return 1
          else:
            return 2
        """

        after = """
        from _codegen import IS_ASYNC, from_codegen, generate_unasynced

        @from_codegen
        def do_thing():
          return 2

        @generate_unasynced
        async def ado_thing():
          if IS_ASYNC:
            return 1
          else:
            return 2
        """

        self.assertCodemod(before, after, config=self.config)

        # also confirm this code is properly loadable
        after_globals = {}
        exec(dedent(after), after_globals)
        assert after_globals["do_thing"]() == 2
        loop = asyncio.new_event_loop()
        assert loop.run_until_complete(after_globals["ado_thing"]()) == 1
