import json
from pathlib import Path
from typing import Dict, List, Optional

from agentic_builder.common.types import AgentType, Task
from agentic_builder.common.utils import get_project_root


class TaskManager:
    def __init__(self):
        self._cache: Dict[str, Task] = {}

    @property
    def task_dir(self) -> Path:
        return get_project_root() / ".tasks"

    def _get_path(self, task_id: str) -> Path:
        return self.task_dir / f"{task_id}.json"

    def create_task(self, description: str, agent_type: AgentType, dependencies: List[str] = None) -> Task:
        if not self.task_dir.exists():
            self.task_dir.mkdir(parents=True, exist_ok=True)

        # Determine ID based on existing count (simplified) usually we scan dir
        # For concurrency safety usually we use random or a lock.
        # Requirement says TASK-0001. I'll use a simple counter based on file count for now...
        # ...or random to avoid race in this basic impl.
        # Actually random hex is safer for MVP, but req said TASK-0001.
        # I'll stick to random suffix for safety unless strict seq is needed.
        # Let's try to do sequential if possible, scanning dir.
        existing = list(self.task_dir.glob("TASK-*.json"))
        next_num = len(existing) + 1
        task_id = f"TASK-{next_num:04d}"

        task = Task(id=task_id, description=description, agent_type=agent_type, dependencies=dependencies or [])
        self.save_task(task)
        return task

    def save_task(self, task: Task):
        if not self.task_dir.exists():
            self.task_dir.mkdir(parents=True, exist_ok=True)

        self._cache[task.id] = task
        with open(self._get_path(task.id), "w") as f:
            f.write(task.model_dump_json(indent=2))

    def get_task(self, task_id: str) -> Optional[Task]:
        if task_id in self._cache:
            return self._cache[task_id]

        path = self._get_path(task_id)
        if not path.exists():
            return None

        with open(path, "r") as f:
            data = json.load(f)
            task = Task(**data)
            self._cache[task_id] = task
            return task

    def get_dependencies(self, task_id: str) -> List[Task]:
        task = self.get_task(task_id)
        if not task:
            return []

        deps = []
        for dep_id in task.dependencies:
            dt = self.get_task(dep_id)
            if dt:
                deps.append(dt)
        return deps
