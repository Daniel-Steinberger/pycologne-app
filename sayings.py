from flask.ext.babel import gettext as _
from random import shuffle

def get_saying():
    sayings = [(_('The Zen of Python, by Tim Peters'), _('__Tim Peters, The Zen of Python')),
               (_("Beautiful is better than ugly."), _('__Tim Peters, The Zen of Python')),
               (_("Explicit is better than implicit."), _('__Tim Peters, The Zen of Python')),
               (_("Simple is better than complex."), _('__Tim Peters, The Zen of Python')),
               (_("Complex is better than complicated."), _('__Tim Peters, The Zen of Python')),
               (_("Flat is better than nested."), _('__Tim Peters, The Zen of Python')),
               (_("Sparse is better than dense."), _('__Tim Peters, The Zen of Python')),
               (_("Readability counts."), _('__Tim Peters, The Zen of Python')),
               (_("Special cases aren't special enough to break the rules."), _('__Tim Peters, The Zen of Python')),
               (_("Although practicality beats purity."), _('__Tim Peters, The Zen of Python')),
               (_("Errors should never pass silently."), _('__Tim Peters, The Zen of Python')),
               (_("Unless explicitly silenced."), _('__Tim Peters, The Zen of Python')),
               (_("In the face of ambiguity, refuse the temptation to guess."), _('__Tim Peters, The Zen of Python')),
               (_("Although that way may not be obvious at first unless you're Dutch."), _('__Tim Peters, The Zen of Python')),
               (_("Now is better than never."), _('__Tim Peters, The Zen of Python')),
               (_("Although never is often better than *right* now."), _('__Tim Peters, The Zen of Python')),
               (_("If the implementation is hard to explain, it's a bad idea."), _('__Tim Peters, The Zen of Python')),
               (_("If the implementation is easy to explain, it may be a good idea."), _('__Tim Peters, The Zen of Python')),
               (_("Namespaces are one honking great idea -- let's do more of those!"), _('__Tim Peters, The Zen of Python')),
               ]
    
    shuffle(sayings)
    
    saying, author = sayings[0]
    return saying, author
