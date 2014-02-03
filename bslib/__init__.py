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
        self._config  = config
        self._opener = build_opener(
            self._config.apiurl,
            self._config.user,
            self._config.pswd,
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
        return cls(config=BSConfig.fromoscrc(path).for_apiurl(apiurl), logger=None)

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

    @property
    def apiurl(self):
        return self._config.apiurl

    @property
    def config(self):
        return self._config

    @property
    def opener(self):
        return self._opener

__all__ = ["BSContext", ]
