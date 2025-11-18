import datetime
from typing import Any, Dict, List


def current_utc_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.datetime.utcnow().isoformat() + "Z"


class EpisodeRecorder:
    """
    Recorder for a single MAS experiment episode.

    It stores:
    - high level meta information (task, config, etc.)
    - message logs between agents
    - environment/tool events
    """

    def __init__(self, episode_id: str, framework: str, topology: str) -> None:
        self.episode_id: str = episode_id
        self.framework: str = framework
        self.topology: str = topology
        self.messages: List[Dict[str, Any]] = []
        self.tool_events: List[Dict[str, Any]] = []
        self.meta: Dict[str, Any] = {}

    def log_message(self, step: int, sender: str, receiver: str, content: str) -> None:
        """Append a message record to the trace."""
        self.messages.append({
            "step": step,
            "sender": sender,
            "receiver": receiver,
            "content": content,
            "timestamp": current_utc_iso(),
        })

    def log_tool_event(
        self,
        step: int,
        agent: str,
        tool: str,
        args: Dict[str, Any],
        result_summary: str = ""
    ) -> None:
        """Append a tool event record to the trace."""
        self.tool_events.append({
            "step": step,
            "agent": agent,
            "tool": tool,
            "args": args,
            "result_summary": result_summary,
            "timestamp": current_utc_iso(),
        })

    def set_meta(self, key: str, value: Any) -> None:
        """Set a meta field for this episode."""
        self.meta[key] = value

    def to_trace_json(self) -> Dict[str, Any]:
        """Return the full episode trace as a JSON-compatible dict."""
        return {
            "episode_id": self.episode_id,
            "framework": self.framework,
            "topology": self.topology,
            "meta": self.meta,
            "messages": self.messages,
            "tool_events": self.tool_events,
        }
