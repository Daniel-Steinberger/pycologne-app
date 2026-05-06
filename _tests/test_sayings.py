#!/usr/bin/env python
"""Unit tests for pycgnweb.sayings module."""

from pycgnweb.sayings import get_saying


def test_saying():
    """Test that 'sayings' tuple elements are not None."""
    saying, author = get_saying()
    assert saying is not None
    assert author is not None
