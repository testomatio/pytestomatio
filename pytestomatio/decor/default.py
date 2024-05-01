import libcst as cst
from typing import List, Tuple, Union


class DecoratorUpdater(cst.CSTTransformer):
    def __init__(self, mapped_tests: List[Tuple[str, int]], all_tests: List[str], decorator_name: str):
        self.mapped_tests = mapped_tests
        self.all_tests = all_tests
        self.decorator_name = decorator_name

    def _get_id_by_title(self, title: str):
        for pair in self.mapped_tests:
            if pair[0] == title:
                return pair[1]

    def _remove_decorator(self, node: cst.FunctionDef) -> cst.FunctionDef:
        node.decorator_list = [decorator for decorator in node.decorator_list if
                               not (isinstance(decorator, cst.Call) and decorator.func.attr == self.decorator_name)]
        return node

    def remove_decorators(self, tree: cst.Module) -> cst.Module:
        for node in cst.walk(tree):
            if isinstance(node, cst.FunctionDef):
                self.visit_FunctionDef(node, remove=True)
        return tree

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        if original_node.name.value in self.all_tests:
            test_id = self._get_id_by_title(original_node.name.value)
            if test_id is None:
                return updated_node

            deco_name = f'pytest.mark.{self.decorator_name}("{test_id}")'
            decorator = cst.Decorator(decorator=cst.parse_expression(deco_name))

            # Check if the decorator already exists
            for existing_decorator in original_node.decorators:
                if isinstance(existing_decorator.decorator, cst.Call) and \
                        isinstance(existing_decorator.decorator.func, cst.Attribute) and \
                        existing_decorator.decorator.func.attr.value == self.decorator_name:
                    # The decorator already exists, so we don't add it
                    return updated_node

            # The decorator doesn't exist, so we add it
            return updated_node.with_changes(decorators=[decorator] + list(updated_node.decorators))
        return updated_node


class DecoratorRemover(cst.CSTTransformer):
    def __init__(self, decorator_name: str):
        self.decorator_name = decorator_name

    def leave_Decorator(self, original_node: cst.Decorator, updated_node: cst.Decorator) -> Union[
        cst.Decorator, cst.RemovalSentinel]:
        if isinstance(original_node.decorator, cst.Call) and \
                isinstance(original_node.decorator.func, cst.Attribute) and \
                original_node.decorator.func.attr.value == self.decorator_name and \
                isinstance(original_node.decorator.func.value, cst.Attribute) and \
                original_node.decorator.func.value.attr.value == 'mark' and \
                isinstance(original_node.decorator.func.value.value, cst.Name) and \
                original_node.decorator.func.value.value.value == 'pytest':
            return cst.RemovalSentinel.REMOVE
        return updated_node


def update_tests(file: str,
                 mapped_tests: List[Tuple[str, int]],
                 all_tests: List[str],
                 decorator_name: str,
                 remove=False):
    with open(file, 'r') as f:
        source_code = f.read()

    tree = cst.parse_module(source_code)
    transform = DecoratorUpdater(mapped_tests, all_tests, decorator_name)
    if remove:
        transform = DecoratorRemover(decorator_name)
        tree = tree.visit(transform)
    else:
        transform = DecoratorUpdater(mapped_tests, all_tests, decorator_name)
        tree = tree.visit(transform)
    updated_source_code = tree.code

    with open(file, "w") as file:
        file.write(updated_source_code)