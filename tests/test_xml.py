#encoding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from xml.etree import cElementTree as ET
from bslib.xml import Request, Collection, Result, ResultList, StatusElement

#TBD: this is uterly incomplete!!!
def test_request_from_apidocs():
    rq = Request.fromxml(ET.parse("apidocs/api.opensuse.org/apidocs/request.xml").getroot())

    assert rq.reqid == 12
    assert rq.title == "Kraft"
    assert rq.description[:21] == "Kraft is KDE software"
    assert rq.accept_at == "2009-12-22T23:00:00"
    assert rq.state.name == "superseded"
    assert len(rq.actions) == 10
    assert len(rq.reviews) == 2
    assert len(rq.history) == 2

def test_collection_from_apidocs():
    cl = Collection.fromxml(ET.parse("apidocs/collection.xml").getroot())

    assert len(cl) == 2
    assert cl[0] != cl[1]

    with pytest.raises(IndexError):
        cl[42]

    for el in cl:
        assert isinstance(el, Request)

def test_resultlist_from_apidocs():
    rl = ResultList.fromxml(ET.parse("apidocs/pkgresult.xml").getroot())

    assert len(rl) == 18
    assert isinstance(rl[0], Result)

    res = rl[0]
    assert res.project == "Base:System"
    assert len(res.statuslist) == 1

    st = res.statuslist[0]
    assert isinstance(st, StatusElement)
    assert st.package == "gpg2"
