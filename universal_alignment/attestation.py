"""Local HMAC authentication; keys and signing services belong to the protected host.
This is neither a sandbox nor a proof of the truth of the signed observations.
"""
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
from typing import Mapping


def utc_now():
    return datetime.now(timezone.utc)


def parse_time(value):
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp_required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone_required")
    return result


def _message_bytes(message):
    payload = asdict(message)
    payload.pop("signature", None)
    return (message.DOMAIN + "\n" + json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )).encode("utf-8")


class LocalAttestor:
    """Do not expose this object, its key or an arbitrary signing endpoint to the agent."""
    def __init__(self, source: str, key: bytes):
        if not isinstance(source, str) or not source or not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("source_and_at_least_32_byte_key_required")
        self.source = source
        self._key = key

    def sign(self, message, *, lifetime_seconds=60, now=None):
        if message.source != self.source:
            raise ValueError("signer_source_mismatch")
        if not 0 < lifetime_seconds <= 300:
            raise ValueError("attestation_lifetime_must_be_1_to_300_seconds")
        now = now or utc_now()
        stamped = replace(message, issued_at=now.isoformat(),
                          expires_at=(now + timedelta(seconds=lifetime_seconds)).isoformat(),
                          signature="")
        signature = hmac.new(self._key, _message_bytes(stamped), sha256).hexdigest()
        return replace(stamped, signature=signature)


class AttestationVerifier:
    def __init__(self, keys: Mapping[str, bytes]):
        if not isinstance(keys, Mapping):
            raise ValueError("attestation_keys_mapping_required")
        self._keys = dict(keys)
        if any(not isinstance(source, str) or not source for source in self._keys):
            raise ValueError("invalid_attestation_source")
        if any(not isinstance(k, bytes) or len(k) < 32 for k in self._keys.values()):
            raise ValueError("at_least_32_byte_keys_required")

    def valid(self, message, *, now=None):
        try:
            key = self._keys.get(message.source)
            if key is None or not isinstance(message.signature, str):
                return False
            expected = hmac.new(key, _message_bytes(message), sha256).hexdigest()
            if not hmac.compare_digest(expected, message.signature):
                return False
            start, end = parse_time(message.issued_at), parse_time(message.expires_at)
            current = now or utc_now()
            return start <= current < end and timedelta(0) < end - start <= timedelta(seconds=300)
        except (TypeError, ValueError, AttributeError, OverflowError):
            return False
