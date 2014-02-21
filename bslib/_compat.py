# compatibility for python2

import codecs
from ConfigParser import ConfigParser

# taken from python3 docs
# http://docs.python.org/3.3/library/types.html
class SimpleNamespace(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))

# Used in parser getters to indicate the default behaviour when a specific
# option is not found it to raise an exception. Created to enable `None' as
# a valid fallback value.
_UNSET = object()

class ConfigParser3(ConfigParser):
    # taken from python 3.3 souce code
    def read_file(self, f, source=None):
        """Like read() but the argument must be a file-like object.

        The `f' argument must be iterable, returning one line at a time.
        Optional second argument is the `source' specifying the name of the
        file being read. If not given, it is taken from f.name. If `f' has no
        `name' attribute, `<???>' is used.
        """
        if source is None:
            try:
                source = f.name
            except AttributeError:
                source = '<???>'
        self._read(f, source)

    def items(self, section=_UNSET, raw=False, vars=None):
        if section is _UNSET:
            return self._sections.items()
        return ConfigParser.items(self, section, raw, vars)

#mvyskocil: written from scratch
class bytes(type):
    """
bytes(iterable_of_ints) -> bytes
bytes(string, encoding[, errors]) -> bytes
bytes(bytes_or_buffer) -> immutable copy of bytes_or_buffer
bytes(int) -> bytes object of size given by the parameter initialized with null bytes
bytes() -> empty bytes object

Construct an immutable array of bytes from:
  - an iterable yielding integers in range(256)
  - a text string encoded using the specified encoding
  - any object implementing the buffer API.
  - an integer"""

    def __new__(klass, arg = None, encoding = None, errors = "strict"):

        if arg is None:
            return str()
        elif isinstance(arg, (int, long)):
            return long(arg) * "\0"
        elif isinstance(arg, (str, unicode)):
            if encoding is None:
                raise TypeError("TypeError: string argument without an encoding")
            if not isinstance(encoding, (str, unicode)):
                raise TypeError("bytes() argument 2 must be str, not %s" % type(args[1]))
            if not isinstance(errors, (str, unicode)):
                raise TypeError("bytes() argument 3 must be str, not %s" % type(args[1]))
            return codecs.encode(arg, encoding, errors)
        elif hasattr(arg, "__iter__"):
            out = StringIO()
            for i in iter(arg):
                if not isinstance(i, (int, long)):
                    raise TypeError("'%s' object cannot be intereted as integer" % type(i))
                if i > 255:
                    raise ValueError("bytes must be in range(0, 256)")
            return out.getvalue()
        else:
            raise TypeError("'%s' is not iterable" % type(arg))
