import asyncio
from pathlib import Path
from textwrap import dedent

from libcst.codemod import CodemodTest

from django_unasyncify.transform import UnasyncifyMethodCommand
from django_unasyncify.config import Config


class TestFoo(CodemodTest):

    TRANSFORM = UnasyncifyMethodCommand

    def test_unasynced_generation(self):
        before = """
        @generate_unasynced()
        async def aoperation(self):
          # a comment to be preserved
          await self.afoo()
        """

        after = """
        from django.utils.codegen import from_codegen, generate_unasynced

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
        from django.utils.codegen import from_codegen, generate_unasynced

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
