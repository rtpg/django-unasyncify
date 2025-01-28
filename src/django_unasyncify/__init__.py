def hello() -> str:
    return "Hello from django-unasyncify!"


def from_codegen(f):
    """
    This indicates that the function was gotten from codegen, and
    should not be directly modified
    """
    return f


def generate_unasynced(async_unsafe=False):
    """
    This indicates we should unasync this function/method

    async_unsafe indicates whether to add the async_unsafe decorator
    """

    def wrapper(f):
        return f

    return wrapper


# this marker gets replaced by False when unasyncifying a function
# In particular this value never reads as False, even when we aren't
# in an async context
IS_ASYNC = True
