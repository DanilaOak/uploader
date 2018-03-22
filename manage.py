import asyncio
import logging

from aiohttp import web
from aio_manager import Manager, Command
from aio_manager.commands.runserver import RunServer as BaseRunServer
import pytest

from app import create_app
from utils import create_database, get_config, drop_database, migrate, get_test_config

app = create_app()
manager = Manager(app)
config = get_config()


class RunTests(Command):
    def run(self, app, args):
        loop = asyncio.get_event_loop()
        test_config = get_test_config()
        loop.run_until_complete(create_database(test_config))
        run_command = './tests'

        if args.test_file:
            run_command += '/' + args.test_file

        pytest.main(['-x', '-s', run_command])

        loop.run_until_complete(drop_database(test_config))

    def configure_parser(self, parser):
        super().configure_parser(parser)
        parser.add_argument('--test-file')


manager.add_command(RunTests('tests', app))


class RunServer(BaseRunServer):
    def run(self, app, args):
        logging.basicConfig(level=args.level)
        logging.getLogger().setLevel(args.level)
        web.run_app(app, host=args.hostname, port=config['PORT'], access_log=None)


manager.add_command(RunServer(app))


class CreateDatabase(Command):
    def run(self, app, args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(create_database(config))


manager.add_command(CreateDatabase('create_database', app))


class DropDatabase(Command):
    def run(self, app, args):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(drop_database(config))


manager.add_command(DropDatabase('drop_database', app))


class Migrate(Command):
    def run(self, app, args):
        migrate(config)


manager.add_command(Migrate('migrate', app))


class ResetDB(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands = [
            DropDatabase(*args, **kwargs),
            CreateDatabase(*args, **kwargs),
            Migrate(*args, **kwargs)
        ]

    def run(self, app, args):
        for cm in self._commands:
            cm.run(app, args)


manager.add_command(ResetDB('reset_db', app))


if __name__ == '__main__':
    manager.run()
