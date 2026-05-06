"""Container for sayings related to Python."""

from random import choice

SAYINGS: list[tuple[str, str]] = [
    ("Beautiful is better than ugly.", "__Tim Peters, The Zen of Python"),
    ("Explicit is better than implicit.", "__Tim Peters, The Zen of Python"),
    ("Simple is better than complex.", "__Tim Peters, The Zen of Python"),
    ("Complex is better than complicated.", "__Tim Peters, The Zen of Python"),
    ("Flat is better than nested.", "__Tim Peters, The Zen of Python"),
    ("Sparse is better than dense.", "__Tim Peters, The Zen of Python"),
    ("Readability counts.", "__Tim Peters, The Zen of Python"),
    ("Special cases aren't special enough to break the rules.", "__Tim Peters, The Zen of Python"),
    ("Although practicality beats purity.", "__Tim Peters, The Zen of Python"),
    (
        "Errors should never pass silently, unless explicitly silenced.",
        "__Tim Peters, The Zen of Python",
    ),
    (
        "In the face of ambiguity, refuse the temptation to guess.",
        "__Tim Peters, The Zen of Python",
    ),
    (
        "Although that way may not be obvious at first unless you're Dutch.",
        "__Tim Peters, The Zen of Python",
    ),
    ("Now is better than never.", "__Tim Peters, The Zen of Python"),
    ("Although never is often better than *right* now.", "__Tim Peters, The Zen of Python"),
    (
        "If the implementation is hard to explain, it's a bad idea.",
        "__Tim Peters, The Zen of Python",
    ),
    (
        "If the implementation is easy to explain, it may be a good idea.",
        "__Tim Peters, The Zen of Python",
    ),
    (
        "Namespaces are one honking great idea -- let's do more of those!",
        "__Tim Peters, The Zen of Python",
    ),
    (
        "I once tried Java, but it was too complicated for me, Python is easier.",
        "__Valentin Pratz, novice programmer",
    ),
]


def get_saying() -> tuple[str, str]:
    """Return a random saying."""
    saying, author = choice(SAYINGS)  # noqa: S311 — kein Krypto-Kontext
    return saying, author
