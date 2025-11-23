from unittest.mock import patch

import pytest

from agentic_builder.common.types import AgentType, Task
from agentic_builder.pms.context_serializer import ContextSerializer
from agentic_builder.pms.task_manager import TaskManager


@pytest.fixture
def task_manager(tmp_path):
    with patch("agentic_builder.pms.task_manager.get_project_root", return_value=tmp_path):
        yield TaskManager()


def test_create_task(task_manager):
    task = task_manager.create_task(description="Test task", agent_type=AgentType.PM)
    assert task.id.startswith("TASK-")
    assert task.status == "pending"

    loaded = task_manager.get_task(task.id)
    assert loaded.description == "Test task"


def test_dependency_resolution(task_manager):
    t1 = task_manager.create_task("Root", AgentType.PM)
    t2 = task_manager.create_task("Child", AgentType.ARCHITECT, dependencies=[t1.id])

    assert t1.id in t2.dependencies

    # Check if we can traverse (simple check)
    deps = task_manager.get_dependencies(t2.id)
    assert len(deps) == 1
    assert deps[0].id == t1.id


def test_context_serializer():
    task = Task(id="TASK-001", description="Do something", agent_type=AgentType.PM, dependencies=[])
    xml = ContextSerializer.serialize(task, dependency_outputs={})

    assert "<task_context>" in xml
    assert "<task_id>TASK-001</task_id>" in xml
    assert "Do something" in xml
