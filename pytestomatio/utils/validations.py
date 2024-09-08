import os
from typing import Literal
from pytest import Config


def validate_option(config: Config) -> Literal['sync', 'report', 'remove', 'debug', None]:
    option = config.getoption('testomatio')
    option = option.lower() if option else None
    if option in ('sync', 'report', 'remove'):
        if os.getenv('TESTOMATIO') is None:
            raise ValueError('TESTOMATIO env variable is not set')

    if hasattr(config.option, 'numprocesses') and option in ('sync', 'debug', 'remove'):
        raise ValueError('Testomatio does not support parallel sync, remove or report. Remove --numprocesses option')

    return option
