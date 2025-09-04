import pytest

plugins = ['pytester']


@pytest.fixture
def single_test_item(pytester, request):
    cache = getattr(request.config, "_collected_single_test_item_cache", None)
    if cache is None:
        pytester.makepyfile(test_single='''
                import pytest
    
                @pytest.mark.testomatio("@T12345678")
                def test_addition():
                    """Test basic addition"""
                    assert 1 + 1 == 2
            ''')
        items = pytester.getitems(pytester.path / 'test_single.py')
        request.config._collected_single_test_item_cache = items
        return items
    return request.config._collected_single_test_item_cache


@pytest.fixture
def multiple_test_items(pytester, request):
    cache = getattr(request.config, "_collected_multiple_test_item_cache", None)
    if cache is None:
        pytester.makepyfile(test_multiple='''
                import pytest

                @pytest.mark.testomatio("@T12345678")
                def test_division():
                    """Test basic division"""
                    assert 2 / 2 == 1
                    
                @pytest.mark.testomatio("@T42312343")
                def test_first():
                    assert True
                    
                @pytest.mark.testomatio("@T46512343")
                @pytest.mark.parametrize("value", [1, 2, 3])
                def test_parametrized(value):
                    assert value > 0
                    
            ''')
        items = pytester.getitems(pytester.path / 'test_multiple.py')
        request.config._collected_multiple_test_item_cache = items
        return items
    return request.config._collected_multiple_test_item_cache
