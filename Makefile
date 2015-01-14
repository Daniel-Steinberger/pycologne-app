#
# Makefile for pymove3D
#

# location for the webapp.py we use:
export PYTHONPATH=$(PWD)

pylint:
	pylint ./webapp.py
