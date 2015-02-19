#
# Makefile for pycologne
#

SOURCES = webapp.py sayings.py config.py lib/events.py
TESTS = _tests/test_sayings.py \
        _tests/test_http_status.py

LINTME = $(SOURCES) $(TESTS)

# location for the webapp.py we use:
export PYTHONPATH=$(PWD)

.PHONY: pylint

pylint: $(LINTME)
	pylint --rcfile=pylint.rc $^
