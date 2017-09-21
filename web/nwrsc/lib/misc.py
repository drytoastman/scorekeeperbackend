
class ArchivedSeriesException(Exception):
    pass

class InvalidSeriesException(Exception):
    pass

class InvalidEventException(Exception):
    pass

class InvalidChallengeException(Exception):
    pass

class NotLoggedInException(Exception):
    pass

class DisplayableError(Exception):
    def __init__(self, header, content, **kwargs):
        Exception.__init__(self, **kwargs)
        self.header = header
        self.content = content

def csvlist(inputstr, converter=None):
    arr = inputstr.strip().split(',')
    arr = [x for x in arr if x.strip() != '']
    if converter is not None:
        ret = []
        for x in arr:
            try:
                ret.append(converter(x))
            except:
                pass
        return ret
    else:
        return arr

