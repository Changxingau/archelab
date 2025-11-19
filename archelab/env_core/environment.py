import datetime
from typing import Any, Dict, List


def current_utc_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.datetime.utcnow().isoformat() + "Z"


class Environment:
    """
    Minimal environment wrapper for MAS experiments.

    This class abstracts file I/O and test execution so that all actions
    can be logged and replayed for later analysis. The actual file system
    and test runner integration is intentionally kept simple and can be
    extended as needed.
    """

    def __init__(self, repo_path: str, secret: str) -> None:
        self.repo_path: str = repo_path
        self.secret: str = secret
        self.events: List[Dict[str, Any]] = []

    def read_file(self, path: str) -> str:
        """Read file content from repo_path/path and log the event.

        In this minimal version we do not actually touch the file system.
        You can replace the stub with real I/O if desired.
        """
        # TODO: Replace this stub with real file reading if needed.
        content = f"<stubbed content for {path}>"

        self.events.append({
            "type": "read_file",
            "path": path,
            "timestamp": current_utc_iso(),
        })
        return content

    def write_file(self, path: str, content: str) -> None:
        """Write file content and log the event.

        In this minimal version we do not actually write to disk.
        You can replace the stub with real file writing if desired.
        """
        # TODO: Replace this stub with real file writing if needed.

        self.events.append({
            "type": "write_file",
            "path": path,
            "timestamp": current_utc_iso(),
        })

    def run_tests(self) -> bool:
        """Run tests for the current repo and log the event.

        In this minimal version, we always return True. You can integrate
        with pytest or another test runner later.
        """
        # TODO: Replace this stub with a real test runner.
        passed = True

        self.events.append({
            "type": "run_tests",
            "passed": passed,
            "timestamp": current_utc_iso(),
        })
        return passed

    def contains_secret(self, text: str) -> bool:
        """Check whether the secret token appears in the given text."""
        return self.secret in text
