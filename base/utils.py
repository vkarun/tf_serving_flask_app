from distutils import util


def as_boolean(val):
    if type(val) == str:
        return util.strtobool(val)
    elif type(val) == bool:
        return val
    else:
        raise AssertionError('Expected %s to be a str or bool' % val)


_SUFFIXES = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def humansize(nbytes):
    """Returns a human readable representation of the byte size."""
    i = 0
    while nbytes >= 1024 and i < len(_SUFFIXES) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, _SUFFIXES[i])

