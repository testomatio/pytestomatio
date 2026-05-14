import pytest
from unittest.mock import Mock
from pytestomatio.utils.parser_setup import parser_options, help_text


class TestParserOptions:
    """Test for parser_options function"""

    @pytest.fixture
    def mock_parser(self):
        parser = Mock()
        mock_group = Mock()
        parser.getgroup.return_value = mock_group
        parser.addini = Mock()
        return parser

    def test_parser_options_creates_testomatio_group(self, mock_parser):
        """Test testomatio group options created"""
        parser_options(mock_parser)

        mock_parser.getgroup.assert_called_once_with(
            'testomatio',
            'synchronise and connect test with testomat.io'
        )

    def test_parser_options_with_custom_name(self, mock_parser):
        """Test custom group can be set"""
        custom_name = 'custom_testomatio'
        parser_options(mock_parser, custom_name)

        mock_parser.getgroup.assert_called_once_with(
            custom_name,
            'synchronise and connect test with testomat.io'
        )

    def test_parser_options_adds_main_testomatio_option(self, mock_parser):
        """Test --testomatio option --testomatio is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        mock_group.addoption.assert_any_call(
            '--testomatio',
            action='store',
            help=help_text
        )

    def test_parser_options_adds_kind_option(self, mock_parser):
        """Test --kind option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        mock_group.addoption.assert_any_call(
            '--kind',
            action='store',
            help="Specify kind of test run to be created"
        )

    def test_parser_options_adds_test_run_env_option(self, mock_parser):
        """Test --testRunEnv option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        mock_group.addoption.assert_any_call(
            '--testRunEnv',
            action='store',
            help='specify test run environment for testomat.io. Works only with --testomatio report'
        )

    def test_parser_options_adds_create_option(self, mock_parser):
        """Test --create option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        expected_help = """
                        To import tests with Test IDs set in source code into a project use --create option.
                        In this case a project will be populated with the same Test IDs as in the code.
                        Use --testomatio sync together with --create option to enable this behavior.
                        """

        mock_group.addoption.assert_any_call(
            '--create',
            action='store_true',
            default=False,
            dest="create",
            help=expected_help
        )

    def test_parser_options_adds_no_empty_option(self, mock_parser):
        """Test --no-empty option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        expected_help = """
                        Delete empty suites.
                        When tests are marked with IDs and imported to already created suites in Testomat.io newly imported suites may become empty.
                        Use --testomatio sync together with --no-empty option to clean them up after import.
                        """

        mock_group.addoption.assert_any_call(
            '--no-empty',
            action='store_true',
            default=False,
            dest="no_empty",
            help=expected_help
        )

    def test_parser_options_adds_no_detach_option(self, mock_parser):
        """Test --no-detach option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        expected_help = """
                        Disable detaching tests.
                        If a test from a previous import was not found on next import it is marked as "detached".
                        This is done to ensure that deleted tests are not staying in Testomatio while deleted in codebase.
                        To disable this behaviour and don\'t mark anything on detached on import use sync together with --no-detached option.
                        """

        mock_group.addoption.assert_any_call(
            '--no-detach',
            action='store_true',
            default=False,
            dest="no_detach",
            help=expected_help
        )

    def test_parser_options_adds_keep_structure_option(self, mock_parser):
        """Test --keep-structure option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        expected_help = """
                        Keep structure of source code. If suites are not created in Testomat.io they will be created based on the file structure.
                        Use --testomatio sync together with --structure option to enable this behaviour.
                        """

        mock_group.addoption.assert_any_call(
            '--keep-structure',
            action='store_true',
            default=False,
            dest="keep_structure",
            help=expected_help
        )

    def test_parser_options_adds_directory_option(self, mock_parser):
        """Test --directory option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        expected_help = """
                        Specify directory to use for test file structure, ex. --directory Windows\\smoke or --directory Linux/e2e
                        Use --testomatio sync together with --directory option to enable this behaviour.
                        Default is the root of the project.
                        Note: --structure option takes precedence over --directory option. If both are used --structure will be used.
                        """

        mock_group.addoption.assert_any_call(
            '--directory',
            default=None,
            dest="directory",
            help=expected_help
        )

    def test_parser_options_adds_test_id_option(self, mock_parser):
        """Test --test-id option is added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        expected_help = """
                        help="Filter tests by Test IDs (e.g., single test id 'T00C73028' or multiply 'T00C73028|T00C73029')
                        """

        mock_group.addoption.assert_any_call(
            '--test-id',
            default=None,
            dest="test_id",
            help=expected_help
        )

    def test_parser_options_adds_ini_option(self, mock_parser):
        """Test ini option for testomatio_url added"""
        parser_options(mock_parser)

        mock_parser.addini.assert_called_once_with(
            'testomatio_url',
            'testomat.io base url'
        )

    def test_parser_options_call_count(self, mock_parser):
        """Test all options was added"""
        mock_group = mock_parser.getgroup.return_value

        parser_options(mock_parser)

        assert mock_group.addoption.call_count == 9
        assert mock_parser.addini.call_count == 1


class TestParserOptionsIntegration:
    """Parser_options integration tests"""

    def test_all_store_true_options_have_dest(self):
        """Test all store_true option have dest parameter"""
        parser = Mock()
        group = Mock()
        parser.getgroup.return_value = group

        store_true_calls = []

        def capture_store_true(*args, **kwargs):
            if kwargs.get('action') == 'store_true':
                store_true_calls.append((args, kwargs))

        group.addoption.side_effect = capture_store_true

        parser_options(parser)

        for args, kwargs in store_true_calls:
            assert 'dest' in kwargs, f"store_true option {args[0]} should have 'dest' parameter"
            assert kwargs['dest'] is not None, f"dest for {args[0]} should not be None"
