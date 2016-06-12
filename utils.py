from recordclass import recordclass


def recordclassdef(name, fields, default=None):
    r = recordclass(name, fields)

    def newNew(_cls):
        ff = [default for f in fields]
        #print(ff)
        return _cls.__old_new(_cls, *ff)

    r.__old_new = r.__new__
    r.__new__ = newNew

    return r



def fillunderlongTableRows(tab, filler):
    maxLen = 0
    for r in tab:
        maxLen = max(len(r), maxLen)

    for r in tab:
        undersize = maxLen - len(r)
        if undersize > 0:
            r.extend((filler,) * undersize)

    return tab


def expectValue(value, expected, comment):
    if value != expected:
        print('Unexpected value {0} (expected {1}): {2}'.format(value, expected, comment))