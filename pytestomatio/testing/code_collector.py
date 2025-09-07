import importlib.util
import inspect

# TODO: Create Code Collector class, use Strategy pattern or Registry for code extracting if needed?


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


SOURCE_EXTRACTORS = [
    (lambda f: hasattr(f, '__scenario__'), get_bdd_function_source),  # extractor for pytest-bdd functions
    (lambda f: True, inspect.getsource)  # fallback extractor
]


def extract_source_code(function) -> str:
    """Extracts function source code. Dynamically applies code extractor depends on function type"""
    for predicate, extractor in SOURCE_EXTRACTORS:
        if predicate(function):
            return extractor(function)


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
            source = extract_source_code(function)
            yield function_name, source
