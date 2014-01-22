import types
import collections.abc
import configparser
import os
from collections import deque

from .utils import is_url, passx_decode

class BSConfig(types.SimpleNamespace, collections.abc.Mapping):

    """
    Provides property and dictionary access to config values. Nested
    dictionaries are converted to BSConfig instances. Note this class
    does not provide defaults, neither
    """

    def __init__(self, **kwargs):

        for key, value in kwargs.items():
            if isinstance(value, dict):
                vk = value.keys()
                #ensure at least name/pass exists for apiurl configs
                if is_url(key):
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
                if "aliases" in cfg:
                    for a in cfg.aliases:
                        self.__dict__[a] = cfg
            else:
                self.__dict__[key] = value

    @classmethod
    def fromoscrc(cls, path=None):
        if path is None:
            path = os.path.expanduser("~/.oscrc")
        st_mode =os.stat(path).st_mode 
        if st_mode & 0x0fff != 0o600:
            raise Exception("Bad permission of `{}', expected 0o600, got {}".format(path, oct(st_mode)))
        cfg = configparser.ConfigParser()
        with open(path, "rt") as fp:
            cfg.read_file(fp, source=path)
        # remove crufty default section
        return cls(**{k:dict(v) for k, v in cfg.items() if k != "DEFAULT"})

    def apiurls(self):
        return (k for k in self.keys() if is_url(k))

    def __getitem__(self, value):
        return self.__dict__.__getitem__(value)
        
    def __iter__(self):
        return self.__dict__.__iter__()
        
    def __len__(self):
        return self.__dict__.__len__()
