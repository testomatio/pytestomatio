import os
from typing import Literal
from pytest import Config
from _pytest.config.exceptions import UsageError



def validate_option(config: Config) -> Literal['sync', 'report', 'remove', 'debug', 'launch', 'finish', None]:
    option = config.getoption('testomatio')
    option = option.lower() if option else None
    if option in ('sync', 'report', 'remove', 'launch', 'finish'):
        if os.getenv('TESTOMATIO') is None:
            raise ValueError('TESTOMATIO env variable is not set')

    if option == 'finish' and not (os.getenv('TESTOMATIO_RUN_ID') or os.getenv('TESTOMATIO_RUN')):
        raise ValueError('TESTOMATIO_RUN_ID env variable is not set')
    if option == 'launch' and (os.getenv('TESTOMATIO_RUN_ID') or os.getenv('TESTOMATIO_RUN')):
        raise ValueError('Test Run id was passed. Please unset TESTOMATIO_RUN_ID or '
                         'TESTOMATIO_RUN env variablses to create an empty run')

    xdist_plugin = config.pluginmanager.getplugin('xdist')
    if xdist_plugin and option in ('sync', 'debug', 'remove'):
        if config.option.numprocesses == 0:
            return

        raise UsageError("The 'sync' mode does not support parallel execution! "
                     "In order to synchronise test run command sync as '--testomatio sync -n 0'")

    return option
