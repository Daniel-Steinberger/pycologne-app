from random import shuffle

def get_saying():
    sayings = [('The Zen of Python, by Tim Peters', '__Tim Peters, The Zen of Python'),
    ("Beautiful is better than ugly.", '__Tim Peters, The Zen of Python'),
    ("Explicit is better than implicit.", '__Tim Peters, The Zen of Python'),
    ("Simple is better than complex.", '__Tim Peters, The Zen of Python'),
    ("Complex is better than complicated.", '__Tim Peters, The Zen of Python'),
    ("Flat is better than nested.", '__Tim Peters, The Zen of Python'),
    ("Sparse is better than dense.", '__Tim Peters, The Zen of Python'),
    ("Readability counts.", '__Tim Peters, The Zen of Python'),
    ("Special cases aren't special enough to break the rules.", '__Tim Peters, The Zen of Python'),
    ("Although practicality beats purity.", '__Tim Peters, The Zen of Python'),
    ("Errors should never pass silently.", '__Tim Peters, The Zen of Python'),
    ("Unless explicitly silenced.", '__Tim Peters, The Zen of Python'),
    ("In the face of ambiguity, refuse the temptation to guess.", '__Tim Peters, The Zen of Python'),
    ("Although that way may not be obvious at first unless you're Dutch.", '__Tim Peters, The Zen of Python'),
    ("Now is better than never.", '__Tim Peters, The Zen of Python'),
    ("Although never is often better than *right* now.", '__Tim Peters, The Zen of Python'),
    ("If the implementation is hard to explain, it's a bad idea.", '__Tim Peters, The Zen of Python'),
    ("If the implementation is easy to explain, it may be a good idea.", '__Tim Peters, The Zen of Python'),
    ("Namespaces are one honking great idea -- let's do more of those!", '__Tim Peters, The Zen of Python'),
    ]

    shuffle(sayings)

    saying, author = sayings[0]
    return saying, author
