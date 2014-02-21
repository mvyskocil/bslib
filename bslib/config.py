#encoding: utf-8

# handle reading config for bslib
# Copyright (c) 2014 Michal Vyskocil<michal.vyskocil@gmail.com>
# Licensed under MIT, see bslib/__init__.py

from __future__ import print_function
from __future__ import unicode_literals

import os
import copy
from collections import deque

try:
    from collections.abc import Mapping
    from types import SimpleNamespace
    from configparser import ConfigParser
except ImportError:
    from collections import Mapping
    from ._compat import SimpleNamespace
    from ._compat import ConfigParser3 as ConfigParser

from .utils import is_url, passx_decode

class BSConfig(SimpleNamespace, Mapping):

    """
    Provides property and dictionary access to config values. Nested
    dictionaries are converted to BSConfig instances. Note this class
    does not provide defaults, neither
    """

    def __init__(self, **kwargs):

        for key, value in kwargs.items():
            if not isinstance(value, dict):
                self.__dict__[key] = value
                continue

            #ensure at least name/pass exists for apiurl configs
            if is_url(key):
                # do not modify dict
                value = copy.copy(value)
                vk = value.keys()

                if not "user" in vk:
                    raise ValueError("'user' field is mandatory")
                if value.get("keyring") == "1":
                    raise NotImplementedError("keyring support is not yet done")
                if value.get("passx") is not None:
                    value["pass"] = passx_decode(value["passx"])
                    del value["passx"]

                if not "pass" in vk:
                    raise ValueError("'pass' field is mandatory")
                #this is attribute friendly version
                value["pswd"] = value["pass"]
                del value["pass"]

            cfg = BSConfig(**value)
            self.__dict__[key] = cfg

    @classmethod
    def fromoscrc(cls, path=None):
        if path is None:
            path = os.path.expanduser("~/.oscrc")
        st_mode =os.stat(path).st_mode 
        if st_mode & 0x0fff != 0o600:
            raise Exception("Bad permission of `{}', expected 0o600, got {}".format(path, oct(st_mode)))
        cfg = ConfigParser()
        with open(path, "rt") as fp:
            cfg.read_file(fp, source=path)
        # remove crufty default section
        return cls(**{k:dict(v) for k, v in cfg.items() if k != "DEFAULT"})

    def apiurls(self):
        return (k for k in self.keys() if is_url(k))

    def for_apiurl(self, apiurl):
        """Return a BSConfig instance for given apiurl + general section only"""
        if apiurl not in self.apiurls():
            raise ValueError("Unknown apiurl {}, not in {}".format(apiurl, list(self.apiurls())))

        dct = {k:v for k, v in self["general"].items()}
        dct.update({k:v for k, v in self[apiurl].items()})
        dct["apiurl"] = apiurl

        return self.__class__(**dct)

    def __getitem__(self, value):
        return self.__dict__.__getitem__(value)
        
    def __iter__(self):
        return self.__dict__.__iter__()
        
    def __len__(self):
        return self.__dict__.__len__()

    def items(self):
        return self.__dict__.items()
