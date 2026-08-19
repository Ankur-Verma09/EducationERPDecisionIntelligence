"""Authenticated principal representations."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TokenPrincipal:
    """Claims trusted only after cryptographic token validation."""

    issuer: str
    subject: str
    audience: str
    issued_at: datetime
    expires_at: datetime
    token_id: str | None
    assurance_methods: frozenset[str]

    def has_mfa(self, approved_methods: tuple[str, ...]) -> bool:
        """Return whether the token carries an approved MFA method."""

        return bool(self.assurance_methods.intersection(approved_methods))
