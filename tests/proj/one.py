# ruff: noqa


@generate_unasynced
async def aget_thing(qs):
    return await qs.aget()


@generate_unasynced
async def ado_thing():
    if IS_ASYNC:
        return 1
    else:
        return 2
