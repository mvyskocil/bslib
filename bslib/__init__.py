#
# bslib - open build service client library
#
# Copyright (c) 2013 Michal Vyskocil<michal.vyskocil@gmail.com>
# Licensed under MIT
#

__version__ = '0.1'

import logging
from collections import namedtuple

from .utils import build_opener

class BSContext:

    def __init__(self, config, logger=None):
        if not logger:
            logger = logging.getLogger("bslib").addHandler(logging.NullHandler())
        #TODO: logger handling
        self._logger = logger
        self._config  = config
        self._opener = dict()
        for apiurl in self._config.apiurls():
            self._opener[apiurl] = build_opener(
                apiurl,
                self._config[apiurl].user,
                self._config[apiurl].pswd,
                self._config.get("cookiejar", "~/.osc_cookiejar"),
                debuglevel=5,
                capath=self._config[apiurl].get("capath", None),
                cafile=self._config[apiurl].get("cafile", None),
                )

    @classmethod
    def fromoscrc(cls, path=None):
        """Load context from oscrc and setup the logger properly"""
        from bslib.config import BSConfig
        #TODO: logger handling
        return cls(config=BSConfig.fromoscrc(path), logger=None)

    def log(self, severity, msg):
        """log the 'msg' with given integer 'severity'"""
        self._logger.log(severity, msg)

    def debug(self, msg):
        self._logger.debug(msg)
    
    def info(self, msg):
        self._logger.info(msg)
        
    def warning(self, msg):
        self._logger.warning(msg)
    
    def error(self, msg):
        self._logger.error(msg)
        
    def critical(self, msg):
        self._logger.critical(msg)

    def opener(self, apiurl):
        return self._opener[apiurl]

    @property
    def config(self):
        return self._config

__all__ = ["BSContext", ]

# prototype - this should go away from __init__

"""
from http.cookiejar import LWPCookieJar, CookieJar
from urllib.request import Request, install_opener, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, HTTPCookieProcessor, ProxyHandler, build_opener, urlopen
import os.path

apiurl = "https://api.opensuse.org/"
url =  apiurl + "source/" + "openSUSE:Factory/" + "make" + "?rev=latest"
req = Request(url)
authhandler = HTTPBasicAuthHandler(
    HTTPPasswordMgrWithDefaultRealm())
authhandler.add_password(None, apiurl, "mvyskocil", "20Dvacet")
# TODO check ssl certs

# TODO cookiejar handling
cookie_file = os.path.expanduser("~/.osc_cookiejar")
cookiejar = LWPCookieJar(cookie_file)
try:
    cookiejar.load(ignore_discard=True)
except IOError:
    try:
        open(cookie_file, 'w').close()
        os.chmod(cookie_file, 0o600)
    except:
        #print 'Unable to create cookiejar file: \'%s\'. Using RAM-based cookies.' % cookie_file
        cookiejar = CookieJar()


# TODO proxy handling
proxyhandler = ProxyHandler()

opener = build_opener(HTTPCookieProcessor(cookiejar), authhandler, proxyhandler)

install_opener(opener)

fd = urlopen(url)
"""

# explained
# HTTPBasicAuthHandler - support of HTTP Basic auth
# HTTPPasswordMgrWithDefaultRealm - some mapping
# authhandler.add_password - add a password for given apiurl
#
# ProxyHandler - the class dealing with proxies
#
# HttpCookieProcessor - deals with stored cookie
#
# install_opener - install a "global" opener - don't use that!
#
# there is HTTPSHandler, which might do something similar
#
# # allow only sslv3 and tlsv1, but not sslv2
# ctx = ssl.SSLContext(protocol=ssl.PROTCOL_SSLv23)
# ctx.options |= ssl.OP_NO_SSLv2
# ctx.verify_mode = ssl.CERT_REQUIRED
# ctx.set_default_verify_paths()
# ctx.load_verify_locations ???
# httpsh = HTTPSHandler(debuglevel=5, context=5, check_hostname=True)
#
# opener = build_opener(httpsh, ..., ...)
# opener.open(url)
