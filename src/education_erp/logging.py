"""Structured logging with conservative field redaction."""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "database_url",
        "password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
    }
)
SENSITIVE_TEXT_REPLACEMENTS = (
    (
        re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([a-z0-9._~+/=-]+)"),
        r"\1[REDACTED]",
    ),
    (re.compile(r"(?i)(bearer\s+)([a-z0-9._~+/=-]+)"), r"\1[REDACTED]"),
    (
        re.compile(r"(?i)(postgres(?:ql)?(?:\+\w+)?://[^:\s/]+:)([^@\s/]+)(@)"),
        r"\1[REDACTED]\3",
    ),
    (
        re.compile(
            r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|authorization)"
            r"(\s*[:=]\s*)([^\s,;]+)"
        ),
        r"\1\2[REDACTED]",
    ),
)


def sanitize_text(value: str) -> str:
    """Remove common credential forms from free-form messages and exceptions."""

    sanitized = value
    for pattern, replacement in SENSITIVE_TEXT_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def redact(value: Any) -> Any:
    """Recursively redact known credential fields before serialization."""

    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


class JsonFormatter(logging.Formatter):
    """Render log records as one-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_text(record.getMessage()),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = sanitize_text(self.formatException(record.exc_info))
        return json.dumps(redact(payload), ensure_ascii=False, separators=(",", ":"))


def configure_logging(level: str) -> None:
    """Configure root logging once for application startup."""

    handler = logging.StreamHandler()
    handler.name = "education_erp_json"
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    if not any(existing.name == handler.name for existing in root.handlers):
        root.addHandler(handler)
    root.setLevel(level)
