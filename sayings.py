from random import shuffle


def get_saying():
    sayings = [
        (u'The Zen of Python, by Tim Peters',
         u'__Tim Peters, The Zen of Python'),
        (u"Beautiful is better than ugly.",
         u'__Tim Peters, The Zen of Python'),
        (u"Explicit is better than implicit.",
         u'__Tim Peters, The Zen of Python'),
        (u"Simple is better than complex.",
         u'__Tim Peters, The Zen of Python'),
        (u"Complex is better than complicated.",
         u'__Tim Peters, The Zen of Python'),
        (u"Flat is better than nested.",
         u'__Tim Peters, The Zen of Python'),
        (u"Sparse is better than dense.",
         u'__Tim Peters, The Zen of Python'),
        (u"Readability counts.", u'__Tim Peters, The Zen of Python'),
        (u"Special cases aren't special enough to break the rules.",
         u'__Tim Peters, The Zen of Python'),
        (u"Although practicality beats purity.",
         u'__Tim Peters, The Zen of Python'),
        (u"Errors should never pass silently, unless explicitly silenced.",
         u'__Tim Peters, The Zen of Python'),
        (u"In the face of ambiguity, refuse the temptation to guess.",
         u'__Tim Peters, The Zen of Python'),
        (u"Although that way may not be obvious at first unless you're Dutch.",
         u'__Tim Peters, The Zen of Python'),
        (u"Now is better than never.",
         u'__Tim Peters, The Zen of Python'),
        (u"Although never is often better than *right* now.",
         u'__Tim Peters, The Zen of Python'),
        (u"If the implementation is hard to explain, it's a bad idea.",
         u'__Tim Peters, The Zen of Python'),
        (u"If the implementation is easy to explain, it may be a good idea.",
         u'__Tim Peters, The Zen of Python'),
        (u"Namespaces are one honking great idea -- let's do more of those!",
         u'__Tim Peters, The Zen of Python'),
        (u"I once tried Java, but it was too complicated for me, "
         "Python is easier.",
         u'__Valentin Pratz,  novice programmers'),
    ]

    shuffle(sayings)

    saying, author = sayings[0]
    return saying, author
