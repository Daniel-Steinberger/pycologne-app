#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

__all__ = ['meeting_dates']

from dateutil.rrule import rrule, MONTHLY, WE


def meeting_dates(count=12):
    """Return iterator yielding datetime instances for *count* next meetings.
    """
    return iter(rrule(MONTHLY, byweekday=WE(+2), byhour=19, byminute=0,
                      bysecond=0, count=count))


if __name__ == '__main__':
    # example usage
    import locale

    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    DATE_FMT = "%A, %d. %B %Y, %H:%M Uhr"

    meetings = meeting_dates()
    print("Nächstes PyCologne-Treffen: {}".format(
        next(meetings).strftime(DATE_FMT)))

    print("\nNachfolgende Termine:\n")

    for date in meetings:
        print("* {}".format(date.strftime(DATE_FMT)))
