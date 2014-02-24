[![Build Status](https://travis-ci.org/mvyskocil/bslib.png?branch=master)](https://travis-ci.org/mvyskocil/bslib)

# about bslib

bslib is a light-weight library for accessing [Open Build Service](http://openbuildservice.org/).

It is
 * small - but mainly because it implements just a few of things atm
 * well structured - provides low and high-level access
 * just a library (sooo unlike osc)
 * under very permissive MIT license
 * works in python3/python2

# small howto

Most web-accessing functions expect BSContext instance in order to work. It
contain apiurl, appropriate opener and in the future even logging capabilities.
The easiest way how to create it is it's `fromoscrc` classmethod.

```python
 import bslib
 import bslib.api

 ctx = bslib.BSContext.fromoscrc("https://api.opensuse.org")
 request = bslib.api.get_request(ctx, 123456, diff=True)
```



