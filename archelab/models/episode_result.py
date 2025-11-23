from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional, Union, Literal


AttackType = Literal[
    "secret_leak",
    "backdoor",
    "prompt_injection",
    "social_engineering",
    "other",
]


@dataclass
class EpisodeResult:
    """Structured summary of a single experiment episode.

    This is the schema that will be used for CSV / JSON output and later
    evaluation. It is intentionally framework-agnostic so that different
    MAS engines can be compared.
    """

    episode_id: str
    framework: str                 # e.g. kiro / autogen / chatdev / metagpt / a2a / mcp / minimal_two_agent
    topology: str                  # e.g. star / chain / mesh / hybrid / custom
    task_id: str
    task_type: str                 # e.g. coding / planning / qa / multistep
    input_context: Union[str, Any]
    expected_output: Union[str, Any]
    worker_output: Union[str, Any]
    task_success: bool
    attack_success: bool
    attack_type: Optional[AttackType]
    contains_secret_in_msg: bool
    unauthorized_write: Optional[bool]
    steps: int
    defense_enabled: bool = False
    defense_profile: str | None = None
    defense_summary: Dict[str, int] = field(default_factory=dict)
    episode_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the episode result."""
        return asdict(self)
