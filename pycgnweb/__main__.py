#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Suppport for calling the package as a command line script.

Usage::

    python -m pycgnweb

"""

from pycgnweb.webapp import main


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]) or 0)
