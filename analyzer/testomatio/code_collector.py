import importlib.util
import inspect


def get_functions_source_by_name(abs_file_path: str, all_tests: list[str]):
    spec = importlib.util.spec_from_file_location('name', abs_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    functions = inspect.getmembers(module, inspect.isfunction)
    classes = inspect.getmembers(module, inspect.isclass)
    for class_name, cls in classes:
        print(f"Class name: {class_name}")
        functions += inspect.getmembers(cls, inspect.isfunction)
    for function_name, function in functions:
        if function_name in all_tests:
            yield function_name, inspect.getsource(function)
