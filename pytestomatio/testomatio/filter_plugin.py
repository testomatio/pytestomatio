import pytest

class TestomatioFilterPlugin:
    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        # By now all other filters (like -m, -k, name-based) have been applied
        # and `items` is the filtered set after all their conditions.
        test_ids_str = config.getoption("test_id")
        if not test_ids_str:
            # No custom IDs specified, nothing to do
            return

        test_ids = test_ids_str.split("|")
        # Remove "@" from the start of test IDs if present
        test_ids = [test_id.lstrip("@T") for test_id in test_ids]
        if not test_ids:
            return

        # Now let's find all tests that match these test IDs from the original full list.
        # We use the originally collected tests to avoid losing tests filtered out by others.
        original_items = session._pytestomatio_original_collected_items
        testomatio_matched = []
 
        for item in original_items:
            # Check for testomatio marker
            for marker in item.iter_markers(name="testomatio"):

                marker_id = marker.args[0].lstrip("@T")  # Strip "@" from the marker argument
                if marker_id in test_ids:
                     testomatio_matched.append(item)
                     break
       
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
