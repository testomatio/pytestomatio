from pytest import Parser

help_text = """
            synchronise and connect test with testomat.io. Use parameters:
            sync - synchronize tests and set test ids in the code
            remove - removes testomat.io ids from the ALL test
            report - report tests into testomat.io
            debug - saves analysed test metadata to the json in the test project root
            """


def parser_options(parser: Parser, testomatio='testomatio') -> None:
    parser.addoption(f'--{testomatio}',
                     action='store',
                     help=help_text)
    parser.addoption(f'--testRunEnv',
                     action='store',
                     help=f'specify test run environment for testomat.io. Works only with --testomatio sync')
    parser.addoption(f'--create',
                     action='store_true',
                     default=False,
                     dest="create",
                     help="""
                        To import tests with Test IDs set in source code into a project use --create option.
                        In this case a project will be populated with the same Test IDs as in the code.
                        Use --testomatio sync together with --create option to enable this behavior.
                        """
                     )
    parser.addoption(f'--no-empty',
                     action='store_true',
                     default=False,
                     dest="no_empty",
                     help="""
                        Delete empty suites.
                        When tests are marked with IDs and imported to already created suites in Testomat.io newly imported suites may become empty.
                        Use --testomatio sync together with --no-empty option to clean them up after import.
                        """
                     )
    parser.addoption(f'--no-detach',
                     action='store_true',
                     default=False,
                     dest="no_detach",
                     help="""
                        Disable detaching tests.
                        If a test from a previous import was not found on next import it is marked as "detached".
                        This is done to ensure that deleted tests are not staying in Testomatio while deleted in codebase.
                        To disable this behaviour and don\'t mark anything on detached on import use sync together with --no-detached option.
                        """
                     )
    parser.addoption(f'--keep-structure',
                     action='store_true',
                     default=False,
                     dest="keep_structure",
                     help="""
                        Keep structure of source code. If suites are not created in Testomat.io they will be created based on the file structure.
                        Use --testomatio sync together with --structure option to enable this behaviour.
                        """
                     )
    parser.addoption('--directory',
                     default=None,
                     dest="directory",
                     help="""
                        Specify directory to use for test file structure, ex. --directory Windows\\smoke or --directory Linux/e2e
                        Use --testomatio sync together with --directory option to enable this behaviour.
                        Default is the root of the project.
                        Note: --structure option takes precedence over --directory option. If both are used --structure will be used.
                        """
                     )
    parser.addini('testomatio_url', 'testomat.io base url', default='https://app.testomat.io')
