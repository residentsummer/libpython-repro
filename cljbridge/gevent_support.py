import time

from gevent import get_hub

from . import clojure

import logging
logger = logging.getLogger(__name__)


## Python+Clojure bootstrap

def spawn_real_thread(fn, *args, **kwargs):
    '''Spawns real OS thread, while loops are running on gevent'''
    pool = get_hub().threadpool
    return pool.spawn(fn, *args, **kwargs)


def start_clojure_thread(aliases=None, with_repl=True, post_init=None):
    '''Make sure repl deps are there, if you want to start it'''

    # Must be done on main thread
    jvm_params = clojure.prepare_jvm_params(aliases)

    def clj_thread():
        clojure.init(jvm_params)
        if with_repl:
            clojure.start_repl("0.0.0.0", 50000)

        if post_init:
            post_init()

        while True:
            # logger.warning("test")
            time.sleep(3600)

    spawn_real_thread(clj_thread)
