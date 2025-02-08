from libcst import EmptyLine, FunctionDef, Name, Decorator
from libcst.helpers import get_full_name_for_node

from collections import namedtuple
from typing import cast

import libcst as cst
import libcst.matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor

from django_unasyncify.config import Config
from .transform import UnasyncifyMethod

DecoratorInfo = namedtuple("DecoratorInfo", ["from_codegen", "unasync", "async_unsafe"])


class UnasyncifyMethodCommand(VisitorBasedCodemodCommand):
    DESCRIPTION = "Transform async methods to sync ones"

    config: Config

    def __init__(self, context: CodemodContext, config: Config) -> None:
        self.config = config
        super().__init__(context)

    def add_codegen_imports(self, *names):
        for name in names:
            AddImportsVisitor.add_needed_import(
                self.context, self.config.unasync_helpers_import_path, name
            )

    def label_as_codegen(self, node: FunctionDef, async_unsafe: bool) -> FunctionDef:
        from_codegen_marker = Decorator(decorator=Name("from_codegen"))
        self.add_codegen_imports("from_codegen", "generate_unasynced")

        decorators_to_add = [from_codegen_marker]
        if async_unsafe:
            async_unsafe_marker = Decorator(decorator=Name("async_unsafe"))
            AddImportsVisitor.add_needed_import(
                self.context, "django.utils.asyncio", "async_unsafe"
            )
            decorators_to_add.append(async_unsafe_marker)
        # we remove generate_unasynced_codegen
        return node.with_changes(decorators=[*decorators_to_add, *node.decorators[1:]])

    def codegenned_func(self, node: FunctionDef) -> bool:
        for decorator in node.decorators:
            if (
                isinstance(decorator.decorator, Name)
                and decorator.decorator.value == "from_codegen"
            ):
                return True
        return False

    unasynced_name = m.Name(value="generate_unasynced")
    generate_unasynced_pattern = unasynced_name | m.Call(func=unasynced_name)
    generate_unasync_pattern = m.Call(
        func=m.Name(value="generate_unasynced"),
    )

    generated_keyword_pattern = m.Arg(
        keyword=m.Name(value="async_unsafe"),
        value=m.Name(value="True"),
    )

    def decorator_info(self, node: FunctionDef) -> DecoratorInfo:
        from_codegen = False
        unasync = False
        async_unsafe = False

        # we only consider the top decorator, and will copy everything else
        if node.decorators:
            decorator = node.decorators[0]
            if m.matches(decorator.decorator, self.generate_unasynced_pattern):
                # raw call @generate_unasynced
                if isinstance(decorator.decorator, Name):
                    unasync = True
                    async_unsafe = False
                else:
                    # Safety: m.matches call above
                    call: cst.Call = cast(cst.Call, decorator.decorator)
                    unasync = True
                    args = call.args
                    if len(args) == 0:
                        async_unsafe = False
                    elif len(args) == 1:
                        # assert that it's async_unsafe, our only supported
                        # keyword for now
                        assert m.matches(
                            args[0], self.generated_keyword_pattern
                        ), f"We only support async_unsafe=True as a keyword argument, got {args}"
                        async_unsafe = True
                    else:
                        raise ValueError(
                            "generate_unasynced only supports 0 or 1 arguments"
                        )
            elif isinstance(decorator.decorator, cst.Name):
                if decorator.decorator.value == "from_codegen":
                    from_codegen = True

        return DecoratorInfo(from_codegen, unasync, async_unsafe)

    def decorator_names(self, node: FunctionDef) -> list[str]:
        # get the names of the decorators on this function
        # this doesn't try very hard
        return [
            decorator.decorator.value
            for decorator in node.decorators
            if isinstance(decorator.decorator, Name)
        ]

    def calculate_new_name(self, old_name):
        if old_name.startswith("test_async_"):
            # test_async_foo -> test_foo
            return old_name.replace("test_async_", "test_", 1)
        if old_name.startswith("_a"):
            # _ainsert -> _insert
            return old_name.replace("_a", "_", 1)
        if old_name.startswith("a"):
            # aget -> get
            return old_name[1:]
        raise ValueError(
            f"""
            Unknown name replacement pasttern for {old_name}
            """
        )

    def leave_FunctionDef(self, original_node: FunctionDef, updated_node: FunctionDef):
        decorator_info = self.decorator_info(updated_node)
        # if we are looking at something that's already codegen, drop it
        # (it will get regenerated)
        if decorator_info.from_codegen:
            return cst.RemovalSentinel.REMOVE

        if decorator_info.unasync:
            new_name = self.calculate_new_name(
                get_full_name_for_node(updated_node.name)
            )

            unasynced_func = updated_node.with_changes(
                name=Name(new_name),
                asynchronous=None,
            )
            unasynced_func = self.label_as_codegen(
                unasynced_func, async_unsafe=decorator_info.async_unsafe
            )
            transformer = UnasyncifyMethod(self.config)

            transformed_unasynced_func = unasynced_func.visit(transformer)

            if transformer.is_async_seen:
                self.add_codegen_imports("IS_ASYNC")

            # while here the async version is the canonical version, we place
            # the unasync version up on top
            return cst.FlattenSentinel(
                [transformed_unasynced_func, EmptyLine(), updated_node]
            )
        else:
            return updated_node
