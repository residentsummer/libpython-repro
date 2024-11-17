import gevent.monkey
gevent.monkey.patch_all()

import asyncio
import asyncio_gevent
asyncio.set_event_loop_policy(asyncio_gevent.EventLoopPolicy())
