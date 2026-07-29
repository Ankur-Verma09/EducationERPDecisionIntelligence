from uuid import UUID

from education_erp.middleware import valid_request_id


def test_valid_request_id_preserves_uuid() -> None:
    value = "c7ea2964-554f-4eed-98cc-49c1fdc41926"
    assert valid_request_id(value) == value


def test_invalid_request_id_is_replaced() -> None:
    generated = valid_request_id("bad\r\nheader")
    assert generated != "bad\r\nheader"
    assert str(UUID(generated)) == generated
