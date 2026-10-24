"""
Endpoint management and secure enrollment service for ForenX Remote Forensics.
Implements one-time short-lived enrollment tokens, device identity exchange,
revocation, and audit logging.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import List, Optional

from forenx.database import get_db_connection
from forenx.exceptions import SecurityViolationError
from forenx.models import Endpoint, EnrollmentToken, generate_id, utc_now_iso
from forenx.audit import log_audit


def generate_enrollment_token(
    device_label: str,
    operating_system: str = "linux",
    created_by: str = "Examiner",
    expiry_minutes: int = 60
) -> EnrollmentToken:
    """Generate a cryptographically secure, short-lived, one-time enrollment token."""
    token_str = secrets.token_hex(24)
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=expiry_minutes)

    token_obj = EnrollmentToken(
        token=token_str,
        device_label=device_label.strip(),
        operating_system=operating_system.lower().strip(),
        created_at=now.isoformat(),
        expires_at=expires.isoformat(),
        used=False,
        created_by=created_by
    )

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO enrollment_tokens (
                    token, device_label, operating_system, created_at, expires_at, used, created_by
                ) VALUES (?, ?, ?, ?, ?, 0, ?);
                """,
                (token_obj.token, token_obj.device_label, token_obj.operating_system,
                 token_obj.created_at, token_obj.expires_at, token_obj.created_by)
            )
            log_audit(
                operation="enrollment_token_generated",
                outcome="success",
                details=f"Generated one-time token for endpoint '{device_label}' (expires in {expiry_minutes}m)",
                conn=conn
            )
        return token_obj
    finally:
        conn.close()


def enroll_endpoint(
    token: str,
    certificate_identity: str = "",
    ip_address: str = "127.0.0.1",
    agent_version: str = "1.0.0"
) -> Endpoint:
    """
    Exchange an authorized enrollment token for a registered endpoint identity.
    Rejects expired, revoked, or already-used tokens.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enrollment_tokens WHERE token = ?;", (token.strip(),))
        row = cursor.fetchone()

        if not row:
            raise SecurityViolationError("Invalid enrollment token.")

        if row["used"] == 1:
            raise SecurityViolationError("Enrollment token has already been consumed.")

        now_str = utc_now_iso()
        if now_str > row["expires_at"]:
            raise SecurityViolationError("Enrollment token has expired.")

        endpoint_id = generate_id("ep")
        cert_id = certificate_identity or f"cert_{secrets.token_hex(8)}"

        endpoint = Endpoint(
            id=endpoint_id,
            device_label=row["device_label"],
            operating_system=row["operating_system"],
            agent_version=agent_version,
            enrollment_status="active",
            certificate_identity=cert_id,
            last_seen=now_str,
            created_at=now_str,
            ip_address=ip_address
        )

        with conn:
            # Mark token used
            conn.execute(
                "UPDATE enrollment_tokens SET used = 1, used_at = ? WHERE token = ?;",
                (now_str, token.strip())
            )

            # Insert enrolled endpoint
            conn.execute(
                """
                INSERT INTO endpoints (
                    id, device_label, operating_system, agent_version, enrollment_status,
                    certificate_identity, last_seen, created_at, ip_address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (endpoint.id, endpoint.device_label, endpoint.operating_system,
                 endpoint.agent_version, endpoint.enrollment_status,
                 endpoint.certificate_identity, endpoint.last_seen,
                 endpoint.created_at, endpoint.ip_address)
            )

            log_audit(
                operation="endpoint_enrolled",
                outcome="success",
                details=f"Endpoint '{endpoint.device_label}' enrolled with ID '{endpoint.id}'.",
                conn=conn
            )

        return endpoint
    finally:
        conn.close()


# Alias for test compatibility
enroll_endpoint_with_token = enroll_endpoint


def list_endpoints() -> list[Endpoint]:
    """Retrieve all enrolled endpoints."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM endpoints ORDER BY created_at DESC;")
        rows = cursor.fetchall()
        return [
            Endpoint(
                id=r["id"],
                device_label=r["device_label"],
                operating_system=r["operating_system"],
                agent_version=r["agent_version"],
                enrollment_status=r["enrollment_status"],
                certificate_identity=r["certificate_identity"] or "",
                last_seen=r["last_seen"],
                created_at=r["created_at"],
                revocation_timestamp=r["revocation_timestamp"],
                ip_address=r["ip_address"] or "127.0.0.1"
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_endpoint(endpoint_id: str) -> Optional[Endpoint]:
    """Retrieve endpoint by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM endpoints WHERE id = ?;", (endpoint_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return Endpoint(
            id=r["id"],
            device_label=r["device_label"],
            operating_system=r["operating_system"],
            agent_version=r["agent_version"],
            enrollment_status=r["enrollment_status"],
            certificate_identity=r["certificate_identity"] or "",
            last_seen=r["last_seen"],
            created_at=r["created_at"],
            revocation_timestamp=r["revocation_timestamp"],
            ip_address=r["ip_address"] or "127.0.0.1"
        )
    finally:
        conn.close()


def revoke_endpoint(endpoint_id: str) -> bool:
    """Revoke an endpoint identity to prevent further collection jobs or uploads."""
    conn = get_db_connection()
    try:
        now_str = utc_now_iso()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE endpoints SET enrollment_status = 'revoked', revocation_timestamp = ? WHERE id = ?;",
                (now_str, endpoint_id)
            )
            if cursor.rowcount == 0:
                return False

            log_audit(
                operation="endpoint_revoked",
                outcome="warning",
                details=f"Endpoint ID '{endpoint_id}' was revoked.",
                conn=conn
            )
        return True
    finally:
        conn.close()
