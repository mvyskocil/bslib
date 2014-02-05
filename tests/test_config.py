#encoding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

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

CFG_DICT = {
    "general" : {
        "apiurl" : "https://api.opensuse.org/",
        "user" : "foo",
        "pass" : "bar",
        "passx" : "ham",
    },

    "https://api.suse.de" : {
        "user" : "bbb",
        "pass" : "zzz",
        "aliases" : ("ibs", ),
        "somedict" : {"foo" : 42, "bar" : None}
    },

    "https://api.opensuse.org/" : {
        "user" : "joe",
        "pass" : "joes's passwd",
    }
}

def test_BSConfig_advanced():

    global CFG_DICT
    cfg = BSConfig(**CFG_DICT)
    assert "general" in cfg
    #TODO: does osc some url normalization?
    assert "https://api.suse.de/" not in cfg
    assert "https://api.suse.de" in cfg
    assert "https://api.opensuse.org/" in cfg

def test_BSConfig_for_apiurl():
    
    global CFG_DICT
    cfg = BSConfig(**CFG_DICT)

    with pytest.raises(ValueError):
        ocfg = cfg.for_apiurl("https://api.opensuse.org")
    
    ocfg = cfg.for_apiurl("https://api.opensuse.org/")
    assert cfg != ocfg
    assert cfg.items() != ocfg.items()
    assert set(ocfg.items()) == \
        {('pswd', "joes's passwd"), ('apiurl', 'https://api.opensuse.org/'), ('pass', 'bar'), ('passx', 'ham'), ('user', 'joe')}
    
    icfg = cfg.for_apiurl("https://api.suse.de")
    assert cfg != icfg
    assert ocfg != icfg
    assert ocfg.items() != icfg.items()
    assert icfg.apiurl == "https://api.suse.de"

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
