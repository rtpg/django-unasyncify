from libcst.codemod import CodemodTest

from django_unasyncify.transform import UnasyncifyMethodCommand


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
        from django.utils.codegen import from_codegen

        @from_codegen
        def operation(self):
          # a comment to be preserved
          self.foo()

        @generate_unasynced()
        async def aoperation(self):
          # a comment to be preserved
          await self.afoo()
        """

        self.assertCodemod(before, after)

    # def test_something(self):
    #     assert 1 == 2
