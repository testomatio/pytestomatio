import ast
import autopep8

pytest_mark = 'pytest', 'mark'


class DecoratorUpdater(ast.NodeTransformer):
    def __init__(self, mapped_tests: list[tuple[str, int]], all_tests: list[str], decorator_name: str):
        self.mapped_tests = mapped_tests
        self.all_tests = all_tests
        self.decorator_name = decorator_name

    def _get_id_by_title(self, title: str):
        for pair in self.mapped_tests:
            if pair[0] == title:
                return pair[1]

    def _remove_decorator(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.decorator_list = [decorator for decorator in node.decorator_list if
                               not (isinstance(decorator, ast.Call) and decorator.func.attr == self.decorator_name)]
        return node

    def remove_decorators(self, tree: ast.Module) -> ast.Module:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.visit_FunctionDef(node, remove=True)
        return tree

    def visit_FunctionDef(self, node: ast.FunctionDef, remove=False) -> ast.FunctionDef:
        if remove:
            return self._remove_decorator(node)
        else:
            if node.name in self.all_tests:
                if not any(isinstance(decorator, ast.Call) and
                           decorator.func.attr == self.decorator_name
                           for decorator in node.decorator_list):
                    test_id = self._get_id_by_title(node.name)
                    deco_name = f'mark.{self.decorator_name}(\'{test_id}\')'
                    decorator = ast.Name(id=deco_name, ctx=ast.Load())
                    node.decorator_list = [decorator] + node.decorator_list
        return node

    def insert_pytest_mark_import(self, tree: ast.Module, module_name: str, decorator_name: str) -> None:
        # Check if the import statement already exists
        if not any(
                isinstance(node, ast.ImportFrom) and
                node.module == module_name and
                any(alias.name == decorator_name for alias in node.names)
                for node in tree.body
        ):
            import_node = ast.ImportFrom(
                module=module_name,
                names=[ast.alias(name=decorator_name, asname=None)],
                level=0
            )
            tree.body.insert(0, import_node)


def update_tests(file: str,
                 mapped_tests: list[tuple[str, int]],
                 all_tests: list[str],
                 decorator_name: str,
                 remove=False):
    with open(file, 'r') as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    transform = DecoratorUpdater(mapped_tests, all_tests, decorator_name)
    if remove:
        transform.remove_decorators(tree)
    else:
        tree = transform.visit(tree)
        transform.insert_pytest_mark_import(tree, *pytest_mark)
    updated_source_code = ast.unparse(tree)

    pep8_source_code = autopep8.fix_code(updated_source_code)

    with open(file, "w") as file:
        file.write(pep8_source_code)