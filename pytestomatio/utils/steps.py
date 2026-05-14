import functools
import time
import pytest

from typing import Dict, List


_step_managers = {}


class Step:
    step_categories = {'user', 'system', 'framework'}

    def __init__(self, title: str, category: str = None):
        self.title = title
        self.category = category if category in self.step_categories else None
        self.start_time = None
        self.end_time = None
        self.status = None
        self.error = None
        self.children = []

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time

    def to_dict(self) -> Dict:
        """Returns dict representation of Step"""
        return {
            "title": self.title,
            "category": self.category,
            "status": self.status,
            "duration": self.duration,
            "error": self.error,
            "steps": [child.to_dict() for child in self.children]
        }


class StepManager:
    def __init__(self):
        self.root_steps = []
        self._step_stack = []

    def _get_current_step(self) -> Step:
        return self._step_stack[-1] if self._step_stack else None

    def start_step(self, step: Step) -> Step:
        """Handles start of test step"""
        step.start_time = time.time()
        current_step = self._get_current_step()
        if current_step:
            current_step.children.append(step)
        else:
            self.root_steps.append(step)

        self._step_stack.append(step)
        return step

    def finish_step(self, step: Step, exc_type=None, exc_val=None, exc_tb=None):
        """Handles end of test step. Updates step end time, status and errors if step or nested steps are failed"""
        step.end_time = time.time()
        failed_children = [child for child in step.children if child.status == "failed"]
        if exc_type or failed_children:
            step.status = "failed"
            if exc_type:
                step.error = str(exc_val)
            elif failed_children:
                step.error = f'Child step failed: {failed_children[0].title}'
        else:
            step.status = "passed"

        if self._step_stack and self._step_stack[-1] == step:
            self._step_stack.pop()

    def get_steps(self) -> List[Dict]:
        """Returns list of steps in manager"""
        return [i.to_dict() for i in self.root_steps]


def get_step_manager() -> StepManager:
    """Returns StepManager for current Pytest Test Item"""
    item = getattr(pytest, '_current_item', None)
    item_id = item.nodeid if item else None

    if item_id not in _step_managers:
        _step_managers[item_id] = StepManager()
    return _step_managers[item_id]


class StepContext:
    def __init__(self, title: str, category: str = None):
        self.step = Step(title, category)
        self.manager = get_step_manager()

    def __enter__(self):
        self.manager.start_step(self.step)
        return self.step

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.finish_step(self.step, exc_type, exc_val, exc_tb)
        return False


def step(title: str, category: str = None):
    """Context manager for test step

    :param title: name of test step
    :param category: category of test step(user|framework|system)
    """
    return StepContext(title, category)


def step_decorator(title: str, category: str = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_step_manager()
            step_obj = Step(title, category)
            manager.start_step(step_obj)
            try:
                result = func(*args, **kwargs)
                manager.finish_step(step_obj)
                return result
            except Exception as e:
                manager.finish_step(step_obj, type(e), e)
                raise
        return wrapper
    return decorator


def step_function(title: str, category: str = None):
    """Decorator for test step

    :param title: name of test step
    :param category: category of test step(user|framework|system)
    """
    return step_decorator(title, category)
