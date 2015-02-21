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

.PHONY: check flake less pylint pylint-report run run-debug

all:
	@echo "No default make target."

%.css: $(LESSDIR)/%.less
	less $< > $(CSSDIR)/$@

pylint: $(LINTME)
# 	Pylint exit codes other than 1, 2 and 32 are ignored
	pylint --rcfile=pylint.rc --reports=n $^ || test $$(($$?&35)) -eq 0

pylint-report: $(LINTME)
	pylint --rcfile=pylint.rc $^

flake:
# 	flake8 should read tox.ini by default but it does not
	flake8 --config=tox.ini

check: flake pylint

less: $(CSSFILES)

run:
	python -m pycgnweb

run-debug:
	python -m pycgnweb -d
