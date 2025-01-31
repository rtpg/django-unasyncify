Why Not ``sync_to_async``?
==========================

If you are asked to have async and synchronous variants for your API, it might be tempting to reach for ``asgiref``'s ``sync_to_async`` wrapper.

While ``sync_to_async`` provides a helpful last-resort tool to offer an async API, it has a couple issues.


``sync_to_async`` prevents


Backwards Compatibility Issues In Subclasses
---------------------------------------------

Imagine you have the following class in a Django library::

  class ThingDoer:
    def do_thing(self):
      self.step1()
      self.step2()
      self.step3()

    async def ado_thing(self):
      await sync_to_async(self.do_thing)()


A user of ``ThingDoer`` subclasses it to add their own custom step::

  class SpecialThingDoer(ThingDoer):
    def do_thing(self):
      super().do_thing()
      self.step4()

At this point something odd has happened. ``SpecialThingDoer.ado_thing`` will _also_ use ``step4``!

At first this seems great. After all, the user wants to have ``step4`` happen and since it was specified in ``do_thing``, you "probably" want it in ``step4``


At one point you realise that ``step2`` can be made async! Of course in order to do so we can no longer blindly call ``sync_to_async``::

  class ThingDoer:
    def do_thing(self):
      self.step1()
      self.step2()
      self.step3()

    async def ado_thing(self):
      self.step1()
      await self.astep2()
      self.step3()

Here we broke out separate implementations, in order to actualy `await` on the second step.

This change just broke ``SpecialThingDoer``! While before it was able to rely on ``ado_thing`` calling into ``do_thing``, this is no longer the case.

Of course, in this new model, ``ThingDoer`` subclasses now have to maintain *two* method overrides to handle their extra step. In practice this can be extremely tedious (hence ``django-unasyncify``'s existence in the first place). So one might still opt for ``sync_to_async`` in circumstances where one really doesn't expect (or want) async operations to occur.

But if you want to hold out for a future where async makes sense, you probably want to avoid ``sync_to_async``.
