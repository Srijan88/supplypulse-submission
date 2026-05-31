from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class AuditLoggingPlugin:
    """
    Shared SupplyPulse audit logging plugin.

    Purpose:
    - Track every important agent step.
    - Keep logs structured.
    - Support pipeline-level traceability using conversation_id, session_id, run_id, and thread_id.
    """

    def __init__(
        self,
        default_agent_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        run_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.default_agent_name = default_agent_name
        self.conversation_id = conversation_id or f"conv_{uuid4().hex[:12]}"
        self.session_id = session_id or f"session_{uuid4().hex[:12]}"
        self.run_id = run_id or f"run_{uuid4().hex[:12]}"
        self.thread_id = thread_id or f"thread_{uuid4().hex[:12]}"
        self.model_name = model_name

        self._logs: List[Dict[str, Any]] = []
        self._sequence_number = 0

    @staticmethod
    def create_context(model_name: Optional[str] = None) -> Dict[str, Optional[str]]:
        """
        Creates one shared audit context for a full pipeline run.

        This is useful when Router, Scheduler, Report Builder, and future risk agents
        should all share the same conversation/session/run identifiers.
        """
        return {
            "conversation_id": f"conv_{uuid4().hex[:12]}",
            "session_id": f"session_{uuid4().hex[:12]}",
            "run_id": f"run_{uuid4().hex[:12]}",
            "thread_id": f"thread_{uuid4().hex[:12]}",
            "model_name": model_name,
        }

    def set_context(
        self,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        run_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        if conversation_id:
            self.conversation_id = conversation_id

        if session_id:
            self.session_id = session_id

        if run_id:
            self.run_id = run_id

        if thread_id:
            self.thread_id = thread_id

        if model_name:
            self.model_name = model_name

    def get_context(self) -> Dict[str, Optional[str]]:
        return {
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "thread_id": self.thread_id,
            "model_name": self.model_name,
        }

    def log(
        self,
        agent_name: Optional[str] = None,
        stage: str = "",
        thought_content: str = "",
        stage_output: Optional[Any] = None,
        agent_output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._sequence_number += 1

        resolved_agent_name = agent_name or self.default_agent_name or "UNKNOWN_AGENT"

        self._logs.append(
            {
                "log_id": f"log_{uuid4().hex[:12]}",
                "conversation_id": self.conversation_id,
                "session_id": self.session_id,
                "run_id": self.run_id,
                "thread_id": self.thread_id,
                "sequence_number": self._sequence_number,
                "agent_name": resolved_agent_name,
                "model_name": self.model_name,
                "thinking_stage": stage,
                "thought_content": thought_content,
                "thinking_stage_output": stage_output,
                "agent_output": agent_output,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
        )

    def get_logs(self) -> List[Dict[str, Any]]:
        return self._logs

    def clear(self) -> None:
        self._logs = []
        self._sequence_number = 0