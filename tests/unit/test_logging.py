import json
import logging
import sys

import pytest

from education_erp.logging import JsonFormatter, redact, sanitize_text


def test_redact_nested_sensitive_fields() -> None:
    payload = {"user": "safe", "authorization": "Bearer value", "nested": {"token": "x"}}
    assert redact(payload) == {
        "user": "safe",
        "authorization": "[REDACTED]",
        "nested": {"token": "[REDACTED]"},
    }


def test_json_formatter_emits_structured_record() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
    record.request_id = "request-1"
    result = json.loads(JsonFormatter().format(record))
    assert result["message"] == "hello"
    assert result["request_id"] == "request-1"
    assert result["level"] == "INFO"


@pytest.mark.parametrize(
    ("unsafe", "secret"),
    [
        ("password=plain-secret", "plain-secret"),
        ("Authorization: Bearer abc.def.ghi", "abc.def.ghi"),
        ("postgresql+psycopg://user:database-secret@db/app", "database-secret"),
        ("api_key = key-value", "key-value"),
    ],
)
def test_sanitize_text_removes_common_secret_forms(unsafe: str, secret: str) -> None:
    assert secret not in sanitize_text(unsafe)


def test_json_formatter_sanitizes_message_and_exception() -> None:
    try:
        raise RuntimeError("token=exception-secret")
    except RuntimeError:
        record = logging.LogRecord(
            "test",
            logging.ERROR,
            __file__,
            1,
            "password=message-secret",
            (),
            sys.exc_info(),
        )
    result = json.loads(JsonFormatter().format(record))
    assert "message-secret" not in result["message"]
    assert "exception-secret" not in result["exception"]
