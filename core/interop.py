from cljbridge.gevent_support import start_clojure_thread
from cljbridge import clojure


def start_clojure():
    start_clojure_thread(['dev', 'repl'], post_init=start_app)


def start_app():
    clojure.require("dev")
    clojure.resolve_call_fn("dev/-main")


__BORROWED = {}

def borrow(pyobj):
    __BORROWED[id(pyobj)] = pyobj
    return pyobj

def release(pyobj):
    del __BORROWED[id(pyobj)]
