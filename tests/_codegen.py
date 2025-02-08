"""
This file is managed by django-unasyncify and should not be
directly modified. Future runs of django-unasyncify will
likely overwrite any changes you make to this file.
"""


def from_codegen(f):
    """
    This indicates that the function was gotten from codegen, and
    should not be directly modified
    """
    return f


def generate_unasynced(*args, **kwargs):
    """
    This indicates we should unasync this function/method
    """

    def wrapper(f):
        return f

    # @generate_unasynced()
    if not args and not kwargs:
        return wrapper

    # @generate_unasynced
    if args:
        assert (
            len(args) == 1 and len(kwargs) == 0
        ), "Invalid calling convention for generate_unasynced"
        return args[0]

    if kwargs:
        raise NotImplementedError("Handling kwargs...")


# this marker gets replaced by False when unasyncifying a function
IS_ASYNC = True
