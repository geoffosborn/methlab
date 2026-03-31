"""Standard health endpoint helper."""

import subprocess
import time

_start_time = time.time()
_git_sha: str | None = None


def get_git_sha() -> str:
    global _git_sha
    if _git_sha is None:
        try:
            _git_sha = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            ).strip()
        except Exception:
            _git_sha = "unknown"
    return _git_sha


def health_response(app_name: str, **extra: object) -> dict:
    return {
        "status": "healthy",
        "app": app_name,
        "version": get_git_sha(),
        "uptime": int(time.time() - _start_time),
        **extra,
    }
