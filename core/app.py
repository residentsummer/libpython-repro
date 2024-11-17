import core.use_gevent_aio_loop  # noqa: should go first due to monkey-patching

import asyncio
import json
from pprint import pformat

from cljbridge.gevent_support import start_clojure_thread
from cljbridge import clojure


TAP = None


def set_tap(fn):
    global TAP
    TAP = fn


def start_clojure_app():
    print("starting clojure app")
    clojure.require("eeel.main")
    clojure.resolve_call_fn("eeel.main/-main")


def save_something():
    '''To be called from clojure'''
    test_obj = json.loads('{"test": [1, 2, 3, 4]}')
    print("saved:", pformat(test_obj))
    if TAP:
        TAP(test_obj)


async def main():
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    print("starting clojure thread")
    start_clojure_thread(['dev', 'repl'], post_init=start_clojure_app)
    asyncio.run(main())
