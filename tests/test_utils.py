import pytest

import ssl
from urllib.request import HTTPSHandler, HTTPCookieProcessor
from http.cookiejar import CookieJar

from bslib.utils import *

def test_passx_encode_decode():
    passwd = 'abcde'
    passwx = 'QlpoOTFBWSZTWaNbTfQAAAABAD4AIAAhg0GaAlxxdyRThQkKNbTfQA=='

    assert passx_encode(passwd) == passwx
    assert passx_decode(passwx)  == passwd
    assert passx_decode(passx_encode(passwd)) == passwd
    
    # below is passx string made in python 2.7
    passwx2= 'QlpoOTFBWSZTWaNbTfQAAAABAD4AIAAhg0GaAlxxdyRThQkKNbTfQA=='

    assert passwx == passwx2

def test_is_url():

    assert is_url("foo://bar")
    assert is_url("ftp://suse.com/pub/people/mvyskocil")
    assert not is_url("general")
    #this one lack a netloc, which is out of scope for bslib
    assert not is_url("file:///etc/passwd")

#FIXME: how to test that properly?
def test_build_opener():
    
    opener = build_opener("https://api.url", "joe", "s3scret", None)
    print(dir(opener))

    #there are 8 handlers installed by build_opener
    #we add
    #   - https_handler (already included in default list)
    #   - http basic auth handler +1
    #   - cookie processor +1
    #   - proxy handler (for uknown reason not in handlers list)
    #   ^^^ maybe to test in env with proxy?
    assert len(opener.handlers) == 10

    assert isinstance(opener.handlers[6], HTTPSHandler)

    ctx = opener.handlers[6]._context
    
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.protocol == ssl.PROTOCOL_SSLv23
    #test if sslv2 support was realy disables
    assert ctx.options == ctx.options | ssl.OP_NO_SSLv2

    assert isinstance(opener.handlers[7], HTTPCookieProcessor)
    assert isinstance(opener.handlers[7].cookiejar, CookieJar)

def test_inspect_signature():
    
    def foo(arg, barg=12, *args, **kwargs):
        pass

    assert list(inspect_signature(foo)) == \
        [("arg", False, None), ("barg", True, 12)]

def test_applyurltemplate():
    
    #url w/o query
    assert apply_urltemplate("https://api.url/{path}", {'path' : "PATH!"}) == \
           "https://api.url/PATH%21"
    
    #url with query w/o quoting
    template = "https://api.url/{path}/?q={q1}&empty={empty}&q2={q2}"
    kwdct = {"path" : "PATH!", "q1" : "q1", "empty" : None, "q2" : ""}
    assert apply_urltemplate(template, kwdct) == \
           "https://api.url/PATH%21/?q=q1"

    #url with query and different quoting for + in path and query
    kwdct = {"path" : "PATH + !", "q1" : "q1 + !", "empty" : None, "q2" : ""}
    assert apply_urltemplate(template, kwdct) == \
            "https://api.url/PATH%20%2B%20%21/?q=q1+%2B+%21"

    # to emphasize, apply_urltemplate does not call is_url (yet)
    assert apply_urltemplate("blah{blah}blah", {"blah" : "X"}) == "blahXblah"