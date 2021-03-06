#encoding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import pytest
import sys
from io import BytesIO

import bslib.raw

from bslib import BSContext
from bslib.config import BSConfig
from bslib.raw import api, GET_request_id, POST_request_id_cmddiff, POST_request

from .test_config import CFG_DICT

@pytest.yield_fixture
def raw_return_string():
    #monkeys, monkeys!
    old_raw = bslib.raw.raw
    def raw(ctx, method, url, datafp=None):
        if method == "POST":
            return method, url, datafp
        return method, url
    bslib.raw.raw = raw
    yield

    bslib.raw.raw = old_raw
    del raw

cfg = BSConfig(**CFG_DICT)
ctx = BSContext(cfg.for_apiurl("https://api.opensuse.org/"))

def test_basic_requests(raw_return_string):
    """
    due the fact all basic requests, which are decorated through @api are empty,
    let test only a few of them
    """

    global ctx
    apiurl = ctx.apiurl

    assert GET_request_id(ctx, 11) == ("GET", "{}/request/11".format(apiurl))
    #it is OK to pass an incorrect argument, as functions does not do any checking
    assert GET_request_id(ctx, "joe") == ("GET", "{}/request/joe".format(apiurl))
    #tests POST
    assert POST_request_id_cmddiff(ctx, 11) == ("POST", "{}/request/11?cmd=diff".format(apiurl), None)
    comment = BytesIO(b"comment")
    assert POST_request(ctx, 11, comment=comment) == ("POST", "{}/request/11".format(apiurl), comment)

    @api("PUT {apiurl}/method/?arg={arg}")
    def x(ctx, arg=42): pass

    assert x(ctx, ) == ("PUT", "{}/method/?arg=42".format(apiurl))

@pytest.mark.xfail(sys.version_info < (3,3), reason="FIXME:different unicode/str handling in python2")
def test_unicode_requests(raw_return_string):
    global ctx
    apiurl = ctx.apiurl

    #tests- if quote is used on argument
    assert GET_request_id(ctx, u"žluť") == ("GET", "{}/request/%C5%BElu%C5%A5".format(apiurl))

def test_error_requests(raw_return_string):
    
    global ctx
    apiurl = ctx.apiurl

    @api("FOO foobar")
    def x(ctx, apiurl): pass

    # bad HTTP method FOO raises ValueError
    with pytest.raises(ValueError):
        x(ctx, apiurl)

    @api("GET x")
    def x(): pass

    # ValueError raised by no context and apiurl variables
    with pytest.raises(ValueError):
        x()

    @api("GET api.url/{request}")
    def x(ctx, apiurl, request): pass

    # ValueError raised by bad url
    with pytest.raises(ValueError):
        x(ctx, apiurl, "request")
