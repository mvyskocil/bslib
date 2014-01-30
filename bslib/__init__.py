#
# bslib - open build service client library
#
# Copyright (c) 2013 Michal Vyskocil<michal.vyskocil@gmail.com>
# Licensed under MIT
#

"""Open Build Service client library

Library with interaction with Open Build Service instance. It is
 * small - because can't do much atm
 * well structured - provides low and high-level access
 * just a library (sooo unlike osc)
 * under permissive license - don't belive at GPL libs

"""

__version__ = '0.1'

import logging
from collections import namedtuple

from .utils import build_opener

class BSContext:
    """BSContext does encapsulates all global resources
    for a library and is mandatory argument for most of
    functions. The most convient way how to use that is

        ctx = BSContext.fromoscrc(apiurl)
        some_cool_function(ctx, project, package)

    However in a case you need to talk to more than one
    OBS instances, you can do the following

        cfg = BSConfig.fromoscrc()
        ctx1 = BSContext(cfg.for_apiurl(apiurl1))
        ctx2 = BSContext(cfg.for_apiurl(apiurl2))

        some_cool_function(ctx1, project, package)
        some_cool_function(ctx2, project, package)
    """

    def __init__(self, config, logger=None):
        if not logger:
            logger = logging.getLogger("bslib").addHandler(logging.NullHandler())
        #TODO: logger handling
        self._logger = logger
        self.config  = config
        self._opener = build_opener(
            self.config.apiurl,
            self._config.user,
            self.config.pswd,
            self._config.get("cookiejar", "~/.osc_cookiejar"),
            debuglevel=5,
            capath=self._config.get("capath", None),
            cafile=self._config.get("cafile", None),
            )

    @classmethod
    def fromoscrc(cls, apiurl, path=None):
        """Load context from oscrc and setup the logger properly"""
        from bslib.config import BSConfig
        #TODO: logger handling
        return cls(config=BSConfig.fromoscrc(path), logger=None).for_apiurl(apiurl)

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
