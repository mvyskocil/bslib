import bz2
import base64
import os
import ssl

from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit, quote
from urllib.request import HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, HTTPSHandler, ProxyHandler, proxy_bypass, HTTPCookieProcessor
from urllib.request import build_opener as _build_opener
from http.cookiejar import LWPCookieJar, CookieJar
from inspect import signature, _empty, _POSITIONAL_OR_KEYWORD

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

    authhandler = HTTPBasicAuthHandler(
        HTTPPasswordMgrWithDefaultRealm())
    authhandler.add_password(None, apiurl, bytes(user, "utf-8"), bytes(password, "ascii"))

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

    try:
    # TODO is this correct?
        cookie_file = os.path.expanduser(cookie_path)
        cookiejar = LWPCookieJar(cookie_file)
        cookiejar.load(ignore_discard=True)
    except (OSError, AttributeError):
        try:
            os.open(cookie_file, os.O_WRONLY | os.O_CREAT, mode=0o600)
        except:
            #TODO: log it
            cookiejar = CookieJar()

    # proxy handling
    if not proxy_bypass(apiurl):
        proxyhandler = ProxyHandler()
    else:
        proxyhandler = ProxyHandler({})

    opener = _build_opener(
        httpshandler,
        HTTPCookieProcessor(cookiejar),
        authhandler,
        proxyhandler)
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
