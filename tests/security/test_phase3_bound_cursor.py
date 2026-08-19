import pytest

from education_erp.api.phase2_controls import (
    decode_bound_cursor,
    encode_bound_cursor,
)
from education_erp.errors import ApiError


def test_phase3_cursor_is_signed_and_bound_to_tenant_and_collection() -> None:
    cursor = encode_bound_cursor(
        "00000000-0000-4000-8000-000000000001",
        tenant_id="tenant-a",
        collection="learners",
    )
    assert (
        decode_bound_cursor(
            cursor,
            tenant_id="tenant-a",
            collection="learners",
        )
        == "00000000-0000-4000-8000-000000000001"
    )

    for invalid, tenant, collection in (
        (
            cursor[:-1] + ("0" if cursor[-1] != "0" else "1"),
            "tenant-a",
            "learners",
        ),
        (cursor, "tenant-b", "learners"),
        (cursor, "tenant-a", "courses"),
    ):
        with pytest.raises(ApiError) as error:
            decode_bound_cursor(
                invalid,
                tenant_id=tenant,
                collection=collection,
            )
        assert error.value.code == "invalid_cursor"
