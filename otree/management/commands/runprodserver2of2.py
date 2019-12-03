import os
from sys import exit as sys_exit

from honcho.manager import Manager as HonchoManager
from django.core.management.base import BaseCommand
from otree.extensions import get_extensions_modules

class Command(BaseCommand):
    help = 'Run timeoutworker, botworker, and backgroundworker.'

    def add_arguments(self, parser):
        BaseCommand.add_arguments(self, parser)

    def handle(self, *args, verbosity=1, **options):
        # TODO: what is this for?
        self.verbosity = verbosity
        manager = self.get_honcho_manager()
        manager.loop()
        sys_exit(manager.returncode)

    def get_honcho_manager(self):

        # this env var is necessary because if the botworker submits a wait page,
        # it needs to broadcast to redis channel layer, not in-memory.
        # this caused an obscure bug on 2019-09-21.
        os.environ['OTREE_USE_REDIS'] = '1'
        env_copy = os.environ.copy()

        manager = HonchoManager()

        # if I change these, I need to modify the ServerCheck also
        manager.add_process('botworker', 'otree botworker', quiet=False, env=env_copy)
        manager.add_process(
            'timeoutworkeronly', 'otree timeoutworkeronly', quiet=False, env=env_copy
        )

        # add a worker for all background tasks
        channel_name_routes = []
        for extensions_module in get_extensions_modules('routing'):
            channel_name_routes += getattr(extensions_module, "channel_name_routes", {}).keys()

        if channel_name_routes:
            route_string = " ".join(channel_name_routes)
            manager.add_process('backgroundworker', 'otree runworker %s' % route_string, quiet=False, env=env_copy)

        return manager
