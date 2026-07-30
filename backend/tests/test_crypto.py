import pytest

from app.core.crypto import DecryptionError, decrypt_secret, encrypt_secret
from app.core.security import hash_password, verify_password
from app.utils.password_gen import generate_strong_password


def test_encrypt_decrypt_roundtrip():
    plaintext = "s3cr3t-router-password"
    token = encrypt_secret(plaintext)
    assert token != plaintext
    assert decrypt_secret(token) == plaintext


def test_decrypt_garbage_raises():
    with pytest.raises(DecryptionError):
        decrypt_secret("not-a-valid-fernet-token")


def test_password_hash_and_verify():
    password = "correct horse battery staple"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_generate_strong_password_length_and_charset():
    password = generate_strong_password()
    assert len(password) >= 12
    assert not any(c in "Il1O0" for c in password)


def test_generate_strong_password_uniqueness():
    passwords = {generate_strong_password() for _ in range(20)}
    assert len(passwords) == 20
