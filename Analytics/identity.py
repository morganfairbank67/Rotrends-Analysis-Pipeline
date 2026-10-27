import re
import unicodedata
import uuid
from datetime import date, datetime

BRACKETED = re.compile(r"\[[^\]]*\]|\([^)]*\)")
NON_WORD = re.compile(r"[\W_]+")
EMOJI_JOINERS = {0xFE0F, 0x200D}
NAMESPACE = uuid.UUID("6f1c2b1e-3f55-4a0e-9a54-5c6b1f0d7a11")


def is_emoji(char: str) -> bool:
    return (
        unicodedata.category(char) == "So"
        or ord(char) >= 0x1F000
        or ord(char) in EMOJI_JOINERS
    )


def core_title(title: str) -> str:
    text = BRACKETED.sub(" ", str(title).lower())
    text = "".join(" " if is_emoji(c) else c for c in text)
    return NON_WORD.sub(" ", text).strip()


def created_label(created) -> str:
    if isinstance(created, (datetime, date)):
        return created.strftime("%Y-%m-%d")
    if created is None or str(created) in ("", "NaT", "nan"):
        return "unknown"
    return str(created)[:10]


def game_key(name: str, created) -> str:
    return f"{core_title(name)}|{created_label(created)}"


def stable_game_id(name: str, created) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, game_key(name, created))
