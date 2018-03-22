import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from aiohttp import web
import uvloop

from routes import setup_routes
from utils import get_config, connect_to_db

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
middlewares = []


def create_app(config=None):
    if not config:
        config = get_config()

    cpu_count = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()

    app = web.Application(loop=loop, middlewares=middlewares)
    app['executor'] = ProcessPoolExecutor(cpu_count)
    app['config'] = config
    app.on_startup.append(init_database)
    setup_routes(app)

    return app


async def init_database(app):
    app['pg'] = await connect_to_db(app['config'])
