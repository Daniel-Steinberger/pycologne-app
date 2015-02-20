#
# Makefile for pycologne
#

PKG = pycgnweb
SOURCES = \
	$(PKG)/__main__.py \
	$(PKG)/config.py \
	$(PKG)/events.py \
	$(PKG)/sayings.py \
	$(PKG)/webapp.py
TESTS =\
	_tests/test_sayings.py \
	_tests/test_http_status.py
CSSFILES = \
	pycologne.css
LINTME = $(SOURCES) $(TESTS)
STATICDIR = static
LESSDIR = $(STATICDIR)/less
CSSDIR = $(STATICDIR)/css

# location for the webapp.py we use:
export PYTHONPATH=$(PWD)

%.css: $(LESSDIR)/%.less
	less $< > $(CSSDIR)/$@

.PHONY: check flake less pylint pylint-report run run-debug

pylint: $(LINTME)
	# Pylint exit code 4 (warnings) and higher ignored
	pylint --rcfile=pylint.rc --reports=n $^ || test $$[$$?&3] -eq 0

pylint-report: $(LINTME)
	pylint --rcfile=pylint.rc $^

flake:
	flake8

check: flake pylint

less: $(CSSFILES)

run:
	python -m pycgnweb

run-debug:
	python -m pycgnweb -d
