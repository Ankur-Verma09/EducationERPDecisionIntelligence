"""Fail-closed OIDC JWT access-token validation."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient

from education_erp.config import Settings
from education_erp.identity.principal import TokenPrincipal


class AuthenticationError(ValueError):
    """Raised when access-token validation fails."""


class TokenVerifier(Protocol):
    """Replaceable access-token verifier contract."""

    def verify(self, token: str) -> TokenPrincipal:
        """Validate a token and return trusted claims."""


def _claim_timestamp(claims: Mapping[str, Any], name: str) -> datetime:
    value = claims.get(name)
    if not isinstance(value, int | float):
        raise AuthenticationError(f"required token claim is invalid: {name}")
    return datetime.fromtimestamp(value, UTC)


class OidcJwtVerifier:
    """Validate asymmetric JWTs using the configured issuer's JWKS."""

    def __init__(self, settings: Settings) -> None:
        if not settings.oidc_issuer_url or not settings.oidc_audience:
            raise ValueError("OIDC issuer and audience are required")
        if any(
            algorithm == "none" or algorithm.startswith("HS")
            for algorithm in settings.oidc_algorithms
        ):
            raise ValueError("only approved asymmetric JWT algorithms are allowed")
        self._issuer = settings.oidc_issuer_url.rstrip("/")
        self._audience = settings.oidc_audience
        self._algorithms = settings.oidc_algorithms
        self._clock_skew = settings.oidc_clock_skew_seconds
        self._jwks = PyJWKClient(
            f"{self._issuer}/.well-known/jwks.json",
            cache_jwk_set=True,
            lifespan=settings.oidc_jwks_cache_seconds,
        )

    def verify(self, token: str) -> TokenPrincipal:
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self._algorithms),
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._clock_skew,
                options={"require": ["iss", "sub", "aud", "exp", "iat"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("access token is invalid") from exc

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthenticationError("required token claim is invalid: sub")
        raw_amr = claims.get("amr", [])
        if isinstance(raw_amr, str):
            raw_amr = [raw_amr]
        if not isinstance(raw_amr, list) or not all(isinstance(item, str) for item in raw_amr):
            raise AuthenticationError("token assurance claim is invalid")
        return TokenPrincipal(
            issuer=self._issuer,
            subject=subject,
            audience=self._audience,
            issued_at=_claim_timestamp(claims, "iat"),
            expires_at=_claim_timestamp(claims, "exp"),
            token_id=claims.get("jti") if isinstance(claims.get("jti"), str) else None,
            assurance_methods=frozenset(raw_amr),
        )
