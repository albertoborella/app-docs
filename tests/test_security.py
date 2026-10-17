import base64
import hashlib
from datetime import datetime, timedelta, timezone

from app.core import security


def test_hash_password_is_bcrypt_not_plaintext():
    hashed = security.hash_password("s3cret-pass")
    assert hashed.startswith("$2b$")
    assert "s3cret-pass" not in hashed


def test_verify_password_roundtrip():
    hashed = security.hash_password("s3cret-pass")
    assert security.verify_password("s3cret-pass", hashed)
    assert not security.verify_password("wrong-pass", hashed)


def test_session_token_is_256_bits():
    token = security.create_session_token()
    raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
    assert len(raw) == 32


def test_only_sha256_of_token_is_persisted():
    token = security.create_session_token()
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert security.hash_token(token) == expected


def test_expired_ttl_is_rejected_and_valid_ttl_is_not():
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    future = datetime.now(timezone.utc) + timedelta(hours=12)
    assert security.is_token_expired(past)
    assert not security.is_token_expired(future)
