import libcst as cst

from django_unasyncify.config import Config


class UnasyncifyMethod(cst.CSTTransformer):
    """
    Make a non-sync version of the method
    """

    config: Config
    is_async_seen: bool

    def __init__(self, config):
        self.config = config
        self.await_depth = 0
        self.is_async_seen = False

    def visit_Await(self, node):
        self.await_depth += 1

    def leave_Await(self, original_node, updated_node):
        self.await_depth -= 1
        # we just remove the actual await
        return updated_node.expression

    def leave_Name(self, original_node, updated_node):
        # IS_ASYNC is a bit of a special case
        if updated_node.value == "IS_ASYNC":
            self.is_async_seen = True
        # some names will get rewritten because we know
        # about them
        if updated_node.value in self.config.attribute_renames:
            return updated_node.with_changes(
                value=self.config.attribute_renames[updated_node.value]
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
        # checking if the original if was "if IS_ASYNC"
        # (the updated node would have turned this to if False)
        if (
            isinstance(original_node.test, cst.Name)
            and original_node.test.value == "IS_ASYNC"
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
