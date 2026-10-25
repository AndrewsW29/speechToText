"""OIDC/JWT validation (Keycloak JWKS). Auth can be disabled only via explicit settings."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Request

from app.adapters.inbound.rest.errors import ProblemError
from app.config import Settings


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    claims: dict[str, Any]


ANONYMOUS = Principal(subject="anonymous", claims={})


class JwtVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        key_resolver: Callable[[str], Any],
        algorithms: tuple[str, ...] = ("RS256", "ES256"),
    ) -> None:
        self._issuer = issuer
        self._audience = audience
        self._key_resolver = key_resolver
        self._algorithms = list(algorithms)

    def verify(self, token: str) -> Principal:
        try:
            key = self._key_resolver(token)
            claims = jwt.decode(
                token,
                key=key,
                algorithms=self._algorithms,
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise ProblemError(401, "Invalid or expired token") from exc
        return Principal(subject=str(claims["sub"]), claims=claims)


def jwks_verifier(settings: Settings) -> JwtVerifier:
    if not (settings.oidc_issuer and settings.oidc_jwks_url and settings.oidc_audience):
        raise RuntimeError("auth enabled but VA_OIDC_ISSUER/JWKS_URL/AUDIENCE are not set")
    client = jwt.PyJWKClient(settings.oidc_jwks_url)
    return JwtVerifier(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        key_resolver=lambda token: client.get_signing_key_from_jwt(token).key,
    )


async def require_principal(request: Request) -> Principal:
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return ANONYMOUS
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ProblemError(401, "Missing bearer token")
    verifier: JwtVerifier = request.app.state.verifier
    return verifier.verify(token)


def has_role(principal: Principal, role: str) -> bool:
    roles = principal.claims.get("realm_access", {}).get("roles", [])
    return role in roles


def require_role(role: str) -> Callable[[Request], Awaitable[Principal]]:
    async def dependency(request: Request) -> Principal:
        principal = await require_principal(request)
        settings: Settings = request.app.state.settings
        if settings.auth_enabled and not has_role(principal, role):
            raise ProblemError(403, "Forbidden", f"Requires the '{role}' role")
        return principal

    return dependency
