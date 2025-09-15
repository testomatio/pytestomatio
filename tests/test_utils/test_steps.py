from unittest.mock import patch, Mock

import pytest

from pytestomatio.utils.steps import Step, StepManager, _step_managers, StepContext, step, step_decorator, \
    get_step_manager


class TestStep:
    """Test for Step class"""

    def test_step_init(self):
        step = Step("Test Step")
        assert step.title == 'Test Step'
        assert step.category is None
        assert step.start_time is None
        assert step.end_time is None
        assert step.status is None
        assert step.error is None
        assert step.children == []

    def test_step_init_with_allowed_category(self):
        step = Step("Test Step", "system")
        assert step.title == 'Test Step'
        assert step.category == 'system'
        assert step.start_time is None
        assert step.end_time is None
        assert step.status is None
        assert step.error is None
        assert step.children == []

    def test_step_init_with_not_allowed_category(self):
        step = Step("Test Step", "New")
        assert step.title == 'Test Step'
        assert step.category is None
        assert step.start_time is None
        assert step.end_time is None
        assert step.status is None
        assert step.error is None
        assert step.children == []

    def test_step_duration_calculation(self):
        step = Step("Test Step")
        assert step.duration is None
        step.start_time = 1.0
        assert step.duration is None
        step.end_time = 2.5
        assert step.duration == 1.5

    def test_step_to_dict(self):
        step = Step("Test Step", 'system')
        step.status = "passed"
        step.start_time = 1.0
        step.end_time = 2.0

        child = Step('Nested step')
        child.status = 'failed'
        child.error = 'Test error'
        step.children.append(child)

        result = step.to_dict()
        expected = {
            "title": "Test Step",
            "category": 'system',
            "status": "passed",
            "duration": 1.0,
            "error": None,
            "steps": [
                {
                    "title": "Nested step",
                    "category": None,
                    "status": "failed",
                    "duration": None,
                    "error": "Test error",
                    "steps": []
                }
            ]
        }
        assert result == expected


class TestStepManager:

    @pytest.fixture
    def step_manager(self):
        return StepManager()

    def test_initial_state(self, step_manager):
        assert step_manager.root_steps == []
        assert step_manager._step_stack == []

    def test_start_root_step(self, step_manager):
        step = Step('Test Step')
        result = step_manager.start_step(step)

        assert result == step
        assert step.start_time is not None
        assert step in step_manager.root_steps
        assert step in step_manager._step_stack

    def test_start_nested_step(self, step_manager):
        root_step = Step('Root Step')
        nested_step = Step('Nested Step')
        step_manager.start_step(root_step)
        step_manager.start_step(nested_step)

        assert nested_step in root_step.children
        assert nested_step not in step_manager.root_steps
        assert nested_step in step_manager._step_stack

    def test_finish_step_success(self, step_manager):
        step = Step("Test step")
        step_manager.start_step(step)
        step_manager.finish_step(step)

        assert step.end_time is not None
        assert step.status == "passed"
        assert step.error is None
        assert step not in step_manager._step_stack

    def test_finish_step_with_exception(self, step_manager):
        step = Step("Test step")
        step_manager.start_step(step)

        exc = ValueError("Test error")
        step_manager.finish_step(step, ValueError, exc)

        assert step.status == "failed"
        assert step.error == "Test error"

    def test_finish_step_with_failed_children(self, step_manager):
        parent = Step("Parent step")
        child = Step("Child step")

        step_manager.start_step(parent)
        step_manager.start_step(child)

        step_manager.finish_step(child, ValueError, ValueError("Child error"))
        step_manager.finish_step(parent)

        assert parent.status == "failed"
        assert "Child step failed: Child step" in parent.error

    def test_get_current_step(self, step_manager):
        assert step_manager._get_current_step() is None

        step1 = Step("Step 1")
        step2 = Step("Step 2")

        step_manager.start_step(step1)
        assert step_manager._get_current_step() == step1

        step_manager.start_step(step2)
        assert step_manager._get_current_step() == step2

        step_manager.finish_step(step2)
        assert step_manager._get_current_step() == step1

        step_manager.finish_step(step1)
        assert step_manager._get_current_step() is None

    def test_get_steps_without_nested_steps(self, step_manager):
        step = Step("Step")
        step_manager.start_step(step)
        step_manager.finish_step(step)

        steps = step_manager.get_steps()
        assert steps
        assert len(steps) == 1
        assert steps[0].get('title') == step.title

    def test_get_steps_with_nested_steps(self, step_manager):
        root_step = Step("Root Step")
        step_manager.start_step(root_step)
        nested_step = Step("Nested Step")
        step_manager.start_step(nested_step)
        step_manager.finish_step(nested_step)
        step_manager.finish_step(root_step)

        steps = step_manager.get_steps()
        assert steps
        assert len(steps) == 1
        assert steps[0].get('title') == root_step.title

        nested_steps = steps[0].get('steps')
        assert nested_steps
        assert nested_steps[0].get('title') == nested_step.title


class TestStepContext:

    # def setup_method(self):
    #     # Очищаем глобальный state
    #     _managers.clear()

    @patch('pytestomatio.utils.steps.get_step_manager')
    def test_context_manager_success(self, mock_get_manager):
        mock_manager = Mock(spec=StepManager)
        mock_get_manager.return_value = mock_manager

        with StepContext("Test step"):
            pass

        assert mock_manager.start_step.call_count == 1
        assert mock_manager.finish_step.call_count == 1

        start_args = mock_manager.start_step.call_args[0]
        step = start_args[0]
        assert step.title == "Test step"

        finish_args = mock_manager.finish_step.call_args[0]
        assert finish_args[0] == step
        assert finish_args[1] is None  # exc_type
        assert finish_args[2] is None  # exc_val

    @patch('pytestomatio.utils.steps.get_step_manager')
    def test_context_manager_with_exception(self, mock_get_manager):
        mock_manager = Mock(spec=StepManager)
        mock_get_manager.return_value = mock_manager

        with pytest.raises(ValueError, match="Test error"):
            with StepContext("Test step"):
                raise ValueError("Test error")

        finish_args = mock_manager.finish_step.call_args[0]
        assert finish_args[1] == ValueError  # exc_type
        assert str(finish_args[2]) == "Test error"  # exc_val

    class TestStepFunction:

        @patch('pytestomatio.utils.steps.get_step_manager')
        def test_step_returns_context(self, mock_get_manager):
            mock_manager = Mock(spec=StepManager)
            mock_get_manager.return_value = mock_manager

            result = step("Test step")
            assert isinstance(result, StepContext)
            assert result.step.title == "Test step"


class TestStepDecorator:

    @patch('pytestomatio.utils.steps.get_step_manager')
    def test_decorator_success(self, mock_get_manager):
        mock_manager = Mock(spec=StepManager)
        mock_get_manager.return_value = mock_manager

        @step_decorator("Decorated step")
        def test_function():
            return "result"

        result = test_function()

        assert result == "result"
        assert mock_manager.start_step.call_count == 1
        assert mock_manager.finish_step.call_count == 1

        step_obj = mock_manager.start_step.call_args[0][0]
        assert step_obj.title == "Decorated step"

    @patch('pytestomatio.utils.steps.get_step_manager')
    def test_decorator_with_exception(self, mock_get_manager):
        mock_manager = Mock(spec=StepManager)
        mock_get_manager.return_value = mock_manager

        @step_decorator("Failing step")
        def failing_function():
            raise RuntimeError("Function failed")

        with pytest.raises(RuntimeError, match="Function failed"):
            failing_function()

        finish_call = mock_manager.finish_step.call_args[0]
        assert finish_call[1] == RuntimeError
        assert str(finish_call[2]) == "Function failed"

    def test_decorator_preserves_metadata(self):
        @step_decorator("Test step")
        def original_function():
            """Original docstring"""
            pass

        assert original_function.__name__ == "original_function"
        assert original_function.__doc__ == "Original docstring"


    class TestGetStepManager:

        def setup_method(self):
            _step_managers.clear()

        @patch('pytest._current_item')
        def test_get_manager_with_pytest_item(self, mock_item):
            mock_item.nodeid = "test_file.py::test_function"

            manager1 = get_step_manager()
            manager2 = get_step_manager()

            assert isinstance(manager1, StepManager)
            assert manager1 is manager2
            assert "test_file.py::test_function" in _step_managers

        def test_get_manager_without_pytest_item(self):
            with patch('pytest._current_item') as item:
                item.return_value = None
                manager = get_step_manager()
                assert isinstance(manager, StepManager)


