import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from agentic_builder.common.logging_config import get_logger
from agentic_builder.common.types import SessionData, WorkflowStatus
from agentic_builder.common.utils import get_project_root

# Module logger
logger = get_logger(__name__)


class SessionManager:
    def __init__(self):
        self._cache: Dict[str, SessionData] = {}
        logger.debug("SessionManager initialized")

    @property
    def session_dir(self) -> Path:
        return get_project_root() / ".sessions"

    def _get_path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.json"

    def create_session(self, workflow_name: str) -> SessionData:
        logger.debug(f"Creating new session for workflow: {workflow_name}")
        if not self.session_dir.exists():
            logger.debug(f"Creating session directory: {self.session_dir}")
            self.session_dir.mkdir(parents=True, exist_ok=True)

        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        session = SessionData(id=session_id, workflow_name=workflow_name, status=WorkflowStatus.PENDING)
        logger.debug(f"Created session: {session_id}")
        self.save_session(session)
        return session

    def save_session(self, session: SessionData):
        logger.debug(f"Saving session: {session.id} (status: {session.status})")
        if not self.session_dir.exists():
            self.session_dir.mkdir(parents=True, exist_ok=True)

        self._cache[session.id] = session
        path = self._get_path(session.id)
        with open(path, "w") as f:
            f.write(session.model_dump_json(indent=2))
        logger.debug(f"Session saved to: {path}")

    def load_session(self, session_id: str) -> Optional[SessionData]:
        logger.debug(f"Loading session: {session_id}")
        if session_id in self._cache:
            logger.debug(f"Session {session_id} found in cache")
            return self._cache[session_id]

        path = self._get_path(session_id)
        if not path.exists():
            logger.debug(f"Session file not found: {path}")
            return None

        logger.debug(f"Loading session from file: {path}")
        with open(path, "r") as f:
            data = json.load(f)
            session = SessionData(**data)
            self._cache[session_id] = session
            logger.debug(f"Session loaded: status={session.status}, completed_tasks={len(session.completed_tasks)}")
            return session

    def update_status(self, session_id: str, status: WorkflowStatus):
        logger.debug(f"Updating session {session_id} status to: {status}")
        session = self.load_session(session_id)
        if session:
            old_status = session.status
            session.status = status
            self.save_session(session)
            logger.debug(f"Session {session_id} status updated: {old_status} -> {status}")
        else:
            logger.warning(f"Cannot update status: session {session_id} not found")

    def list_sessions(self) -> List[SessionData]:
        logger.debug(f"Listing sessions from: {self.session_dir}")
        if not self.session_dir.exists():
            logger.debug("Session directory does not exist")
            return []
        sessions = []
        for f in self.session_dir.glob("*.json"):
            # Avoid full load if possible, but for now full load is fine
            try:
                s = self.load_session(f.stem)
                if s:
                    sessions.append(s)
            except Exception as e:
                logger.warning(f"Failed to load session from {f}: {e}")
        logger.debug(f"Found {len(sessions)} sessions")
        return sessions
