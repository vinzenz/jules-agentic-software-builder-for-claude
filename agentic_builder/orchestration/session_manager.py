import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from agentic_builder.common.types import SessionData, WorkflowStatus
from agentic_builder.common.utils import get_project_root


class SessionManager:
    def __init__(self):
        self._cache: Dict[str, SessionData] = {}

    @property
    def session_dir(self) -> Path:
        return get_project_root() / ".sessions"

    def _get_path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.json"

    def create_session(self, workflow_name: str) -> SessionData:
        if not self.session_dir.exists():
            self.session_dir.mkdir(parents=True, exist_ok=True)

        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        session = SessionData(id=session_id, workflow_name=workflow_name, status=WorkflowStatus.PENDING)
        self.save_session(session)
        return session

    def save_session(self, session: SessionData):
        if not self.session_dir.exists():
            self.session_dir.mkdir(parents=True, exist_ok=True)

        self._cache[session.id] = session
        with open(self._get_path(session.id), "w") as f:
            f.write(session.model_dump_json(indent=2))

    def load_session(self, session_id: str) -> Optional[SessionData]:
        if session_id in self._cache:
            return self._cache[session_id]

        path = self._get_path(session_id)
        if not path.exists():
            return None

        with open(path, "r") as f:
            data = json.load(f)
            session = SessionData(**data)
            self._cache[session_id] = session
            return session

    def update_status(self, session_id: str, status: WorkflowStatus):
        session = self.load_session(session_id)
        if session:
            session.status = status
            self.save_session(session)

    def list_sessions(self) -> List[SessionData]:
        if not self.session_dir.exists():
            return []
        sessions = []
        for f in self.session_dir.glob("*.json"):
            # Avoid full load if possible, but for now full load is fine
            try:
                s = self.load_session(f.stem)
                if s:
                    sessions.append(s)
            except Exception:
                pass  # corrupted file
        return sessions
