import logging
from pathlib import Path
from typing import Dict

from agentic_builder.agents.configs import get_agent_config, get_agent_prompt
from agentic_builder.common.events import EventEmitter
from agentic_builder.common.logging_config import get_logger, log_separator, truncate_for_log
from agentic_builder.common.types import WorkflowStatus
from agentic_builder.common.utils import get_project_root
from agentic_builder.orchestration.session_manager import SessionManager
from agentic_builder.orchestration.workflows import WorkflowMapper
from agentic_builder.pms.context_serializer import ContextSerializer

# Module logger for debug output
debug_logger = get_logger(__name__)


class WorkflowEngine(EventEmitter):
    def __init__(self, session_manager: SessionManager, pms_manager, git_manager, claude_client, pr_manager):
        super().__init__()
        self.session_manager = session_manager
        self.pms = pms_manager
        self.git = git_manager
        self.claude = claude_client
        self.pr_manager = pr_manager
        self._active_runs: Dict[str, bool] = {}
        debug_logger.debug("WorkflowEngine initialized")

    def start_workflow(self, workflow_name: str) -> str:
        log_separator(debug_logger, f"STARTING WORKFLOW: {workflow_name}")
        debug_logger.debug(f"Workflow Name: {workflow_name}")

        session = self.session_manager.create_session(workflow_name)
        debug_logger.debug(f"Session created: {session.id}")

        self.session_manager.update_status(session.id, WorkflowStatus.RUNNING)
        self._active_runs[session.id] = True
        self.emit("workflow_started", session.id)

        # Create git branch
        branch_name = f"feature/{session.id}"
        debug_logger.debug(f"Creating git branch: {branch_name}")
        try:
            self.git.create_branch(branch_name)
            debug_logger.debug(f"Git branch created: {branch_name}")
        except Exception as e:
            debug_logger.debug(f"Failed to create branch (may already exist): {e}")
            # Maybe branch exists, try to checkout
            try:
                self.git.checkout_branch(branch_name)
                debug_logger.debug(f"Checked out existing branch: {branch_name}")
            except Exception as e:
                # If we can't switch to the branch, we shouldn't proceed
                # as we might pollute the wrong branch.
                debug_logger.error(f"Failed to create or switch to branch {branch_name}: {e}")
                raise Exception(f"Failed to create or switch to branch {branch_name}: {e}")

        try:
            self.run_loop(session.id)
        except Exception as e:
            debug_logger.error(f"Workflow failed with exception: {e}")
            self.session_manager.update_status(session.id, WorkflowStatus.FAILED)
            self.emit("workflow_failed", {"id": session.id, "error": str(e)})
            raise e

        debug_logger.debug(f"Workflow completed successfully: {session.id}")
        return session.id

    def run_loop(self, session_id: str):
        log_separator(debug_logger, f"RUN LOOP: {session_id}")
        session = self.session_manager.load_session(session_id)
        debug_logger.debug(f"Loaded session: workflow={session.workflow_name}, status={session.status}")

        # Setup logging
        log_file = self.session_manager.session_dir / f"{session_id}.log"
        debug_logger.debug(f"Session log file: {log_file}")

        # Avoid clobbering global logging config by attaching handler directly to this logger
        logger = logging.getLogger(session_id)
        logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates if reused
        if logger.hasHandlers():
            logger.handlers.clear()

        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"Starting workflow loop for {session_id}")
        debug_logger.debug(f"Session logger configured, starting workflow loop")

        # Determine execution order based on workflow name
        try:
            execution_order = WorkflowMapper.get_execution_order(session.workflow_name)
            debug_logger.debug(f"Execution order for {session.workflow_name}: {[a.value for a in execution_order]}")
        except Exception as e:
            debug_logger.warning(f"Failed to get execution order for {session.workflow_name}: {e}")
            # Fallback to full generation if mapping fails or handle error
            execution_order = WorkflowMapper.get_execution_order("FULL_APP_GENERATION")
            debug_logger.debug(f"Falling back to FULL_APP_GENERATION execution order")

        # Resume logic: skip completed agents
        completed_agents = set()
        # Map AgentType -> TaskID for dependency resolution
        agent_task_map = {}

        for task_id in session.completed_tasks:
            t = self.pms.get_task(task_id)
            if t:
                completed_agents.add(t.agent_type)
                agent_task_map[t.agent_type] = task_id

        debug_logger.debug(f"Already completed agents: {[a.value for a in completed_agents]}")
        debug_logger.debug(f"Agent-Task mapping: {[(a.value, t) for a, t in agent_task_map.items()]}")

        for agent_type in execution_order:
            if session_id not in self._active_runs:
                debug_logger.debug(f"Session {session_id} cancelled, stopping execution loop")
                break  # Cancelled

            if agent_type in completed_agents:
                debug_logger.debug(f"Skipping already completed agent: {agent_type.value}")
                continue

            log_separator(debug_logger, f"EXECUTING AGENT: {agent_type.value}")
            config = get_agent_config(agent_type)
            debug_logger.debug(f"Agent config: model_tier={config.model_tier}, dependencies={[d.value for d in config.dependencies]}")

            # 1. Create PMS Task
            # Resolve dependencies task IDs
            deps_ids = []
            for dep_agent in config.dependencies:
                # Look for the task ID corresponding to this dependent agent in the current session
                if dep_agent in agent_task_map:
                    deps_ids.append(agent_task_map[dep_agent])

            debug_logger.debug(f"Resolved dependency task IDs: {deps_ids}")

            task = self.pms.create_task(
                description=f"Execute {agent_type.value} phase",
                agent_type=agent_type,
                dependencies=deps_ids,
            )
            debug_logger.debug(f"Created task: {task.id} for agent {agent_type.value}")

            self.emit("agent_spawned", {"agent": agent_type, "task_id": task.id})
            logger.info(f"Spawned agent {agent_type} (Task {task.id})")

            # 2. Serialize Context
            # Gather outputs from dependency tasks (summary, next_steps, warnings, file paths)
            debug_logger.debug(f"Gathering dependency task outputs...")
            dep_tasks = {}
            for dep_id in task.dependencies:
                dep_task = self.pms.get_task(dep_id)
                if dep_task:
                    dep_tasks[dep_id] = dep_task
                    debug_logger.debug(f"  Dep task {dep_id}: agent={dep_task.agent_type.value}, files={len(dep_task.context_files)}")

            # Serialize context including full agent outputs from dependencies
            context_xml = ContextSerializer.serialize(task, dep_tasks)
            debug_logger.debug(f"Serialized context XML length: {len(context_xml)} characters")
            debug_logger.debug(f"Context XML preview:\n{truncate_for_log(context_xml, max_length=2000)}")

            # 3. Call Claude
            # Pass the task description as the prompt (-p)
            prompt = task.description
            debug_logger.debug(f"Calling Claude with prompt: {prompt}")

            response = self.claude.call_agent(
                agent_type=agent_type, prompt=prompt, user_input=context_xml, model=config.model_tier
            )
            debug_logger.debug(f"Received response from Claude: success={response.success}")

            # 4. Handle Response
            # Agents write files directly to disk - we just track what was created/modified
            if response.success:
                debug_logger.debug(f"Processing successful response for agent {agent_type.value}")
                created_files = []
                # Use project root (where .git is) not CWD which may be different
                root_path = get_project_root().resolve()
                debug_logger.debug(f"Project root path: {root_path}")

                debug_logger.debug(f"Processing {len(response.artifacts)} artifacts...")
                for artifact in response.artifacts:
                    if artifact.type == "file" and artifact.path:
                        # New format: agent already wrote file, we just validate and track
                        # Resolve path relative to project root, not CWD
                        artifact_path = Path(artifact.path)
                        if artifact_path.is_absolute():
                            fpath = artifact_path.resolve()
                        else:
                            fpath = (root_path / artifact_path).resolve()

                        debug_logger.debug(f"  Checking artifact: {artifact.path} -> {fpath}")

                        if not fpath.is_relative_to(root_path):
                            logger.error(f"Security: Agent reported file outside repo: {fpath}")
                            debug_logger.error(f"SECURITY: Path traversal attempt: {fpath}")
                            continue

                        # Verify file exists (agent should have created it)
                        if fpath.exists():
                            created_files.append(str(fpath))
                            logger.info(f"Agent {artifact.action or 'created'} file: {fpath}")
                            debug_logger.debug(f"  File verified: {fpath}")
                        else:
                            logger.warning(f"Agent reported file but it doesn't exist: {fpath}")
                            debug_logger.warning(f"  File not found: {fpath}")

                    elif artifact.type == "file" and artifact.content:
                        # Legacy fallback: write content if provided (backwards compatibility)
                        debug_logger.debug(f"  Processing legacy artifact with content: {artifact.name}")
                        artifact_path = Path(artifact.name)
                        if artifact_path.is_absolute():
                            fpath = artifact_path.resolve()
                        else:
                            fpath = (root_path / artifact_path).resolve()

                        if not fpath.is_relative_to(root_path):
                            logger.error(f"Security: Attempted path traversal write to {fpath}")
                            debug_logger.error(f"SECURITY: Path traversal attempt: {fpath}")
                            continue

                        if fpath.parent:
                            fpath.parent.mkdir(parents=True, exist_ok=True)
                        fpath.write_text(artifact.content)
                        created_files.append(str(fpath))
                        debug_logger.debug(f"  Wrote legacy file: {fpath} ({len(artifact.content)} chars)")

                debug_logger.debug(f"Total files created/modified: {len(created_files)}")
                for f in created_files:
                    debug_logger.debug(f"  - {f}")

                # Update task with created files and agent output so next agents can see them
                task.context_files = created_files
                task.output_summary = response.summary
                task.output_next_steps = response.next_steps
                task.output_warnings = response.warnings
                task.status = "completed"
                self.pms.save_task(task)
                debug_logger.debug(f"Task {task.id} updated and saved")

                session.completed_tasks.append(task.id)
                session.total_tokens += response.metadata.get("tokensUsed", 0)
                debug_logger.debug(f"Session tokens: {session.total_tokens}")

                # Update local map for subsequent agents in this loop
                completed_agents.add(agent_type)
                agent_task_map[agent_type] = task.id

                self.session_manager.save_session(session)
                debug_logger.debug(f"Session saved")

                # Commit
                if created_files:
                    commit_msg = f"[{agent_type.value}] {response.summary[:50]}"
                    debug_logger.debug(f"Committing files with message: {commit_msg}")
                    self.git.commit_files(created_files, commit_msg)
                    debug_logger.debug(f"Git commit completed")

                self.emit("agent_completed", {"agent": agent_type, "summary": response.summary})
                logger.info(f"Agent {agent_type} completed.")
                debug_logger.debug(f"Agent {agent_type.value} completed successfully")
            else:
                debug_logger.error(f"Agent {agent_type.value} failed: {response.summary}")
                self.emit("agent_failed", {"agent": agent_type, "error": response.summary})
                logger.error(f"Agent {agent_type} failed: {response.summary}")
                raise Exception(f"Agent {agent_type} failed: {response.summary}")

        # Finish
        log_separator(debug_logger, "WORKFLOW FINISHING")
        if session_id in self._active_runs:
            debug_logger.debug(f"Marking workflow {session_id} as completed")
            self.session_manager.update_status(session.id, WorkflowStatus.COMPLETED)
            del self._active_runs[session_id]

            # Create PR
            pr_branch = f"feature/{session.id}"
            pr_title = f"Workflow {session.workflow_name}"
            debug_logger.debug(f"Creating PR: branch={pr_branch}, title={pr_title}")
            self.pr_manager.create_pr(
                branch=pr_branch,
                title=pr_title,
                body="Generated by Agentic Mobile App Builder",
            )
            debug_logger.debug(f"PR created successfully")
            self.emit("workflow_completed", session.id)
            debug_logger.debug(f"Workflow {session_id} completed event emitted")
        else:
            debug_logger.debug(f"Session {session_id} was cancelled, skipping completion")

    def get_run(self, run_id: str):
        return self._active_runs.get(run_id)

    def cancel_workflow(self, run_id: str):
        if run_id in self._active_runs:
            del self._active_runs[run_id]
        self.session_manager.update_status(run_id, WorkflowStatus.CANCELLED)
