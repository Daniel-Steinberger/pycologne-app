#
# Makefile for pymove3D
#

# location for the pymove3d.py we use:
export PYTHONPATH=$(PWD)

pylint:
	pylint ./pymove3d.py

pybabel_init:
	pybabel extract -o ./translations/pymove3d.pot .
	pybabel init -i ./translations/pymove3d.pot -d translations -l de
	pybabel init -i ./translations/pymove3d.pot -d translations -l en

pybabel_update:
	pybabel extract -o ./translations/pymove3d.pot .
	pybabel update -i ./translations/pymove3d.pot -d translations -l de
	pybabel update -i ./translations/pymove3d.pot -d translations -l en

msgfmt:
	msgfmt --strict ./translations/de/LC_MESSAGES/messages.po -o ./translations/de/LC_MESSAGES/messages.mo
	