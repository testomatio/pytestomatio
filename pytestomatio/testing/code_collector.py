import importlib.util
import inspect

# TODO: Create Code Collector class?


def get_bdd_function_source(function):
    """Get pytest_bdd plugin function source code. If source code not received from closure, return wrapper code"""
    source_code = None
    if hasattr(function, '__closure__') and function.__closure__ is not None:
        for cell in function.__closure__:
            content = cell.cell_contents
            # Check if function is user function
            if callable(content) and hasattr(content, '__name__') and \
                    content.__name__.startswith('test_'):
                source_code = inspect.getsource(content)
                break
    return source_code if source_code else inspect.getsource(function)


def get_functions_source_by_name(abs_file_path: str, all_tests: list[str]):
    spec = importlib.util.spec_from_file_location('name', abs_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    functions = inspect.getmembers(module, inspect.isfunction)
    classes = inspect.getmembers(module, inspect.isclass)
    for class_name, cls in classes:
        functions += inspect.getmembers(cls, inspect.isfunction)
    for function_name, function in functions:
        if function_name in all_tests:
            source = get_bdd_function_source(function) if hasattr(function, '__scenario__') else \
                inspect.getsource(function)
            yield function_name, source
