import os
from pytest import Config


def validate_env_variables():
    if os.getenv('TESTOMATIO') is None:
        raise ValueError('TESTOMATIO env variable is not set')

    # if os.getenv('TESTOMATIO_SHARED_RUN') and not os.getenv('TESTOMATIO_TITLE'):
    #     raise ValueError('TESTOMATIO_SHARED_RUN can only be used together with TESTOMATIO_TITLE')


def validate_command_line_args(config: Config):
    if config.getoption('numprocesses'):
        if config.getoption('testomatio') and config.getoption('testomatio').lower() in ('sync', 'debug', 'remove'):
            raise ValueError('Testomatio does not support parallel sync, remove or debug. Remove --numprocesses option')
