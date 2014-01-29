import pytest

import os
import tempfile

from bslib.config import BSConfig

@pytest.fixture(scope="module")
def oscrc(request):
    fd, name = tempfile.mkstemp(prefix="bslibtestoscrc", text=True)
    os.fchmod(fd, 0o600)
    os.write(fd, b"""
[general]
apiurl = https://localhost
su-wrapper = sudo
[https://localhost]
user = joe
pass = doe
""")
    os.close(fd)
    def oscrc_teardown():
        os.unlink(name)
    request.addfinalizer(oscrc_teardown)
    return name

@pytest.fixture(scope="module")
def oscrc_badperm(request):
    fd, name = tempfile.mkstemp(prefix="bslibtestoscrc", text=True)
    os.fchmod(fd, 0o777)
    os.close(fd)
    def oscrc_teardown():
        os.unlink(name)
    request.addfinalizer(oscrc_teardown)
    return name

@pytest.fixture(scope="module")
def oscrc_nouser(request):
    fd, name = tempfile.mkstemp(prefix="bslibtestoscrc", text=True)
    os.fchmod(fd, 0o600)
    os.write(fd, b"""
[general]
apiurl = https://localhost
su-wrapper = sudo
[https://localhost]
pass = doe
""")
    os.close(fd)
    def oscrc_teardown():
        os.unlink(name)
    request.addfinalizer(oscrc_teardown)
    return name

def test_BSConfig_basic():
    foo = BSConfig(a=11)
    assert foo.a == 11
    assert hasattr(foo, "a")
    assert getattr(foo, "a") == 11
    assert foo["a"] == 11
    assert len(foo) == 1
    assert "a" in foo

    for k, v in foo.items():
        assert k == "a"
        assert v == 11

    for v in foo.values():
        assert v == 11

    for k in foo.keys():
        assert k == "a"

    assert type(foo.__iter__()) == type({}.__iter__())

def test_BSConfig_advanced():

    cfg_dict = {
        "apiurl" : "https://api.opensuse.org/",
        "user" : "foo",
        "pass" : "bar",
        "passx" : "ham",

        "https://api.suse.de" : {
            "user" : "bbb",
            "pass" : "zzz",
            "aliases" : ("ibs", ),
            "somedict" : {"foo" : 42, "bar" : None}
        }
    }

    cfg = BSConfig(**cfg_dict)
    #TODO: does osc some url normalization?
    assert "https://api.suse.de/" not in cfg
    assert "https://api.suse.de" in cfg

def test_BSConfig_badoscrc(oscrc_nouser):

    with pytest.raises(ValueError):
        cfg = BSConfig(**{"https://api.foo.net/" : {"bar" : 42}})
    
    with pytest.raises(ValueError):
        cfg = BSConfig.fromoscrc(path=oscrc_nouser)

def test_BSConfig_fromoscrc(oscrc):
    cfg = BSConfig.fromoscrc(path=oscrc)
    assert 'general' in cfg

    for apiurl in cfg.apiurls():
        assert cfg[apiurl].user == "joe"
        assert cfg[apiurl].pswd == "doe"

def test_BSConfig_badperms(oscrc_badperm):

    with pytest.raises(Exception):
        cfg = BSConfig.fromoscrc(path=oscrc_badperm)
