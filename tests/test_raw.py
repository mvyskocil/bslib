import pytest
from io import BytesIO

import bslib.raw

@pytest.yield_fixture
def raw_return_string():
    #monkeys, monkeys!
    old_raw = bslib.raw.raw
    def raw(ctx, method, apiurl, url, datafp=None):
        if method == "POST":
            return method, apiurl, url, datafp
        return method, apiurl, url
    bslib.raw.raw = raw
    yield

    bslib.raw.raw = old_raw
    del raw

from bslib.raw import api, GET_request_id, POST_request_id_cmddiff, POST_request

def test_basic_requests(raw_return_string):
    """
    due the fact all basic requests, which are decorated through @api are empty,
    let test only a few of them
    """

    apiurl = "https://api.url"
    
    assert GET_request_id(None, apiurl, 11) == ("GET", apiurl, "https://api.url/request/11")
    #it is OK to pass an incorrect argument, as functions does not do any checking
    assert GET_request_id(None, apiurl, "joe") == ("GET", apiurl, "https://api.url/request/joe")
    #tests- if quote is used on argument
    assert GET_request_id(None, apiurl, "žluť") == ("GET", apiurl, "https://api.url/request/%C5%BElu%C5%A5")
    #tests POST
    assert POST_request_id_cmddiff(None, apiurl, 11) == ("POST", apiurl, "{}/request/11?cmd=diff".format(apiurl), None)
    comment = BytesIO(b"comment")
    assert POST_request(None, apiurl, 11, comment=comment) == ("POST", apiurl, "{}/request/11".format(apiurl), comment)

    @api("PUT {apiurl}/method/?arg={arg}")
    def x(ctx, apiurl, arg=42): pass

    assert x(None, apiurl) == ("PUT", apiurl, "{}/method/?arg=42".format(apiurl))

def test_error_requests(raw_return_string):
    
    apiurl = "https://api.url"

    @api("FOO foobar")
    def x(ctx, apiurl): pass

    # bad HTTP method FOO raises ValueError
    with pytest.raises(ValueError):
        x(None, apiurl)

    @api("GET x")
    def x(): pass

    # ValueError raised by no context and apiurl variables
    with pytest.raises(ValueError):
        x()

    @api("GET api.url/{request}")
    def x(ctx, apiurl, request): pass

    # ValueError raised by bad url
    with pytest.raises(ValueError):
        x(None, apiurl, "request")
