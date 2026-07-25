import pytest

from backend.auth.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_round_trip():
    token = create_access_token(subject="user-123")
    assert decode_access_token(token) == "user-123"


def test_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_access_token("not-a-real-token")
