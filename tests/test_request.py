
from xml.etree import cElementTree as ET
from bslib.request import Request

#TBD: this is uterly incomplete!!!
def test_request_from_apidocs():
    rq = Request.fromxml(ET.parse("apidocs/api.opensuse.org/apidocs/request.xml").getroot())

    assert rq.reqid == "12"
    assert rq.title == "Kraft"
    assert rq.description[:21] == "Kraft is KDE software"
    assert rq.accept_at == "2009-12-22T23:00:00"
    assert rq.state.name == "superseded"
    assert len(rq.actions) == 10
    assert len(rq.reviews) == 2
    assert len(rq.history) == 2
