import secrets
import string

_AMBIGUOUS = set("Il1O0")
_ALPHABET = "".join(c for c in (string.ascii_letters + string.digits) if c not in _AMBIGUOUS)
_SYMBOLS = "!@#$%^&*-_=+"


def generate_strong_password(length: int = 20) -> str:
    """Generate a random password suitable for a PPP secret.

    Avoids visually-ambiguous characters (I/l/1/O/0) since these are often
    read off a screen and typed into a peer router's config by hand.
    """
    if length < 12:
        length = 12
    # Guarantee at least one symbol and one digit for basic complexity, then
    # fill the rest randomly from the full alphabet.
    chars = [
        secrets.choice(_SYMBOLS),
        secrets.choice([c for c in string.digits if c not in _AMBIGUOUS]),
    ]
    chars += [secrets.choice(_ALPHABET + _SYMBOLS) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)
