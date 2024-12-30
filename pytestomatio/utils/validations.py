import os
from typing import Literal
from pytest import Config
from _pytest.config.exceptions import UsageError



def validate_option(config: Config) -> Literal['sync', 'report', 'remove', 'debug', None]:
    option = config.getoption('testomatio')
    option = option.lower() if option else None
    if option in ('sync', 'report', 'remove'):
        if os.getenv('TESTOMATIO') is None:
            raise ValueError('TESTOMATIO env variable is not set')

    xdist_plugin = config.pluginmanager.getplugin('xdist')
    if xdist_plugin and option in ('sync', 'debug', 'remove'):
        if config.option.numprocesses == 0:
            return

        raise UsageError("The 'sync' mode does not support parallel execution! "
                     "In order to synchronise test run command sync as '--testomatio sync -n 0'")

    return option
