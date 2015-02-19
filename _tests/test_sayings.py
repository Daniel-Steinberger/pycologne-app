from sayings import get_saying


def test_saying():
    saying, author = get_saying()
    assert saying is not None
    assert author is not None
