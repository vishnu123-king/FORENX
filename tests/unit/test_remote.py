"""
Unit tests for ForenX Remote Forensics (Mode B).
Covers endpoint enrollment tokens, revocation, and strict collection job scope enforcement.
"""

import pytest
from forenx.remote.endpoints import (
    generate_enrollment_token,
    enroll_endpoint_with_token,
    revoke_endpoint,
    get_endpoint,
    list_endpoints
)
from forenx.remote.jobs import (
    create_acquisition_job,
    validate_job_scope,
    get_job,
    list_jobs
)
from forenx.exceptions import SecurityViolationError
from forenx.cases import create_case


def test_enrollment_token_lifecycle():
    token = generate_enrollment_token(
        device_label="TEST-LAPTOP-01",
        operating_system="windows",
        created_by="Inspector Gadget",
        expiry_minutes=30
    )

    assert token.token is not None
    assert len(token.token) >= 32
    assert token.used is False

    # Enroll device using the token
    endpoint = enroll_endpoint_with_token(
        token=token.token,
        certificate_identity="SHA256:CERT:FINGERPRINT:TEST",
        ip_address="192.168.1.105"
    )

    assert endpoint.device_label == "TEST-LAPTOP-01"
    assert endpoint.enrollment_status == "active"
    assert endpoint.certificate_identity == "SHA256:CERT:FINGERPRINT:TEST"

    # Reusing the token must fail (single-use constraint)
    with pytest.raises(SecurityViolationError):
        enroll_endpoint_with_token(
            token=token.token,
            certificate_identity="SHA256:CERT:OTHER",
            ip_address="192.168.1.106"
        )


def test_endpoint_revocation():
    token = generate_enrollment_token(device_label="REVOKE-ME-PC")
    endpoint = enroll_endpoint_with_token(
        token=token.token,
        certificate_identity="CERT:REVOKE:TEST",
        ip_address="10.0.0.99"
    )

    assert endpoint.enrollment_status == "active"

    # Revoke
    ok = revoke_endpoint(endpoint.id)
    assert ok is True

    # Fetching again confirms revoked
    fetched = get_endpoint(endpoint.id)
    assert fetched is not None
    assert fetched.enrollment_status == "revoked"
    assert fetched.revocation_timestamp is not None


def test_job_scope_allowlist_enforcement():
    # Valid scope
    valid_scope = {
        "approved_browsers": ["chrome", "firefox"],
        "approved_artifact_types": ["History", "places.sqlite"]
    }
    validate_job_scope(valid_scope)  # should not raise

    # Disallowed browser
    with pytest.raises(SecurityViolationError):
        validate_job_scope({
            "approved_browsers": ["safari_ios_exploit"],
            "approved_artifact_types": ["History"]
        })

    # Disallowed artifact (e.g. passwords or cookies)
    with pytest.raises(SecurityViolationError):
        validate_job_scope({
            "approved_browsers": ["chrome"],
            "approved_artifact_types": ["Login Data", "Cookies"]
        })

    # Disallowed arbitrary command injection attempt
    with pytest.raises(SecurityViolationError):
        validate_job_scope({
            "approved_browsers": ["chrome"],
            "approved_artifact_types": ["History"],
            "command": "rm -rf /"
        })

    with pytest.raises(SecurityViolationError):
        validate_job_scope({
            "approved_browsers": ["chrome"],
            "approved_artifact_types": ["History"],
            "shell": "/bin/bash -c whoami"
        })


def test_create_acquisition_job():
    test_case = create_case("Remote Job Case")

    token = generate_enrollment_token(device_label="JOB-TEST-PC")
    endpoint = enroll_endpoint_with_token(
        token=token.token,
        certificate_identity="CERT:JOB:PC",
        ip_address="10.0.0.120"
    )

    scope = {
        "approved_browsers": ["chrome", "firefox"],
        "approved_artifact_types": ["History", "places.sqlite"],
        "allow_wal_sidecars": True
    }

    metadata = {
        "warrant_or_incident_id": "WARRANT-2026-991",
        "investigator_signature_label": "Special Agent"
    }

    job = create_acquisition_job(
        case_id=test_case.id,
        endpoint_id=endpoint.id,
        requesting_investigator_id="Special Agent",
        authorized_scope=scope,
        authorization_metadata=metadata
    )

    assert job.id.startswith("job_")
    assert job.status in ("created", "approved")
    assert job.replay_nonce is not None
    assert len(job.replay_nonce) >= 16

    # Attempting to dispatch job to revoked endpoint must fail
    revoke_endpoint(endpoint.id)
    with pytest.raises(SecurityViolationError):
        create_acquisition_job(
            case_id=test_case.id,
            endpoint_id=endpoint.id,
            requesting_investigator_id="Special Agent",
            authorized_scope=scope
        )
