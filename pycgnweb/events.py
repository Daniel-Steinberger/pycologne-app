#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calculate dates of next PyCologne meetings."""

from __future__ import unicode_literals, print_function

from dateutil.rrule import rrule, MONTHLY, WE

__all__ = ('meeting_dates',)


def meeting_dates(count=12):
    """Return iterator yielding datetime instances for next meeting dates.

    Yields *count* items (defaults to twelve).

    """
    return iter(rrule(MONTHLY, byweekday=WE(+2), byhour=19, byminute=0,
                      bysecond=0, count=count))


def _test():
    """Test/demonstration code for 'meeting_dates' function."""
    date_fmt = "%A, %d. %B %Y, %H:%M Uhr"
    meetings = meeting_dates()

    print("Nächstes PyCologne-Treffen: {}".format(
        next(meetings).strftime(date_fmt).decode('utf-8')))

    print("\nNachfolgende Termine:\n")

    for date in meetings:
        print("* {}".format(date.strftime(date_fmt).decode('utf-8')))


if __name__ == '__main__':
    # example usage
    import locale

    locale.setlocale(locale.LC_ALL, ('de_DE', 'UTF-8'))
    _test()
