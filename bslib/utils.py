#encoding: utf-8

# bslib - various utilities
# Copyright (c) 2014 Michal Vyskocil<michal.vyskocil@gmail.com>
# Licensed under MIT, see bslib/__init__.py

from __future__ import print_function
from __future__ import unicode_literals

import bz2
import base64
import os
import ssl
from collections import OrderedDict

try:
    unicode
except NameError:
    unicode = str

try:
    from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit, quote
    from urllib.request import HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, HTTPSHandler, ProxyHandler, proxy_bypass, HTTPCookieProcessor
    from urllib.request import build_opener as _build_opener
    from http.cookiejar import LWPCookieJar, CookieJar
    from inspect import signature, _empty, _POSITIONAL_OR_KEYWORD
except ImportError:
    from urlparse import parse_qs, urlsplit, urlunsplit
    from urllib import urlencode, quote
    from urllib2 import HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, HTTPSHandler, ProxyHandler, proxy_bypass, HTTPCookieProcessor
    from urllib2 import build_opener as _build_opener
    from cookielib import LWPCookieJar, CookieJar
    from funcsigs import signature, _empty, _POSITIONAL_OR_KEYWORD
    from ._compat import bytes

__all__ = ["passx_decode", "passx_encode", "is_url", "build_opener", "inspect_signature",
"apply_urltemplate", "coroutine", "diff_to_dict"]

def passx_decode(passx):
    """decode the obfuscated plain text password, returns plain text password"""
    return bz2.decompress(base64.b64decode(passx.encode("ascii"))).decode("ascii")

def passx_encode(passwd):
    """encode plain text password to obfuscated form, mainly used for testing"""
    return base64.b64encode(bz2.compress(passwd.encode('ascii'))).decode("ascii")

def is_url(string):
    """determine if given string is url (ie something with at least scheme and netloc"""
    foo = urlsplit(string)
    return foo.scheme != '' and foo.netloc != ''

def build_opener(apiurl, user, password, cookie_path, debuglevel=0, capath=None, cafile=None, headers=()):
    """build urllib opener for given name/password
    
    it creates
      * HTTPSHandler with proper ssl context
      * HTTPCookieProcessor with a link to cookiejar
      * HTTPBasicAuthHandler with user/password
      * proxyhandler which respects no_proxy variable
    """

    handlers = list()

    if hasattr(ssl, "SSLContext"):
        #allow only sslv3 and tlsv1, but not sslv2
        ctx = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)
        ctx.options |= ssl.OP_NO_SSLv2
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.set_default_verify_paths()
        if cafile or capath:
            if ctx.load_verify_locations(capath=capath, cafile=cafile) != -1:
                raise Exception("load_verify_locations failed for capath={}, cafile={}".format(capath, cafile))
        #TODO: debuglevel
        httpshandler = HTTPSHandler(debuglevel=debuglevel, context=ctx, check_hostname=True)
        handlers.append(httpshandler)

    try:
    # TODO is this correct?
        cookie_file = os.path.expanduser(cookie_path)
        cookiejar = LWPCookieJar(cookie_file)
        cookiejar.load(ignore_discard=True)
    except (OSError, IOError, AttributeError):
        try:
            os.open(cookie_file, os.O_WRONLY | os.O_CREAT, mode=0o600)
        except:
            #TODO: log it
            cookiejar = CookieJar()
    handlers.append(HTTPCookieProcessor(cookiejar))
    
    authhandler = HTTPBasicAuthHandler(
        HTTPPasswordMgrWithDefaultRealm())
    authhandler.add_password(None, apiurl, bytes(user, "utf-8"), bytes(password, "ascii"))
    handlers.append(authhandler)

    # proxy handling
    if not proxy_bypass(apiurl):
        proxyhandler = ProxyHandler()
    else:
        proxyhandler = ProxyHandler({})
    handlers.append(proxyhandler)

    opener = _build_opener(*handlers)
    from bslib import __version__
    opener.addheaders = [("User-agent", "bslib/{}".format(__version__)), ]
    for h in headers:
        opener.addheaders(h)
    return opener

def inspect_signature(func):
    """Inspect a signature of a callable and return the tuple (name, has_default, default)

    note that default does makes a sense only if has_default == True, otherwise is None

    It does return POSITIONAL_OR_KEYWORD arguments only and intention is to determine
    argument with and without default value
    
    >>> def foo(arg, barg=11, *args, **kwargs): pass
    >>> list(inspect_signature(foo))
    [('arg', False, None), ('barg', True, 11)]
    """
    return ((name, par.default != _empty, par.default if par.default != _empty else None) \
            for name, par in signature(func).parameters.items()  \
            if par.kind == _POSITIONAL_OR_KEYWORD
            )

def apply_urltemplate(template, kwdct):
    """get the template, dictionary and apply it with proper quoting for path/url
    """

    # threat None as empty string
    kwdct = {k:v if v is not None else '' for k, v in kwdct.items()}
    
    foo = {}
    st = urlsplit(template)

    foo['path'] = quote(st.path.format(**kwdct))
    if not st.query:
        return urlunsplit(st._replace(**foo))
    query = dict()
    for k, v in parse_qs(st.query).items():
        newv = [y for y in \
            (x.format(**kwdct) for x in v) \
            if y]
        if newv:
            query[k] = newv
    foo['query'] = urlencode(query, doseq=True)
    return urlunsplit(st._replace(**foo))

def coroutine(func):
    """http://www.dabeaz.com/coroutines/coroutine.py
    A decorator function that takes care of starting a coroutine
    automatically on call."""

    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        next(cr)
        return cr
    return start

def cat(fp, target):
    """Like unix cat, just send numbered lines from fp to target"""
    for i, line in enumerate(fp):
        target.send((i+1, line))

@coroutine
def co_parse_obs_diff(target):
    """Parse the OBS diff format and send tuple (key, line) to target"""
    while True:
        num, line = (yield)
        if line.startswith("old:") or line.startswith("new:") or line.startswith("other changes:") or line.startswith("++++++ deleted files:"):
            key = line.strip()
            num, line = (yield)
            if not line.startswith("----"):
                raise SyntaxError("On line {}: the '----' expected, found {}".format(num, line))
            while True:
                num, line = (yield)
                if line == '\n':
                    break
                target.send((key, line.strip()))
        elif line.startswith("++++++ new changes file:"):
            #XXX: ignore that crap
            continue
        elif line.startswith("++++++ new spec file:"):
            continue
        elif line.startswith("++++++ "):
            num, next_line = (yield)
            if next_line.startswith("--- "):
                break
            while True:
                target.send(("rest:", line.strip()))
                num, line = (yield)
                if not line.startswith("++++++ "):
                    break
        elif line.startswith("+++ "):
            key = line[4:].strip()
            num, line = (yield)
            if line[:3] != "@@ ":
                raise SyntaxError("On line {} hunk delimiter expected, got {}".format(num, line))
            target.send((key, line))
            while True:
                num, line = (yield)
                #XXX: OBS does generate a diffs w/o empty space sometimes
                if line == '\n' or line.startswith("--- "):
                    break
                if line.startswith("Index: "):
                    num, line = (yield)
                    if not line.startswith("=========="):
                        raise SyntaxError("On line {}: the '========' expected after 'Index: ', found {}".format(num, line))
                    break
                if line[0] not in (' ', '+', '-') and line[:3] != "@@ ":
                    raise SyntaxError("On line {}: wrong initial character or hunk delimiter, got '{}'".format(num, line))
                target.send((key, line))

@coroutine
def co_diff2dict(dct):
    """Read key, value tuple and add that to mapping object dct"""
    while True:
        key, value = (yield)
        try:
            dct[key].append(value)
        except KeyError:
            dct[key] = list()
            dct[key].append(value)

def diff_to_dict(fp, _klass=OrderedDict):
    """Return diff as a mapping object (OrderedDict instance by default), where keys are
    file names and values are hunks related to them.

    This makes a bridge between coroutines and normal routines ...
    """
    if isinstance(fp, (str, unicode)):
        raise ValueError("IO-like object expected, not plain string/unicode")

    dct = _klass()
    try:
        cat(fp, co_parse_obs_diff(
            co_diff2dict(
                dct)))
    except StopIteration:
        pass
    return dct
