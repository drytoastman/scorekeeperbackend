
from operator import attrgetter
import re

class FlashableException(Exception):
    pass

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

def t3(val, sign=False):
    """ Wrapper to safely print floats as XXX.123 format """
    if val is None: return ""
    if type(val) is not float: return str(val)
    try:
        return (sign and "%+0.3f" or "%0.3f") % (val,)
    except:
        return str(val)

def d2(val):
    """ Wrapper to safely print dollar amounts as $XXX.12 format """
    if val is None: return ""
    if type(val) is not float: return str(val)
    try:
        return "$%0.2f" % (val,)
    except:
        return str(val)

def msort(val, *attr):
    """ Filter to sort on multiple attributes """
    ret = list(val)
    ret.sort(key=attrgetter(*attr))
    return ret

HASHTML = re.compile(r'(<!--.*?-->|<[^>]*>)')
def hashtml(val):
    return HASHTML.search(val) is not None

def any2bool(v):
    if type(v) is bool:
        return v
    if type(v) is str:
        return v.lower() in ("yes", "true", "t", "1")
    return v is not None
