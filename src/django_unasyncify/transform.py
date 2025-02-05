from collections import namedtuple
import libcst as cst
from libcst import EmptyLine, FunctionDef, Name, Decorator
from libcst.helpers import get_full_name_for_node

from typing import cast

import libcst.matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


DecoratorInfo = namedtuple("DecoratorInfo", ["from_codegen", "unasync", "async_unsafe"])


class UnasyncifyMethod(cst.CSTTransformer):
    """
    Make a non-sync version of the method
    """

    def __init__(self):
        self.await_depth = 0

    def visit_Await(self, node):
        self.await_depth += 1

    def leave_Await(self, original_node, updated_node):
        self.await_depth -= 1
        # we just remove the actual await
        return updated_node.expression

    NAMES_TO_REWRITE = {
        "aconnection": "connection",
        "ASYNC_TRUTH_MARKER": "False",
        "acursor": "cursor",
    }

    def leave_Name(self, original_node, updated_node):
        # some names will get rewritten because we know
        # about them
        if updated_node.value in self.NAMES_TO_REWRITE:
            return updated_node.with_changes(
                value=self.NAMES_TO_REWRITE[updated_node.value]
            )
        return updated_node

    def unasynced_function_name(self, func_name: str) -> str | None:
        """
        Return the function name for an unasync version of this
        function (or None if there is no unasync version)
        """
        # XXX bit embarassing but...
        if func_name == "all":
            return None
        if func_name.startswith("a"):
            return func_name[1:]
        elif func_name.startswith("_a"):
            return "_" + func_name[2:]
        else:
            return None

    def leave_Call(self, original_node, updated_node):
        if self.await_depth == 0:
            # we only transform calls that are part of
            # an await expression
            return updated_node

        func_name: cst.Name
        if isinstance(updated_node.func, cst.Name):
            func_name = updated_node.func
            unasync_name = self.unasynced_function_name(updated_node.func.value)
            if unasync_name is not None:
                # let's transform it by removing the a
                unasync_func_name = func_name.with_changes(value=unasync_name)
                return updated_node.with_changes(func=unasync_func_name)

        elif isinstance(updated_node.func, cst.Attribute):
            func_name = updated_node.func.attr
            unasync_name = self.unasynced_function_name(updated_node.func.attr.value)
            if unasync_name is not None:
                # let's transform it by removing the a
                return updated_node.with_changes(
                    func=updated_node.func.with_changes(
                        attr=func_name.with_changes(value=unasync_name)
                    )
                )
        return updated_node

    def leave_If(self, original_node, updated_node):
        # checking if the original if was "if ASYNC_TRUTH_MARKER"
        # (the updated node would have turned this to if False)
        if (
            isinstance(original_node.test, cst.Name)
            and original_node.test.value == "ASYNC_TRUTH_MARKER"
        ):
            if updated_node.orelse is not None:
                if isinstance(updated_node.orelse, cst.Else):
                    # unindent
                    return cst.FlattenSentinel(updated_node.orelse.body.body)
                else:
                    # we seem to have elif continuations so use that
                    return updated_node.orelse
            else:
                # if there's no else branch we just remove the node
                return cst.RemovalSentinel.REMOVE
        return updated_node

    def leave_CompFor(self, original_node, updated_node):
        if updated_node.asynchronous is not None:
            return updated_node.with_changes(asynchronous=None)
        else:
            return updated_node

    def leave_For(self, original_node, updated_node):
        if updated_node.asynchronous is not None:
            return updated_node.with_changes(asynchronous=None)
        else:
            return updated_node

    def leave_With(self, original_node, updated_node):
        if updated_node.asynchronous is not None:
            return updated_node.with_changes(asynchronous=None)
        else:
            return updated_node


class UnasyncifyMethodCommand(VisitorBasedCodemodCommand):
    DESCRIPTION = "Transform async methods to sync ones"

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)

    def label_as_codegen(self, node: FunctionDef, async_unsafe: bool) -> FunctionDef:
        from_codegen_marker = Decorator(decorator=Name("from_codegen"))
        AddImportsVisitor.add_needed_import(
            self.context, "django.utils.codegen", "from_codegen"
        )

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
            if isinstance(decorator.decorator, cst.Name):
                if decorator.decorator.value == "from_codegen":
                    from_codegen = True
            elif m.matches(decorator.decorator, self.generate_unasync_pattern):
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
            transformed_unasynced_func = unasynced_func.visit(UnasyncifyMethod())

            # while here the async version is the canonical version, we place
            # the unasync version up on top
            return cst.FlattenSentinel(
                [transformed_unasynced_func, EmptyLine(), updated_node]
            )
        else:
            return updated_node
