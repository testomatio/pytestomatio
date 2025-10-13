import logging
import pytest

log = logging.getLogger('pytestomatio')


class TestomatioFilterPlugin:
    # todo: check multiple values for filter, apply several filters
    allowed_filters = {'test_id', 'jira', 'label', 'plan', 'tag'}

    def get_matched_test_ids(self, f_type, f_value) -> list:
        """
        Returns test ids that matches given filter
        :param f_type: filter type(test_id, label)
        :param f_value: filter value
        """
        if f_type != 'test_id':
            test_ids = self.filter_by_testomatio_related_fields(f_type, f_value)
        else:
            test_ids = f_value.split("|")
        # Remove "@" from the start of test IDs if present
        cleared_ids = [test_id.lstrip("@T") for test_id in test_ids]
        return cleared_ids

    def filter_by_testomatio_related_fields(self, filter_type, filter_value):
        """Get ids of tests that matches filter from Testomatio. Used for Testomatio related filters"""
        connector = pytest.testomatio.connector
        tests = connector.get_filtered_tests(filter_type, filter_value)
        return tests.get('tests') if tests else []

    def match_tests_by_id(self, test_ids, items) -> list:
        matched_tests = []

        for item in items:
            # Check for testomatio marker
            for marker in item.iter_markers(name="testomatio"):

                marker_id = marker.args[0].lstrip("@T")  # Strip "@" from the marker argument
                if marker_id in test_ids:
                    matched_tests.append(item)
                    break
        return matched_tests

    def filter_tests(self, filter_opts, original_items):
        try:
            f_type, f_value = filter_opts.split('=')
            if not (f_type and f_value):
                log.error(f'Failed to retrieve filter data. Filter type: {f_type} Filter value: {f_value}')
                return

            if f_type not in self.allowed_filters:
                log.error(f"Filter '{f_type}' not allowed. Choose of these filters: {self.allowed_filters}")
                return

            log.info(f"Filtering tests using the '{f_type}' filter with '{f_value}' value")
            test_ids = self.get_matched_test_ids(f_type, f_value)
            if not test_ids:
                return

            return self.match_tests_by_id(test_ids, original_items)
        except ValueError as e:
            log.error(f"Incorrect filter format. Filter must be in type=value format. Received: {filter_opts}")

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        testomatio_option = config.getoption('testomatio')
        if testomatio_option is None or testomatio_option != 'report':
            return

        filter_opts = config.getoption('testomatio_filter')
        if not filter_opts:
            return

        log.info('Testomatio Filter enabled')
        # By now all other filters (like -m, -k, name-based) have been applied
        # and `items` is the filtered set after all their conditions.
        # We use the originally collected tests to avoid losing tests filtered out by others.
        original_items = session._pytestomatio_original_collected_items
        testomatio_matched = self.filter_tests(filter_opts, original_items)
        if not testomatio_matched:
            log.info('No tests were found matching the filter provided. Filtering is skipped')
            return
       
        # We'll check common filters: -k, -m and a few others.
        # If they are empty or None, they are not active.

        other_filters_active = bool(
            config.option.keyword or  # -k
            config.option.markexpr or # -m
            getattr(config.option, 'last_failed', False) or
            getattr(config.option, 'ff', False) or
            getattr(config.option, 'lf', False) or
            False
        )

        if other_filters_active and "not" in config.option.keyword:
            # If a "not" keyword filter exist - it means we have exclusion filter applied.
            # In such scenario we respect the exclusion filters in a way
            # that we accept tests with requested test ids as long as such tests do not fall into exclusion filter
            items[:] = [item for item in testomatio_matched if item in items]
            return

        if other_filters_active:
            # If other filters are applied, use OR logic:
            # the final set is all items that passed previous filters plus those matched by test-ids
            # preserving original order of test
            items[:] = items + [item for item in testomatio_matched if item not in items]
            return

        # If no other filters are applied, test-ids filter acts as an exclusive filter:
        # only run tests that match the given test IDs
        items[:] = testomatio_matched
