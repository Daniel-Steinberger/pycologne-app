#
# Makefile for pycologne
#

PKG = pycgnweb
SOURCES = $(PKG)/__main__.py $(PKG)/config.py $(PKG)/events.py \
	$(PKG)/sayings.py $(PKG)/webapp.py
TESTS = _tests/test_sayings.py \
	_tests/test_http_status.py

LINTME = $(SOURCES) $(TESTS)

# location for the webapp.py we use:
export PYTHONPATH=$(PWD)

.PHONY: check flake less pylint run run-debug

pylint: $(LINTME)
	pylint --rcfile=pylint.rc $^

flake:
	flake8

check: flake pylint

less:
	lessc static/less/pycologne.less > static/css/pycologne.css

run:
	python -m pycgnweb

run-debug:
	python -m pycgnweb -d
