from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class DecryptionError(Exception):
    """Raised when a stored ciphertext cannot be decrypted (wrong/rotated key, corruption)."""


def _fernet() -> Fernet:
    return Fernet(get_settings().FERNET_KEY.encode())


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret (router password, PPP secret password, etc.) for storage at rest."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str) -> str:
    """Decrypt a value previously produced by encrypt_secret()."""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError("Could not decrypt stored secret - FERNET_KEY may have changed") from exc
