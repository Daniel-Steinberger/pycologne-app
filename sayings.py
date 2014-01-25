from flask.ext.babel import gettext as _
from random import shuffle

def get_saying():
    sayings = [(_(u'The Zen of Python, by Tim Peters'), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Beautiful is better than ugly."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Explicit is better than implicit."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Simple is better than complex."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Complex is better than complicated."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Flat is better than nested."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Sparse is better than dense."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Readability counts."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Special cases aren't special enough to break the rules."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Although practicality beats purity."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Errors should never pass silently."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Unless explicitly silenced."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"In the face of ambiguity, refuse the temptation to guess."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Although that way may not be obvious at first unless you're Dutch."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Now is better than never."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Although never is often better than *right* now."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"If the implementation is hard to explain, it's a bad idea."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"If the implementation is easy to explain, it may be a good idea."), _(u'__Tim Peters, The Zen of Python')),
               (_(u"Namespaces are one honking great idea -- let's do more of those!"), _(u'__Tim Peters, The Zen of Python')),
               (_(u"I once tried Java, but it was too complicated for me, Python is easier."),_(u'__Valentin Pratz,  novice programmers')),
               ]
    
    shuffle(sayings)
    
    saying, author = sayings[0]
    return saying, author
