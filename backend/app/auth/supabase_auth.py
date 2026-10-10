"""
Compatibility shim — Supabase Auth has been removed.

This module previously housed SupabaseTokenVerifier. All JWT verification is
now handled by app.auth.security.verify_access_token using FastAPI-native
HS256 tokens minted by our own backend.

Imports of AuthenticatedUser from this module continue to work.
"""
from app.auth.security import AuthenticatedUser  # noqa: F401 — re-export for back-compat
